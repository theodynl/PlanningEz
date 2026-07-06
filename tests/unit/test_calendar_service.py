"""Unit tests for calendar service."""

import pytest
from datetime import date, timedelta
from planningez.core.models.calendar import Calendar, Holiday, DayOfWeek, WorkingHours
from planningez.core.services import CalendarService


class TestCalendarService:
    """Test CalendarService functionality."""

    @pytest.fixture
    def calendar(self) -> Calendar:
        """Create a test calendar."""
        return Calendar(name="Test Calendar")

    @pytest.fixture
    def service(self, calendar: Calendar) -> CalendarService:
        """Create a calendar service."""
        return CalendarService(calendar)

    def test_is_working_day(self, service: CalendarService) -> None:
        """Test working day detection."""
        # Monday (2024-01-01) is a working day
        monday = date(2024, 1, 1)
        assert service.is_working_day(monday)

        # Saturday (2024-01-06) is not a working day
        saturday = date(2024, 1, 6)
        assert not service.is_working_day(saturday)

    def test_get_working_hours(self, service: CalendarService) -> None:
        """Test getting working hours for a day."""
        monday = date(2024, 1, 1)
        hours = service.get_working_hours(monday)
        assert hours > 0  # Should have working hours

        saturday = date(2024, 1, 6)
        hours = service.get_working_hours(saturday)
        assert hours == 0  # Weekend has no working hours

    def test_add_working_days(self, service: CalendarService) -> None:
        """Test adding working days."""
        start = date(2024, 1, 1)  # Monday
        result = service.add_working_days(start, 5)

        # 5 working days from Monday should be Monday next week
        assert (result - start).days >= 5

    def test_subtract_working_days(self, service: CalendarService) -> None:
        """Test subtracting working days."""
        start = date(2024, 1, 8)  # Monday
        result = service.subtract_working_days(start, 5)

        # 5 working days before should be close to the previous week
        assert (start - result).days >= 5

    def test_count_working_days(self, service: CalendarService) -> None:
        """Test counting working days between dates."""
        start = date(2024, 1, 1)  # Monday
        end = date(2024, 1, 5)    # Friday

        count = service.count_working_days(start, end)
        assert count == 5  # Mon-Fri = 5 working days

    def test_next_working_day(self, service: CalendarService) -> None:
        """Test getting next working day."""
        friday = date(2024, 1, 5)
        next_day = service.next_working_day(friday)

        # Next working day after Friday should be Monday
        assert next_day.weekday() == 0  # Monday

    def test_previous_working_day(self, service: CalendarService) -> None:
        """Test getting previous working day."""
        monday = date(2024, 1, 1)
        prev_day = service.previous_working_day(monday)

        # Previous working day before Monday should be Friday
        assert prev_day.weekday() == 4  # Friday

    def test_set_working_hours(self, service: CalendarService) -> None:
        """Test setting working hours for a day."""
        new_hours = WorkingHours(
            start_time=__import__("datetime").time(9, 0),
            end_time=__import__("datetime").time(18, 0),
            is_working_day=True,
            lunch_start=None,
            lunch_end=None,
        )
        service.set_working_hours(DayOfWeek.MONDAY, new_hours)

        monday = date(2024, 1, 1)
        hours = service.get_working_hours(monday)
        assert hours == 9.0  # 9 hours (no lunch break configured)

    def test_add_holiday(self, service: CalendarService) -> None:
        """Test adding a holiday."""
        holiday = Holiday(name="New Year", date=date(2024, 1, 1))
        service.add_holiday(holiday)

        assert not service.is_working_day(date(2024, 1, 1))

    def test_is_weekend(self, service: CalendarService) -> None:
        """Test weekend detection."""
        monday = date(2024, 1, 1)
        assert not service.is_weekend(monday)

        saturday = date(2024, 1, 6)
        assert service.is_weekend(saturday)

    def test_is_holiday(self, service: CalendarService) -> None:
        """Test holiday detection."""
        holiday = Holiday(name="Christmas", date=date(2024, 12, 25))
        service.add_holiday(holiday)

        assert service.is_holiday(date(2024, 12, 25))
        assert not service.is_holiday(date(2024, 12, 24))

    def test_get_working_days_in_range(self, service: CalendarService) -> None:
        """Test getting working days in a range."""
        start = date(2024, 1, 1)   # Monday
        end = date(2024, 1, 7)     # Sunday

        working_days = service.get_working_days_in_range(start, end)
        assert len(working_days) == 5  # Mon-Fri

    def test_create_standard_calendar(self) -> None:
        """Test creating a standard calendar."""
        calendar = CalendarService.create_standard_calendar("Business")
        assert calendar.name == "Business"
        assert len(calendar.working_hours) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
