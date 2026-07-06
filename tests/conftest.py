"""Pytest configuration and shared fixtures."""

import pytest
from datetime import date
from planningez.core.models import Project, Calendar


@pytest.fixture
def sample_project() -> Project:
    """Create a sample project for testing."""
    return Project(
        name="Sample Project",
        client="Sample Client",
        responsible="Project Manager",
        start_date=date(2024, 1, 1),
        target_end_date=date(2024, 12, 31),
    )


@pytest.fixture
def sample_calendar() -> Calendar:
    """Create a sample calendar for testing."""
    return Calendar(name="Standard Business Calendar")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
