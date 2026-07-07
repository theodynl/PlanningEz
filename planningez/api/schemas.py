"""Pydantic request schemas for the PlanningEz API.

Responses are serialized straight from the dataclass models via
:func:`planningez.utils.serialization.to_dict`, so only inbound request bodies
need explicit schemas here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    """Create a project using one of the supported start modes."""

    mode: str = Field(default="empty", description="empty|template|work_package|wbs|json")
    name: str = "New Project"
    # WBS mode
    wbs_format: str = "json"  # json|csv|xml
    wbs_content: Optional[str] = None
    create_tasks: bool = True
    # Work-package mode
    work_package_ids: List[str] = Field(default_factory=list)
    connect_mode: str = "sequential"  # sequential|parallel|custom
    # template / json mode
    document: Optional[Dict[str, Any]] = None


class GenerateRequest(BaseModel):
    """Generate a project from a selection of Work Packages."""

    name: str = "Generated Project"
    work_package_ids: List[str] = Field(default_factory=list)
    connect_mode: str = "sequential"


class TaskCreateRequest(BaseModel):
    """Create a task inside a project."""

    name: str
    duration: float = 1.0
    task_type: str = "task"
    parent_id: Optional[str] = None
    responsible: Optional[str] = None
    progress: float = 0.0
    is_milestone: bool = False


class TaskUpdateRequest(BaseModel):
    """Partial update of a task (only provided fields change).

    ``constraint_date`` uses a sentinel so it can be *cleared*: omit the field
    to leave it unchanged, pass ``null`` to remove the constraint, or an ISO
    date string to set a "start no earlier than" constraint.
    """

    name: Optional[str] = None
    duration: Optional[float] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    responsible: Optional[str] = None
    parent_id: Optional[str] = None
    clear_parent: bool = False
    constraint_date: Optional[str] = Field(default=None)
    clear_constraint: bool = False


class DependencyCreateRequest(BaseModel):
    """Create a dependency between two tasks."""

    predecessor_id: str
    successor_id: str
    dependency_type: str = "FS"
    lag: float = 0.0


class ResourceCreateRequest(BaseModel):
    """Create a resource inside a project."""

    name: str
    role: str = "other"
    daily_cost: float = 0.0
    availability: float = 100.0


class WBSPreviewRequest(BaseModel):
    """Preview a WBS tree parsed from raw content."""

    format: str = "json"  # json|csv|xml
    content: str
    name: str = "WBS"


class WorkPackageImportRequest(BaseModel):
    """Create/import or update a Work Package from a JSON document.

    When ``chain_tasks`` is true, the server (re)builds sequential finish-to-start
    dependencies between consecutive non-milestone tasks — convenient when
    editing a package through the form UI, which does not expose a dependency
    editor.
    """

    document: Dict[str, Any]
    chain_tasks: bool = False
