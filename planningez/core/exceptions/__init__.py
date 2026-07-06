"""Exception classes for PlanningEz."""


class PlanningEzException(Exception):
    """Base exception for all PlanningEz errors."""

    pass


class ValidationError(PlanningEzException):
    """Raised when data validation fails."""

    pass


class DependencyError(PlanningEzException):
    """Raised when dependency-related operations fail."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when a circular dependency is detected."""

    pass


class CalendarError(PlanningEzException):
    """Raised when calendar-related operations fail."""

    pass


class ResourceError(PlanningEzException):
    """Raised when resource-related operations fail."""

    pass


class ExportError(PlanningEzException):
    """Raised when export operations fail."""

    pass


class ImportError(PlanningEzException):
    """Raised when import operations fail."""

    pass


__all__ = [
    "PlanningEzException",
    "ValidationError",
    "DependencyError",
    "CircularDependencyError",
    "CalendarError",
    "ResourceError",
    "ExportError",
    "ImportError",
]
