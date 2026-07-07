"""Microsoft Project XML exporter.

Produces a Microsoft Project 2003+ XML document
(``http://schemas.microsoft.com/project``) preserving tasks, the WBS outline,
resources, dependencies, milestones, progress and start constraints. The output
imports into Microsoft Project without manual correction.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType
from planningez.core.models.dependency import DependencyType
from planningez.export.base_exporter import BaseExporter, register_exporter

_NS = "http://schemas.microsoft.com/project"

# PlanningEz dependency types -> Microsoft Project link-type codes.
_LINK_CODES = {
    DependencyType.FINISH_TO_FINISH: "0",
    DependencyType.FINISH_TO_START: "1",
    DependencyType.START_TO_FINISH: "2",
    DependencyType.START_TO_START: "3",
}


@register_exporter
class MSProjectExporter(BaseExporter):
    """Export a project to Microsoft Project XML."""

    format_key = "msproject"
    file_extension = "xml"
    display_name = "Microsoft Project (XML)"

    def __init__(self, hours_per_day: float = 8.0) -> None:
        """Initialize with the working-hours-per-day used for durations."""
        self.hours_per_day = hours_per_day

    def export(self, project: Project) -> str:
        """Serialize the project to Microsoft Project XML."""
        ET.register_namespace("", _NS)
        root = ET.Element(f"{{{_NS}}}Project")
        self._sub(root, "Name", project.name)
        self._sub(root, "Title", project.name)
        if project.start_date:
            self._sub(root, "StartDate", f"{project.start_date.isoformat()}T08:00:00")
        self._sub(root, "CalendarUID", "1")

        self._append_calendars(root)
        uid_map = self._append_tasks(root, project)
        self._append_resources(root, project)
        self._append_assignments(root, project, uid_map)

        ET.indent(root, space="  ")
        xml_body = ET.tostring(root, encoding="unicode")
        return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n{xml_body}\n'

    # ------------------------------------------------------------------ #
    # Sections
    # ------------------------------------------------------------------ #
    def _append_calendars(self, root: ET.Element) -> None:
        """Emit a single standard (Mon–Fri) base calendar."""
        calendars = self._sub(root, "Calendars", None)
        calendar = self._sub(calendars, "Calendar", None)
        self._sub(calendar, "UID", "1")
        self._sub(calendar, "Name", "Standard")
        self._sub(calendar, "IsBaseCalendar", "1")
        week_days = self._sub(calendar, "WeekDays", None)
        for day_type in range(1, 8):  # 1=Sunday .. 7=Saturday
            week_day = self._sub(week_days, "WeekDay", None)
            self._sub(week_day, "DayType", str(day_type))
            working = day_type not in (1, 7)
            self._sub(week_day, "DayWorking", "1" if working else "0")
            if working:
                times = self._sub(week_day, "WorkingTimes", None)
                for start, finish in (("08:00:00", "12:00:00"), ("13:00:00", "17:00:00")):
                    wt = self._sub(times, "WorkingTime", None)
                    self._sub(wt, "FromTime", start)
                    self._sub(wt, "ToTime", finish)

    def _append_tasks(self, root: ET.Element, project: Project) -> Dict[str, int]:
        """Emit the Tasks section and return a task_id -> UID mapping."""
        tasks_el = self._sub(root, "Tasks", None)
        uid_map: Dict[str, int] = {t.task_id: i for i, t in enumerate(project.tasks, start=1)}

        for index, task in enumerate(project.tasks, start=1):
            task_el = self._sub(tasks_el, "Task", None)
            uid = uid_map[task.task_id]
            self._sub(task_el, "UID", str(uid))
            self._sub(task_el, "ID", str(index))
            self._sub(task_el, "Name", task.name)
            is_milestone = task.is_milestone or task.task_type == TaskType.MILESTONE
            is_summary = task.task_type == TaskType.SUMMARY
            self._sub(task_el, "Type", "1")
            self._sub(task_el, "OutlineLevel", str(self._outline_level(task, project)))
            self._sub(task_el, "Summary", "1" if is_summary else "0")
            self._sub(task_el, "Milestone", "1" if is_milestone else "0")
            self._sub(task_el, "Duration", self._iso_duration(task.duration))
            self._sub(task_el, "DurationFormat", "7")
            self._sub(task_el, "PercentComplete", str(int(task.progress)))
            if task.start_date:
                iso = task.start_date.isoformat()
                self._sub(task_el, "Start", f"{iso}T08:00:00")
                # Start No Earlier Than constraint.
                self._sub(task_el, "ConstraintType", "4")
                self._sub(task_el, "ConstraintDate", f"{iso}T08:00:00")
            if task.end_date:
                self._sub(task_el, "Finish", f"{task.end_date.isoformat()}T17:00:00")

            incoming, _ = project.get_dependencies_for_task(task.task_id)
            for dep in incoming:
                pred_uid = uid_map.get(dep.predecessor_id)
                if pred_uid is None:
                    continue
                link = self._sub(task_el, "PredecessorLink", None)
                self._sub(link, "PredecessorUID", str(pred_uid))
                self._sub(link, "Type", _LINK_CODES.get(dep.dependency_type, "1"))
                self._sub(link, "LinkLag", str(int(dep.lag * self.hours_per_day * 60)))
                self._sub(link, "LagFormat", "7")
        return uid_map

    def _append_resources(self, root: ET.Element, project: Project) -> None:
        """Emit the Resources section."""
        resources_el = self._sub(root, "Resources", None)
        for index, resource in enumerate(project.resources, start=1):
            res_el = self._sub(resources_el, "Resource", None)
            self._sub(res_el, "UID", str(index))
            self._sub(res_el, "ID", str(index))
            self._sub(res_el, "Name", resource.name)
            self._sub(res_el, "Type", "1")  # Work resource
            self._sub(res_el, "MaxUnits", str(resource.availability / 100.0))
            if resource.daily_cost:
                # MS Project standard rate is per hour; convert from daily cost.
                self._sub(res_el, "StandardRate", str(resource.daily_cost / self.hours_per_day))

    def _append_assignments(
        self, root: ET.Element, project: Project, uid_map: Dict[str, int]
    ) -> None:
        """Emit assignments linking responsible resources to tasks."""
        assignments_el = self._sub(root, "Assignments", None)
        res_uid = {r.resource_id: i for i, r in enumerate(project.resources, start=1)}
        uid = 1
        for task in project.tasks:
            if task.responsible and task.responsible in res_uid:
                assign_el = self._sub(assignments_el, "Assignment", None)
                self._sub(assign_el, "UID", str(uid))
                self._sub(assign_el, "TaskUID", str(uid_map[task.task_id]))
                self._sub(assign_el, "ResourceUID", str(res_uid[task.responsible]))
                self._sub(assign_el, "Units", "1")
                uid += 1

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _sub(self, parent: ET.Element, tag: str, text: Optional[str]) -> ET.Element:
        """Create a namespaced sub-element, optionally with text."""
        element = ET.SubElement(parent, f"{{{_NS}}}{tag}")
        if text is not None:
            element.text = text
        return element

    def _iso_duration(self, days: float) -> str:
        """Convert working days into an ISO 8601 duration (``PT#H#M#S``)."""
        total_minutes = int(round(days * self.hours_per_day * 60))
        hours, minutes = divmod(total_minutes, 60)
        return f"PT{hours}H{minutes}M0S"

    @staticmethod
    def _outline_level(task: Task, project: Project) -> int:
        """Compute a 1-based outline level by walking the parent chain."""
        level = 1
        current = task
        guard = 0
        while current.parent_id and guard < 64:
            parent = project.get_task(current.parent_id)
            if parent is None:
                break
            level += 1
            current = parent
            guard += 1
        return level
