"""Factory helpers to rebuild PlanningEz models from plain dicts.

These are the inverse of the ``to_dict`` / serialization helpers and are used
when loading Work Packages, projects and templates back from JSON. Each builder
filters unknown keys and coerces enum/date fields so that hand-written or
externally produced JSON loads cleanly.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any, Callable, Dict, Type, TypeVar

from planningez.core.models.task import Task, TaskType, TaskStatus, TaskPriority
from planningez.core.models.resource import Resource, ResourceRole
from planningez.core.models.dependency import Dependency, DependencyType
from planningez.core.models.calendar import Calendar, CalendarType, Holiday
from planningez.core.models.project import Project
from planningez.core.models.work_package import (
    WorkPackage,
    Discipline,
    Milestone,
    Deliverable,
    Risk,
)
from planningez.utils.serialization import parse_date

T = TypeVar("T")


def _filtered(cls: Type[T], data: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the keys of ``data`` that map to fields of ``cls``."""
    valid = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    return {k: v for k, v in data.items() if k in valid}


def build_task(data: Dict[str, Any]) -> Task:
    """Rebuild a :class:`Task` from a dict."""
    payload = _filtered(Task, data)
    if "status" in payload and payload["status"] is not None:
        payload["status"] = TaskStatus(payload["status"])
    if "priority" in payload and payload["priority"] is not None:
        payload["priority"] = TaskPriority(payload["priority"])
    if "task_type" in payload and payload["task_type"] is not None:
        payload["task_type"] = TaskType(payload["task_type"])
    for date_field in ("start_date", "end_date", "actual_start_date", "actual_end_date"):
        if date_field in payload:
            payload[date_field] = parse_date(payload[date_field])
    # Metadata timestamps are recreated by the dataclass defaults.
    payload.pop("created_at", None)
    payload.pop("updated_at", None)
    return Task(**payload)


def build_resource(data: Dict[str, Any]) -> Resource:
    """Rebuild a :class:`Resource` from a dict."""
    payload = _filtered(Resource, data)
    if "role" in payload and payload["role"] is not None:
        payload["role"] = ResourceRole(payload["role"])
    payload.pop("created_at", None)
    payload.pop("updated_at", None)
    return Resource(**payload)


def build_dependency(data: Dict[str, Any]) -> Dependency:
    """Rebuild a :class:`Dependency` from a dict."""
    payload = _filtered(Dependency, data)
    if "dependency_type" in payload and payload["dependency_type"] is not None:
        payload["dependency_type"] = DependencyType(payload["dependency_type"])
    payload.pop("created_at", None)
    payload.pop("updated_at", None)
    return Dependency(**payload)


def build_calendar(data: Dict[str, Any]) -> Calendar:
    """Rebuild a :class:`Calendar` (holidays preserved, hours reset to defaults)."""
    payload = _filtered(Calendar, data)
    if "calendar_type" in payload and payload["calendar_type"] is not None:
        payload["calendar_type"] = CalendarType(payload["calendar_type"])
    holidays_data = payload.get("holidays", []) or []
    payload["holidays"] = [
        Holiday(
            name=h["name"],
            date=parse_date(h.get("date")),
            is_recurring=h.get("is_recurring", False),
            holiday_id=h.get("holiday_id", ""),
        )
        for h in holidays_data
    ]
    # Working hours use time objects; let __post_init__ rebuild sensible defaults.
    payload.pop("working_hours", None)
    payload.pop("created_at", None)
    payload.pop("updated_at", None)
    return Calendar(**payload)


def _build_list(data: Any, builder: Callable[[Dict[str, Any]], T]) -> list[T]:
    """Apply a builder to each item of a list (tolerating ``None``)."""
    return [builder(item) for item in (data or [])]


def build_work_package(data: Dict[str, Any]) -> WorkPackage:
    """Rebuild a :class:`WorkPackage` and its nested content from a dict."""
    payload = _filtered(WorkPackage, data)
    if "discipline" in payload and payload["discipline"] is not None:
        payload["discipline"] = Discipline(payload["discipline"])

    payload["tasks"] = _build_list(payload.get("tasks"), build_task)
    payload["dependencies"] = _build_list(payload.get("dependencies"), build_dependency)
    payload["default_resources"] = _build_list(
        payload.get("default_resources"), build_resource
    )
    payload["calendars"] = _build_list(payload.get("calendars"), build_calendar)
    payload["milestones"] = [
        Milestone(**{k: v for k, v in m.items() if k in {f.name for f in fields(Milestone)}})
        for m in (payload.get("milestones") or [])
    ]
    payload["deliverables"] = [
        Deliverable(
            **{k: v for k, v in d.items() if k in {f.name for f in fields(Deliverable)}}
        )
        for d in (payload.get("deliverables") or [])
    ]
    payload["risks"] = [
        Risk(**{k: v for k, v in r.items() if k in {f.name for f in fields(Risk)}})
        for r in (payload.get("risks") or [])
    ]
    payload.pop("created_at", None)
    payload.pop("updated_at", None)
    return WorkPackage(**payload)


def build_project(data: Dict[str, Any]) -> Project:
    """Rebuild a :class:`Project` and its collections from a dict."""
    payload = _filtered(Project, data)
    for date_field in ("start_date", "target_end_date", "actual_end_date"):
        if date_field in payload:
            payload[date_field] = parse_date(payload[date_field])
    payload["tasks"] = _build_list(payload.get("tasks"), build_task)
    payload["resources"] = _build_list(payload.get("resources"), build_resource)
    payload["dependencies"] = _build_list(payload.get("dependencies"), build_dependency)
    calendars = _build_list(payload.get("calendars"), build_calendar)
    # Ensure the project always has a default calendar (Project.__post_init__
    # only adds one when the list is empty).
    payload["calendars"] = calendars if calendars else []
    payload.pop("created_at", None)
    payload.pop("updated_at", None)
    return Project(**payload)
