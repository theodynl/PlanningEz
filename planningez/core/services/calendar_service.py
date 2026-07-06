"""Calendar management and working day calculations."""

import logging
from datetime import date, timedelta, time
from typing import List, Optional

from planningez.core.models.calendar import Calendar, Holiday, WorkingHours, DayOfWeek

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for calendar operations and working day calculations."""

    def __init__(self, calendar: Calendar) -> None:
        """Initialize calendar service.

        Args:
            calendar: Calendar instance to manage
        """
        self.calendar = calendar

    def is_working_day(self, date_obj: date) -> bool:
        """Check if a date is a working day.

        Args:
            date_obj: Date to check

        Returns:
            True if the date is a working day
        """
        return self.calendar.is_working_day(date_obj)

    def get_working_hours(self, date_obj: date) -> float:
        """Get working hours for a specific date.

        Args:
            date_obj: Date to get working hours for

        Returns:
            Number of working hours (0 if not a working day)
        """
        if not self.is_working_day(date_obj):
            return 0.0

        day_name = DayOfWeek(date_obj.strftime("%A").lower())
        working_hours = self.calendar.working_hours.get(day_name)
        if working_hours:
            return working_hours.working_hours_count()
        return 8.0  # Default 8 hours

    def add_working_days(self, start_date: date, days: float) -> date:
        """Add working days to a date.

        Args:
            start_date: Starting date
            days: Number of working days to add

        Returns:
            Result date
        """
        current_date = start_date
        remaining_days = days

        while remaining_days > 0:
            current_date += timedelta(days=1)
            if self.is_working_day(current_date):
                remaining_days -= 1

        return current_date

    def subtract_working_days(self, start_date: date, days: float) -> date:
        """Subtract working days from a date.

        Args:
            start_date: Starting date
            days: Number of working days to subtract

        Returns:
            Result date
        """
        current_date = start_date
        remaining_days = days

        while remaining_days > 0:
            current_date -= timedelta(days=1)
            if self.is_working_day(current_date):
                remaining_days -= 1

        return current_date

    def count_working_days(self, start_date: date, end_date: date) -> int:
        """Count working days between two dates (inclusive).

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of working days
        """
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        count = 0
        current_date = start_date

        while current_date <= end_date:
            if self.is_working_day(current_date):
                count += 1
            current_date += timedelta(days=1)

        return count

    def next_working_day(self, start_date: date) -> date:
        """Get the next working day from a given date.

        Args:
            start_date: Starting date

        Returns:
            Next working day
        """
        current_date = start_date + timedelta(days=1)
        while not self.is_working_day(current_date):
            current_date += timedelta(days=1)
        return current_date

    def previous_working_day(self, start_date: date) -> date:
        """Get the previous working day from a given date.

        Args:
            start_date: Starting date

        Returns:
            Previous working day
        """
        current_date = start_date - timedelta(days=1)
        while not self.is_working_day(current_date):
            current_date -= timedelta(days=1)
        return current_date

    def set_working_hours(self, day: DayOfWeek, working_hours: WorkingHours) -> None:
        """Set working hours for a specific day.

        Args:
            day: Day of week
            working_hours: Working hours configuration
        """
        self.calendar.working_hours[day] = working_hours
        logger.info("Updated working hours for %s", day)

    def add_holiday(self, holiday: Holiday) -> None:
        """Add a holiday to the calendar.

        Args:
            holiday: Holiday to add
        """
        self.calendar.add_holiday(holiday)
        logger.info("Added holiday: %s on %s", holiday.name, holiday.date)

    def remove_holiday(self, holiday_id: str) -> None:
        """Remove a holiday from the calendar.

        Args:
            holiday_id: Holiday ID to remove
        """
        self.calendar.remove_holiday(holiday_id)
        logger.info("Removed holiday: %s", holiday_id)

    def get_working_days_in_range(
        self, start_date: date, end_date: date
    ) -> List[date]:
        """Get all working days in a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of working days
        """
        working_days = []
        current_date = start_date

        while current_date <= end_date:
            if self.is_working_day(current_date):
                working_days.append(current_date)
            current_date += timedelta(days=1)

        return working_days

    def is_weekend(self, date_obj: date) -> bool:
        """Check if a date is a weekend.

        Args:
            date_obj: Date to check

        Returns:
            True if the date is a weekend
        """
        day_name = DayOfWeek(date_obj.strftime("%A").lower())
        return day_name in [DayOfWeek.SATURDAY, DayOfWeek.SUNDAY]

    def is_holiday(self, date_obj: date) -> bool:
        """Check if a date is a holiday.

        Args:
            date_obj: Date to check

        Returns:
            True if the date is a holiday
        """
        for holiday in self.calendar.holidays:
            if not holiday.is_recurring and holiday.date == date_obj:
                return True
            if holiday.is_recurring and (
                holiday.date.month == date_obj.month
                and holiday.date.day == date_obj.day
            ):
                return True
        return False

    def get_holidays_in_range(self, start_date: date, end_date: date) -> List[Holiday]:
        """Get all holidays in a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of holidays
        """
        holidays = []
        current_date = start_date

        while current_date <= end_date:
            if self.is_holiday(current_date):
                for holiday in self.calendar.holidays:
                    if not holiday.is_recurring and holiday.date == current_date:
                        holidays.append(holiday)
                    elif holiday.is_recurring and (
                        holiday.date.month == current_date.month
                        and holiday.date.day == current_date.day
                    ):
                        holidays.append(holiday)
            current_date += timedelta(days=1)

        return holidays

    @staticmethod
    def create_standard_calendar(name: str = "Standard") -> Calendar:
        """Create a standard business calendar (Monday-Friday, 8h-17h).

        Args:
            name: Calendar name

        Returns:
            Calendar instance
        """
        calendar = Calendar(name=name)
        return calendar
