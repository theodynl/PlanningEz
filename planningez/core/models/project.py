"""Project model for PlanningEz."""

from datetime import datetime, date
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from uuid import uuid4

from planningez.core.models.task import Task
from planningez.core.models.resource import Resource
from planningez.core.models.dependency import Dependency
from planningez.core.models.calendar import Calendar


@dataclass
class Project:
    """Represents a complete project."""

    name: str
    project_id: str = field(default_factory=lambda: str(uuid4())[:8])
    client: Optional[str] = None
    responsible: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    version: str = "1.0.0"
    comments: str = ""

    # Collections
    tasks: List[Task] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    calendars: List[Calendar] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Calculated fields
    total_duration: float = 0.0
    total_cost: float = 0.0
    progress: float = 0.0
    critical_path_tasks: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate project data after initialization."""
        if not self.calendars:
            default_calendar = Calendar(name="Default", calendar_id="default")
            self.calendars.append(default_calendar)

    def add_task(self, task: Task) -> None:
        """Add a task to the project."""
        self.tasks.append(task)
        self.updated_at = datetime.now()

    def remove_task(self, task_id: str) -> None:
        """Remove a task from the project."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        # Remove related dependencies
        self.dependencies = [
            d for d in self.dependencies
            if d.predecessor_id != task_id and d.successor_id != task_id
        ]
        self.updated_at = datetime.now()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the project."""
        self.resources.append(resource)
        self.updated_at = datetime.now()

    def remove_resource(self, resource_id: str) -> None:
        """Remove a resource from the project."""
        self.resources = [r for r in self.resources if r.resource_id != resource_id]
        self.updated_at = datetime.now()

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by ID."""
        for resource in self.resources:
            if resource.resource_id == resource_id:
                return resource
        return None

    def add_dependency(self, dependency: Dependency) -> None:
        """Add a dependency to the project."""
        self.dependencies.append(dependency)
        self.updated_at = datetime.now()

    def remove_dependency(self, dep_id: str) -> None:
        """Remove a dependency from the project."""
        self.dependencies = [d for d in self.dependencies if d.dep_id != dep_id]
        self.updated_at = datetime.now()

    def get_dependencies_for_task(self, task_id: str) -> tuple[
        List[Dependency], List[Dependency]
    ]:
        """Get incoming and outgoing dependencies for a task."""
        incoming = [d for d in self.dependencies if d.successor_id == task_id]
        outgoing = [d for d in self.dependencies if d.predecessor_id == task_id]
        return incoming, outgoing

    def add_calendar(self, calendar: Calendar) -> None:
        """Add a calendar to the project."""
        self.calendars.append(calendar)
        self.updated_at = datetime.now()

    def remove_calendar(self, calendar_id: str) -> None:
        """Remove a calendar from the project."""
        if calendar_id == "default":
            raise ValueError("Cannot remove the default calendar")
        self.calendars = [c for c in self.calendars if c.calendar_id != calendar_id]
        self.updated_at = datetime.now()

    def get_calendar(self, calendar_id: str) -> Optional[Calendar]:
        """Get a calendar by ID."""
        for calendar in self.calendars:
            if calendar.calendar_id == calendar_id:
                return calendar
        return None

    def get_default_calendar(self) -> Calendar:
        """Get the default calendar."""
        for calendar in self.calendars:
            if calendar.calendar_id == "default":
                return calendar
        # Create default if not found
        default = Calendar(name="Default", calendar_id="default")
        self.calendars.append(default)
        return default

    def calculate_progress(self) -> float:
        """Calculate overall project progress."""
        if not self.tasks:
            return 0.0
        total_progress = sum(t.progress for t in self.tasks)
        return total_progress / len(self.tasks)

    def get_tasks_by_responsible(
        self, responsible: str
    ) -> List[Task]:
        """Get all tasks assigned to a specific resource."""
        return [t for t in self.tasks if t.responsible == responsible]

    def get_root_tasks(self) -> List[Task]:
        """Get all root-level tasks (no parent)."""
        return [t for t in self.tasks if t.parent_id is None]

    def get_child_tasks(self, parent_id: str) -> List[Task]:
        """Get all child tasks of a parent."""
        return [t for t in self.tasks if t.parent_id == parent_id]

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Project("
            f"id={self.project_id}, "
            f"name={self.name}, "
            f"tasks={len(self.tasks)}, "
            f"resources={len(self.resources)}"
            f")"
        )
