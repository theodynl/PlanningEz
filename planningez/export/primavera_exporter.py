"""Primavera P6 XML exporter.

Produces a Primavera P6 XML document (``APIBusinessObjects``) preserving the
WBS, activities, relationships, resources, milestones and progress. Activity
durations are written in hours (the P6 convention). The output is structured so
it can be re-imported by :class:`planningez.import_.primavera_importer`.
"""

from __future__ import annotations

from typing import Dict, Optional
from xml.etree import ElementTree as ET

from planningez.core.models.project import Project
from planningez.core.models.task import TaskType
from planningez.core.models.dependency import DependencyType
from planningez.export.base_exporter import BaseExporter, register_exporter

_NS = "http://xmlns.oracle.com/Primavera/P6/V8.4/API/BusinessObjects"

# PlanningEz dependency types -> Primavera relationship type labels.
_REL_LABELS = {
    DependencyType.FINISH_TO_START: "Finish to Start",
    DependencyType.START_TO_START: "Start to Start",
    DependencyType.FINISH_TO_FINISH: "Finish to Finish",
    DependencyType.START_TO_FINISH: "Start to Finish",
}


@register_exporter
class PrimaveraExporter(BaseExporter):
    """Export a project to Primavera P6 XML."""

    format_key = "primavera"
    file_extension = "xml"
    display_name = "Primavera P6 (XML)"

    def __init__(self, hours_per_day: float = 8.0) -> None:
        """Initialize with the working-hours-per-day used for durations."""
        self.hours_per_day = hours_per_day

    def export(self, project: Project) -> str:
        """Serialize the project to Primavera P6 XML."""
        ET.register_namespace("", _NS)
        root = ET.Element(f"{{{_NS}}}APIBusinessObjects")
        project_el = self._sub(root, "Project", None)
        self._sub(project_el, "Id", (project.project_id or "PROJ")[:20])
        self._sub(project_el, "Name", project.name)
        if project.start_date:
            self._sub(project_el, "PlannedStartDate", f"{project.start_date.isoformat()}T08:00:00")

        self._append_wbs(project_el, project)
        obj_ids = self._append_activities(project_el, project)
        self._append_relationships(project_el, project, obj_ids)
        self._append_resources(project_el, project)

        ET.indent(root, space="  ")
        xml_body = ET.tostring(root, encoding="unicode")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_body}\n'

    # ------------------------------------------------------------------ #
    # Sections
    # ------------------------------------------------------------------ #
    def _append_wbs(self, project_el: ET.Element, project: Project) -> None:
        """Emit a WBS element for each summary task."""
        for index, task in enumerate(project.tasks, start=1):
            if task.task_type != TaskType.SUMMARY:
                continue
            wbs_el = self._sub(project_el, "WBS", None)
            self._sub(wbs_el, "ObjectId", str(index))
            self._sub(wbs_el, "Code", f"WBS.{index}")
            self._sub(wbs_el, "Name", task.name)

    def _append_activities(self, project_el: ET.Element, project: Project) -> Dict[str, int]:
        """Emit an Activity per non-summary task; return task_id -> ObjectId."""
        obj_ids: Dict[str, int] = {}
        counter = 1
        for task in project.tasks:
            if task.task_type == TaskType.SUMMARY:
                continue
            object_id = counter
            counter += 1
            obj_ids[task.task_id] = object_id

            activity = self._sub(project_el, "Activity", None)
            self._sub(activity, "ObjectId", str(object_id))
            self._sub(activity, "Id", f"A{1000 + object_id}")
            self._sub(activity, "Name", task.name)
            is_milestone = task.is_milestone or task.task_type == TaskType.MILESTONE
            self._sub(
                activity,
                "Type",
                "Finish Milestone" if is_milestone else "Task Dependent",
            )
            self._sub(
                activity,
                "PlannedDuration",
                str(round(task.duration * self.hours_per_day, 2)),
            )
            self._sub(activity, "PercentComplete", str(task.progress))
            if task.start_date:
                self._sub(activity, "PlannedStartDate", f"{task.start_date.isoformat()}T08:00:00")
            if task.end_date:
                self._sub(activity, "PlannedFinishDate", f"{task.end_date.isoformat()}T17:00:00")
        return obj_ids

    def _append_relationships(
        self, project_el: ET.Element, project: Project, obj_ids: Dict[str, int]
    ) -> None:
        """Emit a Relationship element for each dependency."""
        for dep in project.dependencies:
            pred = obj_ids.get(dep.predecessor_id)
            succ = obj_ids.get(dep.successor_id)
            if pred is None or succ is None:
                continue
            rel = self._sub(project_el, "Relationship", None)
            self._sub(rel, "PredecessorActivityObjectId", str(pred))
            self._sub(rel, "SuccessorActivityObjectId", str(succ))
            self._sub(rel, "Type", _REL_LABELS.get(dep.dependency_type, "Finish to Start"))
            self._sub(rel, "Lag", str(round(dep.lag * self.hours_per_day, 2)))

    def _append_resources(self, project_el: ET.Element, project: Project) -> None:
        """Emit a Resource element per project resource."""
        for index, resource in enumerate(project.resources, start=1):
            res_el = self._sub(project_el, "Resource", None)
            self._sub(res_el, "ObjectId", str(index))
            self._sub(res_el, "Id", f"R{1000 + index}")
            self._sub(res_el, "Name", resource.name)
            self._sub(res_el, "ResourceType", "Labor")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _sub(self, parent: ET.Element, tag: str, text: Optional[str]) -> ET.Element:
        """Create a namespaced sub-element, optionally with text."""
        element = ET.SubElement(parent, f"{{{_NS}}}{tag}")
        if text is not None:
            element.text = text
        return element
