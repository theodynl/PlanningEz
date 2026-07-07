"""Calendar model for PlanningEz."""

from enum import Enum
from datetime import datetime, date, time
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from uuid import uuid4


class CalendarType(str, Enum):
    """Calendar type enumeration."""

    COMPANY = "company"
    PROJECT = "project"
    TEAM = "team"
    RESOURCE = "resource"
    SUBCONTRACTOR = "subcontractor"


class DayOfWeek(str, Enum):
    """Day of week enumeration."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


@dataclass
class Holiday:
    """Represents a holiday or non-working day."""

    name: str
    date: date
    is_recurring: bool = False  # Recurring yearly
    holiday_id: str = field(default_factory=lambda: str(uuid4())[:8])

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Holiday({self.name}, {self.date})"


@dataclass
class WorkingHours:
    """Represents working hours for a day."""

    start_time: time = field(default_factory=lambda: time(8, 0))
    end_time: time = field(default_factory=lambda: time(17, 0))
    is_working_day: bool = True
    lunch_start: Optional[time] = field(default_factory=lambda: time(12, 0))
    lunch_end: Optional[time] = field(default_factory=lambda: time(13, 0))

    def working_hours_count(self) -> float:
        """Calculate working hours for the day."""
        if not self.is_working_day:
            return 0.0

        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        total_minutes = end_minutes - start_minutes

        if self.lunch_start and self.lunch_end:
            lunch_start_minutes = (
                self.lunch_start.hour * 60 + self.lunch_start.minute
            )
            lunch_end_minutes = self.lunch_end.hour * 60 + self.lunch_end.minute
            total_minutes -= lunch_end_minutes - lunch_start_minutes

        return total_minutes / 60.0


@dataclass
class Calendar:
    """Represents a project calendar."""

    name: str
    calendar_type: CalendarType = CalendarType.PROJECT
    calendar_id: str = field(default_factory=lambda: str(uuid4())[:8])
    working_hours: Dict[DayOfWeek, WorkingHours] = field(default_factory=dict)
    holidays: List[Holiday] = field(default_factory=list)
    base_calendar_id: Optional[str] = None  # Can be based on another calendar

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize default working hours if not provided."""
        if not self.working_hours:
            # Default: Monday-Friday 8h-17h, Saturday-Sunday off
            for day in DayOfWeek:
                if day in [DayOfWeek.SATURDAY, DayOfWeek.SUNDAY]:
                    self.working_hours[day] = WorkingHours(is_working_day=False)
                else:
                    self.working_hours[day] = WorkingHours()

    def is_working_day(self, date_obj: date) -> bool:
        """Check if a date is a working day."""
        # Check holidays first
        for holiday in self.holidays:
            if not holiday.is_recurring and holiday.date == date_obj:
                return False
            if holiday.is_recurring and (
                holiday.date.month == date_obj.month
                and holiday.date.day == date_obj.day
            ):
                return False

        day_name = DayOfWeek(date_obj.strftime("%A").lower())
        return self.working_hours[day_name].is_working_day

    def add_holiday(self, holiday: Holiday) -> None:
        """Add a holiday to the calendar."""
        self.holidays.append(holiday)
        self.updated_at = datetime.now()

    def remove_holiday(self, holiday_id: str) -> None:
        """Remove a holiday from the calendar."""
        self.holidays = [h for h in self.holidays if h.holiday_id != holiday_id]
        self.updated_at = datetime.now()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Calendar(id={self.calendar_id}, name={self.name}, type={self.calendar_type})"
