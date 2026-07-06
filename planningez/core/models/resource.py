"""Resource model for PlanningEz."""

from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from uuid import uuid4


class ResourceRole(str, Enum):
    """Resource role enumeration."""

    MANAGER = "manager"
    ENGINEER = "engineer"
    TECHNICIAN = "technician"
    DESIGNER = "designer"
    CONSULTANT = "consultant"
    OTHER = "other"


@dataclass
class Resource:
    """Represents a project resource (person or equipment)."""

    name: str
    resource_id: str = field(default_factory=lambda: str(uuid4())[:8])
    role: ResourceRole = ResourceRole.OTHER
    company: Optional[str] = None
    daily_cost: float = 0.0
    availability: float = 100.0  # Percentage
    calendar_id: Optional[str] = None
    color: str = "#2E7D5A"
    email: Optional[str] = None
    phone: Optional[str] = None
    comments: str = ""

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate resource data after initialization."""
        if self.daily_cost < 0:
            raise ValueError("Daily cost cannot be negative")
        if not 0 <= self.availability <= 100:
            raise ValueError("Availability must be between 0 and 100")

    def set_availability(self, availability: float) -> None:
        """Set resource availability."""
        if not 0 <= availability <= 100:
            raise ValueError("Availability must be between 0 and 100")
        self.availability = availability
        self.updated_at = datetime.now()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Resource(id={self.resource_id}, name={self.name}, role={self.role})"
