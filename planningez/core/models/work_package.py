"""Work Package model for PlanningEz.

A Work Package is the heart of PlanningEz: a self-contained, reusable block of
planning that can be inserted into any project. Each package bundles its own
tasks, hierarchy, internal dependencies, milestones, default resources,
documents, deliverables, risks, assumptions, suppliers and calendars, and is
versioned so it can be shared and evolved independently.
"""

from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from planningez.core.models.task import Task, TaskType
from planningez.core.models.resource import Resource
from planningez.core.models.dependency import Dependency
from planningez.core.models.calendar import Calendar
from planningez.utils.serialization import to_dict


class Discipline(str, Enum):
    """Common engineering / project disciplines."""

    ENGINEERING = "engineering"
    PROCESS = "process"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    AUTOMATION = "automation"
    PROCUREMENT = "procurement"
    MANUFACTURING = "manufacturing"
    INSTALLATION = "installation"
    COMMISSIONING = "commissioning"
    QUALITY = "quality"
    MANAGEMENT = "management"
    OTHER = "other"


@dataclass
class Milestone:
    """A significant point or event within a Work Package."""

    name: str
    milestone_id: str = field(default_factory=lambda: str(uuid4())[:8])
    offset_days: float = 0.0  # Days from the package start
    comments: str = ""


@dataclass
class Deliverable:
    """A tangible output produced by a Work Package."""

    name: str
    deliverable_id: str = field(default_factory=lambda: str(uuid4())[:8])
    description: str = ""
    document_ref: Optional[str] = None


@dataclass
class Risk:
    """A potential risk associated with a Work Package."""

    name: str
    risk_id: str = field(default_factory=lambda: str(uuid4())[:8])
    probability: float = 0.0  # 0..1
    impact: float = 0.0       # 0..1
    mitigation: str = ""

    @property
    def severity(self) -> float:
        """Return the risk severity (probability x impact)."""
        return self.probability * self.impact


@dataclass
class WorkPackage:
    """A reusable, self-contained block of planning."""

    name: str
    code: str = ""
    work_package_id: str = field(default_factory=lambda: str(uuid4())[:8])
    discipline: Discipline = Discipline.OTHER
    version: str = "1.0.0"
    description: str = ""

    # Planning content
    tasks: List[Task] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    milestones: List[Milestone] = field(default_factory=list)

    # Resourcing & context
    default_resources: List[Resource] = field(default_factory=list)
    calendars: List[Calendar] = field(default_factory=list)

    # Documentation & governance
    documents: List[str] = field(default_factory=list)
    deliverables: List[Deliverable] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    suppliers: List[str] = field(default_factory=list)

    # Estimation
    estimated_duration: float = 0.0
    duration_unit: str = "days"

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_task(self, task: Task) -> None:
        """Add a task to the package."""
        self.tasks.append(task)
        self.updated_at = datetime.now()

    def add_dependency(self, dependency: Dependency) -> None:
        """Add an internal dependency to the package."""
        self.dependencies.append(dependency)
        self.updated_at = datetime.now()

    def add_milestone(self, milestone: Milestone) -> None:
        """Add a milestone to the package."""
        self.milestones.append(milestone)
        self.updated_at = datetime.now()

    def compute_estimated_duration(self) -> float:
        """Estimate package duration as the sum of non-milestone task durations.

        This is a simple roll-up used when no explicit estimate is provided; the
        planning engine computes the true critical-path duration once the
        package is instantiated in a project.
        """
        total = sum(
            t.duration for t in self.tasks if t.task_type != TaskType.MILESTONE
        )
        self.estimated_duration = total
        return total

    def bump_version(self, level: str = "patch") -> str:
        """Increment the semantic version and return the new value.

        Args:
            level: One of ``"major"``, ``"minor"`` or ``"patch"``.
        """
        try:
            major, minor, patch = (int(p) for p in self.version.split("."))
        except ValueError:
            major, minor, patch = 1, 0, 0
        if level == "major":
            major, minor, patch = major + 1, 0, 0
        elif level == "minor":
            minor, patch = minor + 1, 0
        else:
            patch += 1
        self.version = f"{major}.{minor}.{patch}"
        self.updated_at = datetime.now()
        return self.version

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Work Package to a JSON-safe dict."""
        return to_dict(self)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"WorkPackage(code={self.code!r}, name={self.name!r}, "
            f"v{self.version}, tasks={len(self.tasks)})"
        )
