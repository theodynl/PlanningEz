"""Pytest configuration and shared fixtures."""

import os
import tempfile

# Isolate the persistent Work Package library in a throwaway directory so tests
# never touch the developer's real ~/.planningez data. Set before any test
# imports the API store (which reads this at import time).
os.environ.setdefault(
    "PLANNINGEZ_DATA_DIR", tempfile.mkdtemp(prefix="planningez-test-")
)

import pytest  # noqa: E402
from datetime import date  # noqa: E402
from planningez.core.models import Project, Calendar  # noqa: E402


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
