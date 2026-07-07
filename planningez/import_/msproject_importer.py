"""Microsoft Project XML importer for PlanningEz.

Parses the Microsoft Project 2003+ XML schema
(``http://schemas.microsoft.com/project``): tasks with their outline level,
durations, dates, progress and milestone flag, plus predecessor links which map
onto PlanningEz dependencies.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Union
from xml.etree import ElementTree as ET

from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType
from planningez.core.models.dependency import Dependency, DependencyType
from planningez.core.exceptions import ImportError as PlanningImportError
from planningez.utils.serialization import parse_date

_MSP_NS = "{http://schemas.microsoft.com/project}"

# Microsoft Project link-type codes -> PlanningEz dependency types.
_LINK_TYPES = {
    "0": DependencyType.FINISH_TO_FINISH,
    "1": DependencyType.FINISH_TO_START,
    "2": DependencyType.START_TO_FINISH,
    "3": DependencyType.START_TO_START,
}

_DURATION_RE = re.compile(
    r"P(?:T)?(?:(?P<days>\d+)D)?(?:T?(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
)


class MSProjectImporter:
    """Import a :class:`Project` from Microsoft Project XML."""

    def from_xml(self, text: str, hours_per_day: float = 8.0) -> Project:
        """Parse Microsoft Project XML text into a Project."""
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise PlanningImportError(f"Invalid Microsoft Project XML: {exc}") from exc

        # Support documents with or without the MSP namespace.
        ns = _MSP_NS if root.tag.startswith(_MSP_NS) else ""

        project_name = self._text(root, f"{ns}Name") or "Imported MS Project"
        project = Project(name=project_name)
        project.start_date = parse_date(self._text(root, f"{ns}StartDate"))

        uid_to_task: Dict[str, str] = {}
        pending_links: list[tuple[str, str, str, float]] = []

        tasks_el = root.find(f"{ns}Tasks")
        if tasks_el is None:
            return project

        for task_el in tasks_el.findall(f"{ns}Task"):
            uid = self._text(task_el, f"{ns}UID")
            name = self._text(task_el, f"{ns}Name")
            if uid is None or not name:
                # UID 0 is the project summary row with an empty name; skip it.
                continue

            is_milestone = self._text(task_el, f"{ns}Milestone") == "1"
            duration_days = self._parse_duration(
                self._text(task_el, f"{ns}Duration"), hours_per_day
            )
            task = Task(
                name=name,
                duration=0.0 if is_milestone else duration_days,
                task_type=TaskType.MILESTONE if is_milestone else TaskType.TASK,
                is_milestone=is_milestone,
                start_date=parse_date(self._text(task_el, f"{ns}Start")),
                end_date=parse_date(self._text(task_el, f"{ns}Finish")),
                progress=float(self._text(task_el, f"{ns}PercentComplete") or 0),
            )
            project.add_task(task)
            uid_to_task[uid] = task.task_id

            for link in task_el.findall(f"{ns}PredecessorLink"):
                pred_uid = self._text(link, f"{ns}PredecessorUID")
                link_type = self._text(link, f"{ns}Type") or "1"
                lag_raw = self._text(link, f"{ns}LinkLag") or "0"
                lag_days = self._to_float(lag_raw) / (60.0 * hours_per_day)
                if pred_uid:
                    pending_links.append((pred_uid, uid, link_type, lag_days))

        for pred_uid, succ_uid, link_type, lag in pending_links:
            pred_id = uid_to_task.get(pred_uid)
            succ_id = uid_to_task.get(succ_uid)
            if pred_id and succ_id:
                project.add_dependency(
                    Dependency(
                        predecessor_id=pred_id,
                        successor_id=succ_id,
                        dependency_type=_LINK_TYPES.get(link_type, DependencyType.FINISH_TO_START),
                        lag=lag,
                    )
                )
        return project

    def from_file(self, path: Union[str, Path], hours_per_day: float = 8.0) -> Project:
        """Import a Project from a Microsoft Project XML file."""
        path = Path(path)
        if not path.exists():
            raise PlanningImportError(f"File not found: {path}")
        return self.from_xml(path.read_text(encoding="utf-8"), hours_per_day=hours_per_day)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _text(element: ET.Element, tag: str) -> Optional[str]:
        """Return the stripped text of a child element, or ``None``."""
        child = element.find(tag)
        if child is not None and child.text is not None:
            return child.text.strip()
        return None

    @staticmethod
    def _to_float(value: str) -> float:
        """Best-effort float conversion (returns 0.0 on failure)."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _parse_duration(self, value: Optional[str], hours_per_day: float) -> float:
        """Convert an ISO 8601 duration (``PT8H0M0S``) into working days."""
        if not value:
            return 1.0
        match = _DURATION_RE.match(value)
        if not match:
            return 1.0
        days = int(match.group("days") or 0)
        hours = int(match.group("hours") or 0)
        minutes = int(match.group("minutes") or 0)
        total_hours = days * hours_per_day + hours + minutes / 60.0
        result = total_hours / hours_per_day if hours_per_day else 0.0
        return round(result, 2) if result else 1.0
