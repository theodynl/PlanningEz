"""Task model for PlanningEz."""

from enum import Enum
from datetime import datetime, date
from typing import Optional, List
from dataclasses import dataclass, field
from uuid import uuid4


class TaskType(str, Enum):
    """Task type enumeration."""

    TASK = "task"
    MILESTONE = "milestone"
    PHASE = "phase"
    SUMMARY = "summary"


class TaskStatus(str, Enum):
    """Task status enumeration."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Represents a project task."""

    name: str
    task_id: str = field(default_factory=lambda: str(uuid4())[:8])
    duration: float = 1.0
    unit: str = "days"
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.TASK
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    parent_id: Optional[str] = None
    responsible: Optional[str] = None
    color: str = "#2E7D5A"
    progress: float = 0.0
    comments: str = ""
    is_milestone: bool = False
    is_recurring: bool = False
    deliverable: Optional[str] = None
    category: Optional[str] = None

    # Calculated fields
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    total_slack: float = 0.0
    free_slack: float = 0.0
    on_critical_path: bool = False

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate task data after initialization."""
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
        if not 0 <= self.progress <= 100:
            raise ValueError("Progress must be between 0 and 100")

    def is_summary(self) -> bool:
        """Check if this is a summary task."""
        return self.task_type == TaskType.SUMMARY

    def is_phase(self) -> bool:
        """Check if this is a phase."""
        return self.task_type == TaskType.PHASE

    def update_progress(self, progress: float) -> None:
        """Update task progress."""
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        self.progress = progress
        self.updated_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.actual_end_date = date.today()
        self.updated_at = datetime.now()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Task(id={self.task_id}, name={self.name}, duration={self.duration} {self.unit})"
