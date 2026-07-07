"""Primavera P6 XML importer for PlanningEz.

Tolerant parser for the Primavera P6 XML export (``APIBusinessObjects``). It
extracts the WBS hierarchy, Activities (as tasks) and Relationships (as
dependencies). Namespaces vary between P6 versions, so element look-ups are
done by local tag name rather than a fixed namespace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union
from xml.etree import ElementTree as ET

from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType
from planningez.core.models.dependency import Dependency, DependencyType
from planningez.core.exceptions import ImportError as PlanningImportError

# Primavera relationship type codes -> PlanningEz dependency types.
_REL_TYPES = {
    "Finish to Start": DependencyType.FINISH_TO_START,
    "Start to Start": DependencyType.START_TO_START,
    "Finish to Finish": DependencyType.FINISH_TO_FINISH,
    "Start to Finish": DependencyType.START_TO_FINISH,
    "FS": DependencyType.FINISH_TO_START,
    "SS": DependencyType.START_TO_START,
    "FF": DependencyType.FINISH_TO_FINISH,
    "SF": DependencyType.START_TO_FINISH,
}

_MILESTONE_TYPES = {"Start Milestone", "Finish Milestone"}


class PrimaveraImporter:
    """Import a :class:`Project` from Primavera P6 XML."""

    def __init__(self, hours_per_day: float = 8.0) -> None:
        """Initialize with the working-hours-per-day used for durations."""
        self.hours_per_day = hours_per_day

    def from_xml(self, text: str) -> Project:
        """Parse Primavera P6 XML text into a Project."""
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise PlanningImportError(f"Invalid Primavera P6 XML: {exc}") from exc

        project_el = self._find(root, "Project") or root
        project_name = self._child_text(project_el, "Name") or "Imported Primavera Project"
        project = Project(name=project_name)

        activity_id_to_task: Dict[str, str] = {}

        for activity in self._find_all(project_el, "Activity"):
            obj_id = self._child_text(activity, "ObjectId") or self._child_text(activity, "Id")
            name = self._child_text(activity, "Name")
            if not obj_id or not name:
                continue
            activity_type = self._child_text(activity, "Type") or ""
            is_milestone = activity_type in _MILESTONE_TYPES
            duration_hours = self._to_float(
                self._child_text(activity, "PlannedDuration")
                or self._child_text(activity, "AtCompletionDuration")
            )
            duration = duration_hours / self.hours_per_day if self.hours_per_day else duration_hours
            task = Task(
                name=name,
                duration=0.0 if is_milestone else (duration or 1.0),
                task_type=TaskType.MILESTONE if is_milestone else TaskType.TASK,
                is_milestone=is_milestone,
                progress=self._to_float(self._child_text(activity, "PercentComplete")),
            )
            project.add_task(task)
            activity_id_to_task[obj_id] = task.task_id

        for rel in self._find_all(project_el, "Relationship"):
            pred = self._child_text(rel, "PredecessorActivityObjectId")
            succ = self._child_text(rel, "SuccessorActivityObjectId")
            rel_type = self._child_text(rel, "Type") or "Finish to Start"
            lag_hours = self._to_float(self._child_text(rel, "Lag"))
            lag = lag_hours / self.hours_per_day if self.hours_per_day else lag_hours
            pred_id = activity_id_to_task.get(pred or "")
            succ_id = activity_id_to_task.get(succ or "")
            if pred_id and succ_id:
                project.add_dependency(
                    Dependency(
                        predecessor_id=pred_id,
                        successor_id=succ_id,
                        dependency_type=_REL_TYPES.get(rel_type, DependencyType.FINISH_TO_START),
                        lag=lag,
                    )
                )
        return project

    def from_file(self, path: Union[str, Path]) -> Project:
        """Import a Project from a Primavera P6 XML file."""
        path = Path(path)
        if not path.exists():
            raise PlanningImportError(f"File not found: {path}")
        return self.from_xml(path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ #
    # Namespace-agnostic helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _local(tag: str) -> str:
        """Strip an XML namespace from a tag name."""
        return tag.rsplit("}", 1)[-1]

    def _find(self, element: ET.Element, name: str) -> Optional[ET.Element]:
        """Find the first descendant with the given local tag name."""
        for child in element.iter():
            if self._local(child.tag) == name:
                return child
        return None

    def _find_all(self, element: ET.Element, name: str) -> List[ET.Element]:
        """Find all descendants with the given local tag name."""
        return [c for c in element.iter() if self._local(c.tag) == name]

    def _child_text(self, element: ET.Element, name: str) -> Optional[str]:
        """Return the text of the first direct child with a local tag name."""
        for child in element:
            if self._local(child.tag) == name and child.text is not None:
                return child.text.strip()
        return None

    @staticmethod
    def _to_float(value: Optional[str]) -> float:
        """Best-effort float conversion (returns 0.0 on failure)."""
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0
