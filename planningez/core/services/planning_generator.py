"""Intelligent planning generation from Work Packages.

Given a selection of Work Packages, this service assembles a complete project:
it builds the WBS, clones every task (with fresh ids), inserts milestones,
re-wires internal dependencies, computes durations and connects the packages to
one another according to configurable rules.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType
from planningez.core.models.dependency import Dependency, DependencyType
from planningez.core.models.work_package import WorkPackage


class ConnectMode(str, Enum):
    """How consecutive Work Packages are linked together."""

    SEQUENTIAL = "sequential"  # Each package starts after the previous finishes
    PARALLEL = "parallel"      # Packages run independently, no cross links
    CUSTOM = "custom"          # Links supplied explicitly by code pairs


@dataclass
class GenerationRules:
    """Configuration controlling how a plan is generated from packages."""

    connect_mode: ConnectMode = ConnectMode.SEQUENTIAL
    link_type: DependencyType = DependencyType.FINISH_TO_START
    link_lag: float = 0.0
    create_summary_tasks: bool = True
    # For CUSTOM mode: pairs of (predecessor_wp_code, successor_wp_code).
    custom_links: List[Tuple[str, str]] = field(default_factory=list)


class PlanningGenerator:
    """Assemble a :class:`Project` from a list of Work Packages."""

    def __init__(self, rules: Optional[GenerationRules] = None) -> None:
        """Initialize the generator with optional generation rules."""
        self.rules = rules or GenerationRules()

    def generate(
        self,
        packages: List[WorkPackage],
        project_name: str = "Generated Project",
    ) -> Project:
        """Generate a project from the supplied Work Packages.

        Args:
            packages: Work Packages to assemble, in the desired order.
            project_name: Name for the resulting project.

        Returns:
            A fully populated :class:`Project`.
        """
        project = Project(name=project_name)

        # Track, per package, the summary id plus its entry/exit tasks so that
        # cross-package links can be created afterwards.
        wp_entry_tasks: Dict[str, List[str]] = {}
        wp_exit_tasks: Dict[str, List[str]] = {}

        for package in packages:
            summary_id, entries, exits = self._instantiate_package(project, package)
            wp_entry_tasks[package.work_package_id] = entries
            wp_exit_tasks[package.work_package_id] = exits

        self._connect_packages(project, packages, wp_entry_tasks, wp_exit_tasks)

        project.total_duration = sum(
            t.duration for t in project.tasks if t.task_type == TaskType.TASK
        )
        return project

    # ------------------------------------------------------------------ #
    # Package instantiation
    # ------------------------------------------------------------------ #
    def _instantiate_package(
        self, project: Project, package: WorkPackage
    ) -> Tuple[Optional[str], List[str], List[str]]:
        """Clone one package into the project.

        Returns:
            (summary_task_id, entry_task_ids, exit_task_ids)
        """
        summary_id: Optional[str] = None
        if self.rules.create_summary_tasks:
            summary = Task(
                name=package.name,
                task_type=TaskType.SUMMARY,
                duration=0.0,
            )
            project.add_task(summary)
            summary_id = summary.task_id

        # Clone tasks with fresh ids, remembering the old -> new mapping.
        id_map: Dict[str, str] = {}
        cloned: List[Task] = []
        for original in package.tasks:
            clone = copy.deepcopy(original)
            clone.task_id = Task(name="_").task_id  # fresh id
            clone.parent_id = summary_id
            id_map[original.task_id] = clone.task_id
            project.add_task(clone)
            cloned.append(clone)

        # Re-wire internal dependencies onto the cloned tasks.
        internal_pred: set[str] = set()
        internal_succ: set[str] = set()
        for dep in package.dependencies:
            pred = id_map.get(dep.predecessor_id)
            succ = id_map.get(dep.successor_id)
            if pred and succ:
                project.add_dependency(
                    Dependency(
                        predecessor_id=pred,
                        successor_id=succ,
                        dependency_type=dep.dependency_type,
                        lag=dep.lag,
                    )
                )
                internal_succ.add(succ)
                internal_pred.add(pred)

        # Insert milestones as milestone tasks offset from the package start.
        for milestone in package.milestones:
            ms_task = Task(
                name=milestone.name,
                task_type=TaskType.MILESTONE,
                duration=0.0,
                is_milestone=True,
                parent_id=summary_id,
                comments=milestone.comments,
            )
            project.add_task(ms_task)
            cloned.append(ms_task)

        # Carry over default resources (deduplicated by name).
        existing_names = {r.name for r in project.resources}
        for resource in package.default_resources:
            if resource.name not in existing_names:
                project.add_resource(copy.deepcopy(resource))
                existing_names.add(resource.name)

        # Entry tasks have no internal predecessor; exit tasks no internal successor.
        entries = [t.task_id for t in cloned if t.task_id not in internal_succ]
        exits = [t.task_id for t in cloned if t.task_id not in internal_pred]
        # Fall back to all tasks when a package has no internal structure.
        if not entries:
            entries = [t.task_id for t in cloned]
        if not exits:
            exits = [t.task_id for t in cloned]
        return summary_id, entries, exits

    # ------------------------------------------------------------------ #
    # Cross-package connection
    # ------------------------------------------------------------------ #
    def _connect_packages(
        self,
        project: Project,
        packages: List[WorkPackage],
        entries: Dict[str, List[str]],
        exits: Dict[str, List[str]],
    ) -> None:
        """Create links between packages per the configured rules."""
        if self.rules.connect_mode == ConnectMode.PARALLEL:
            return

        if self.rules.connect_mode == ConnectMode.SEQUENTIAL:
            for prev, nxt in zip(packages, packages[1:]):
                self._link(project, exits[prev.work_package_id], entries[nxt.work_package_id])
            return

        if self.rules.connect_mode == ConnectMode.CUSTOM:
            by_code = {p.code: p for p in packages if p.code}
            for pred_code, succ_code in self.rules.custom_links:
                pred_wp = by_code.get(pred_code)
                succ_wp = by_code.get(succ_code)
                if pred_wp and succ_wp:
                    self._link(
                        project,
                        exits[pred_wp.work_package_id],
                        entries[succ_wp.work_package_id],
                    )

    def _link(self, project: Project, predecessors: List[str], successors: List[str]) -> None:
        """Create dependencies from every predecessor to every successor."""
        for pred in predecessors:
            for succ in successors:
                if pred == succ:
                    continue
                project.add_dependency(
                    Dependency(
                        predecessor_id=pred,
                        successor_id=succ,
                        dependency_type=self.rules.link_type,
                        lag=self.rules.link_lag,
                    )
                )
