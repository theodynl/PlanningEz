"""Unit tests for data models."""

import pytest
from datetime import date, datetime
from planningez.core.models import (
    Project,
    Task,
    Resource,
    Dependency,
    Calendar,
    TaskType,
    TaskStatus,
    TaskPriority,
    DependencyType,
    ResourceRole,
)
from planningez.core.exceptions import ValidationError


class TestTask:
    """Test Task model."""

    def test_task_creation(self) -> None:
        """Test creating a task."""
        task = Task(name="Test Task", duration=5.0)
        assert task.name == "Test Task"
        assert task.duration == 5.0
        assert task.status == TaskStatus.NOT_STARTED
        assert task.progress == 0.0
        assert task.task_id  # Should have auto-generated ID

    def test_task_invalid_duration(self) -> None:
        """Test task validation."""
        with pytest.raises(ValueError):
            Task(name="Bad Task", duration=-1)

    def test_task_invalid_progress(self) -> None:
        """Test invalid progress."""
        with pytest.raises(ValueError):
            Task(name="Task", duration=5, progress=150)

    def test_task_update_progress(self) -> None:
        """Test updating task progress."""
        task = Task(name="Task", duration=5)
        task.update_progress(50)
        assert task.progress == 50
        assert task.status == TaskStatus.NOT_STARTED

    def test_task_mark_completed(self) -> None:
        """Test marking task as completed."""
        task = Task(name="Task", duration=5)
        task.mark_completed()
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100
        assert task.actual_end_date == date.today()


class TestResource:
    """Test Resource model."""

    def test_resource_creation(self) -> None:
        """Test creating a resource."""
        resource = Resource(
            name="John Doe",
            role=ResourceRole.ENGINEER,
            daily_cost=200.0,
            availability=100.0,
        )
        assert resource.name == "John Doe"
        assert resource.role == ResourceRole.ENGINEER
        assert resource.daily_cost == 200.0
        assert resource.availability == 100.0

    def test_resource_invalid_cost(self) -> None:
        """Test resource with invalid cost."""
        with pytest.raises(ValueError):
            Resource(name="Bad Resource", daily_cost=-100)

    def test_resource_invalid_availability(self) -> None:
        """Test resource with invalid availability."""
        with pytest.raises(ValueError):
            Resource(name="Bad Resource", availability=150)

    def test_resource_set_availability(self) -> None:
        """Test setting resource availability."""
        resource = Resource(name="Resource", availability=100)
        resource.set_availability(50)
        assert resource.availability == 50


class TestDependency:
    """Test Dependency model."""

    def test_dependency_creation(self) -> None:
        """Test creating a dependency."""
        dep = Dependency(
            predecessor_id="task1",
            successor_id="task2",
            dependency_type=DependencyType.FINISH_TO_START,
            lag=0,
        )
        assert dep.predecessor_id == "task1"
        assert dep.successor_id == "task2"
        assert dep.dependency_type == DependencyType.FINISH_TO_START

    def test_dependency_self_reference(self) -> None:
        """Test that a task cannot depend on itself."""
        with pytest.raises(ValueError):
            Dependency(predecessor_id="task1", successor_id="task1")

    def test_dependency_with_lag(self) -> None:
        """Test dependency with lag."""
        dep = Dependency(
            predecessor_id="task1",
            successor_id="task2",
            lag=2,
        )
        assert dep.lag == 2


class TestCalendar:
    """Test Calendar model."""

    def test_calendar_creation(self) -> None:
        """Test creating a calendar."""
        calendar = Calendar(name="Standard")
        assert calendar.name == "Standard"
        assert len(calendar.working_hours) == 7  # Should have default working hours

    def test_calendar_is_working_day(self) -> None:
        """Test checking working days."""
        calendar = Calendar(name="Test")
        # Monday is working day by default
        monday = date(2024, 1, 1)  # Monday
        assert calendar.is_working_day(monday)

    def test_calendar_add_holiday(self) -> None:
        """Test adding a holiday."""
        from planningez.core.models.calendar import Holiday

        calendar = Calendar(name="Test")
        holiday = Holiday(name="New Year", date=date(2024, 1, 1))
        calendar.add_holiday(holiday)
        assert len(calendar.holidays) == 1
        assert not calendar.is_working_day(date(2024, 1, 1))


class TestProject:
    """Test Project model."""

    def test_project_creation(self) -> None:
        """Test creating a project."""
        project = Project(
            name="Test Project",
            client="Test Client",
            responsible="Manager",
        )
        assert project.name == "Test Project"
        assert project.client == "Test Client"
        assert len(project.calendars) >= 1  # Should have default calendar

    def test_project_add_task(self) -> None:
        """Test adding a task to project."""
        project = Project(name="Project")
        task = Task(name="Task 1", duration=5)
        project.add_task(task)
        assert len(project.tasks) == 1
        assert project.get_task(task.task_id) == task

    def test_project_remove_task(self) -> None:
        """Test removing a task."""
        project = Project(name="Project")
        task = Task(name="Task 1")
        project.add_task(task)
        project.remove_task(task.task_id)
        assert len(project.tasks) == 0

    def test_project_add_resource(self) -> None:
        """Test adding a resource."""
        project = Project(name="Project")
        resource = Resource(name="Resource 1")
        project.add_resource(resource)
        assert len(project.resources) == 1
        assert project.get_resource(resource.resource_id) == resource

    def test_project_add_dependency(self) -> None:
        """Test adding a dependency."""
        project = Project(name="Project")
        task1 = Task(name="Task 1")
        task2 = Task(name="Task 2")
        project.add_task(task1)
        project.add_task(task2)

        dep = Dependency(
            predecessor_id=task1.task_id,
            successor_id=task2.task_id,
        )
        project.add_dependency(dep)
        assert len(project.dependencies) == 1

    def test_project_get_dependencies(self) -> None:
        """Test getting task dependencies."""
        project = Project(name="Project")
        task1 = Task(name="Task 1")
        task2 = Task(name="Task 2")
        project.add_task(task1)
        project.add_task(task2)

        dep = Dependency(
            predecessor_id=task1.task_id,
            successor_id=task2.task_id,
        )
        project.add_dependency(dep)

        incoming, outgoing = project.get_dependencies_for_task(task2.task_id)
        assert len(incoming) == 1
        assert incoming[0].predecessor_id == task1.task_id

        incoming, outgoing = project.get_dependencies_for_task(task1.task_id)
        assert len(outgoing) == 1
        assert outgoing[0].successor_id == task2.task_id

    def test_project_get_default_calendar(self) -> None:
        """Test getting default calendar."""
        project = Project(name="Project")
        calendar = project.get_default_calendar()
        assert calendar.calendar_id == "default"

    def test_project_calculate_progress(self) -> None:
        """Test project progress calculation."""
        project = Project(name="Project")
        task1 = Task(name="Task 1", progress=50)
        task2 = Task(name="Task 2", progress=100)
        project.add_task(task1)
        project.add_task(task2)

        progress = project.calculate_progress()
        assert progress == 75.0  # (50 + 100) / 2

    def test_project_get_tasks_by_responsible(self) -> None:
        """Test getting tasks by responsible party."""
        project = Project(name="Project")
        task1 = Task(name="Task 1", responsible="John")
        task2 = Task(name="Task 2", responsible="Jane")
        project.add_task(task1)
        project.add_task(task2)

        john_tasks = project.get_tasks_by_responsible("John")
        assert len(john_tasks) == 1
        assert john_tasks[0].name == "Task 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
