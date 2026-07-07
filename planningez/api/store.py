"""In-memory application store for the PlanningEz API.

Holds the live projects and the shared Work Package library for the running
server. The library is seeded with a handful of example packages so the web UI
has content on first launch. State is process-local (no database) which suits a
single-user planning assistant; persistence happens through JSON import/export.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType
from planningez.core.models.dependency import Dependency
from planningez.core.models.resource import Resource, ResourceRole
from planningez.core.models.work_package import (
    WorkPackage,
    Discipline,
    Milestone,
    Deliverable,
)
from planningez.core.services.work_package_library import WorkPackageLibrary


class AppStore:
    """Process-local store of projects and the Work Package library."""

    def __init__(self) -> None:
        """Initialize an empty project map and a disk-backed library.

        The Work Package library is persisted under ``PLANNINGEZ_DATA_DIR`` (or
        ``~/.planningez`` by default) so a user's additions, edits and deletions
        survive restarts of the app. The example packages are seeded only on the
        very first run (when the store is empty).
        """
        self.projects: Dict[str, Project] = {}
        data_dir = Path(
            os.environ.get("PLANNINGEZ_DATA_DIR", Path.home() / ".planningez")
        )
        self.library = WorkPackageLibrary(storage_dir=data_dir / "work_packages")
        if len(self.library) == 0:
            self._seed_library()

    # ------------------------------------------------------------------ #
    # Projects
    # ------------------------------------------------------------------ #
    def add_project(self, project: Project) -> Project:
        """Register a project and return it."""
        self.projects[project.project_id] = project
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Return a project by id, or ``None``."""
        return self.projects.get(project_id)

    def remove_project(self, project_id: str) -> None:
        """Delete a project by id (no-op if absent)."""
        self.projects.pop(project_id, None)

    def list_projects(self) -> List[Project]:
        """Return all projects."""
        return list(self.projects.values())

    # ------------------------------------------------------------------ #
    # Library seeding
    # ------------------------------------------------------------------ #
    def _seed_library(self) -> None:
        """Populate the library with representative example Work Packages."""
        self.library.add(self._basic_engineering())
        self.library.add(self._detailed_engineering())
        self.library.add(self._hazop())
        self.library.add(self._fat())
        self.library.add(self._sat())
        self.library.add(self._commissioning())

    @staticmethod
    def _linear_package(
        name: str,
        code: str,
        discipline: Discipline,
        steps: List[tuple[str, float]],
        milestone: Optional[str] = None,
        role: ResourceRole = ResourceRole.ENGINEER,
    ) -> WorkPackage:
        """Build a package whose tasks run in sequence (finish-to-start)."""
        wp = WorkPackage(name=name, code=code, discipline=discipline)
        wp.default_resources.append(Resource(name=f"{discipline.value.title()} Lead", role=role))
        previous: Optional[Task] = None
        for task_name, duration in steps:
            task = Task(name=task_name, duration=duration)
            wp.add_task(task)
            if previous is not None:
                wp.add_dependency(
                    Dependency(predecessor_id=previous.task_id, successor_id=task.task_id)
                )
            previous = task
        if milestone:
            wp.add_milestone(Milestone(name=milestone))
        wp.compute_estimated_duration()
        return wp

    def _basic_engineering(self) -> WorkPackage:
        wp = self._linear_package(
            "Basic Engineering", "BE-001", Discipline.ENGINEERING,
            [("Kick-off", 1), ("Process Design Basis", 5),
             ("PFD Development", 8), ("Basic Engineering Package", 6)],
            milestone="Basic Engineering Complete",
        )
        wp.deliverables.append(Deliverable(name="Process Flow Diagrams"))
        wp.deliverables.append(Deliverable(name="Basic Engineering Package"))
        return wp

    def _detailed_engineering(self) -> WorkPackage:
        return self._linear_package(
            "Detailed Engineering", "DE-001", Discipline.ENGINEERING,
            [("P&ID Development", 10), ("Equipment Datasheets", 8),
             ("3D Modeling", 12), ("Isometrics & MTO", 7)],
            milestone="IFC Drawings Issued",
        )

    def _hazop(self) -> WorkPackage:
        return self._linear_package(
            "HAZOP", "HAZOP-001", Discipline.QUALITY,
            [("HAZOP Preparation", 3), ("HAZOP Sessions", 5),
             ("Actions Close-out", 6)],
            milestone="HAZOP Closed",
        )

    def _fat(self) -> WorkPackage:
        return self._linear_package(
            "Factory Acceptance Test", "FAT-001", Discipline.COMMISSIONING,
            [("FAT Procedure", 3), ("FAT Preparation", 2), ("FAT Execution", 4)],
            milestone="FAT Passed",
            role=ResourceRole.TECHNICIAN,
        )

    def _sat(self) -> WorkPackage:
        return self._linear_package(
            "Site Acceptance Test", "SAT-001", Discipline.COMMISSIONING,
            [("SAT Procedure", 2), ("SAT Execution", 5)],
            milestone="SAT Passed",
            role=ResourceRole.TECHNICIAN,
        )

    def _commissioning(self) -> WorkPackage:
        return self._linear_package(
            "Commissioning", "COM-001", Discipline.COMMISSIONING,
            [("Pre-Commissioning", 6), ("Cold Commissioning", 8),
             ("Hot Commissioning", 10), ("Performance Test", 5)],
            milestone="Ready for Operation",
            role=ResourceRole.TECHNICIAN,
        )


# Module-level singleton used by the API routes.
store = AppStore()
