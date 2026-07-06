"""Dependency model for PlanningEz."""

from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from uuid import uuid4


class DependencyType(str, Enum):
    """Dependency type enumeration."""

    FINISH_TO_START = "FS"  # Finish-to-Start (standard)
    START_TO_START = "SS"   # Start-to-Start
    FINISH_TO_FINISH = "FF" # Finish-to-Finish
    START_TO_FINISH = "SF"  # Start-to-Finish (rare)


@dataclass
class Dependency:
    """Represents a dependency between two tasks."""

    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag: float = 0.0  # Positive lag adds delay, negative removes it
    dep_id: str = field(default_factory=lambda: str(uuid4())[:8])

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate dependency data after initialization."""
        if self.predecessor_id == self.successor_id:
            raise ValueError("A task cannot depend on itself")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Dependency("
            f"{self.predecessor_id} "
            f"{self.dependency_type.value} "
            f"{self.successor_id}"
            f"{'[+' + str(self.lag) + ']' if self.lag else ''}"
            f")"
        )
