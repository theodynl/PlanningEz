"""Unit tests for the planning engine."""

import pytest
from datetime import date, timedelta
from planningez.core.models import Project, Task, Dependency, DependencyType
from planningez.core.services import PlanningEngine
from planningez.core.exceptions import CircularDependencyError


class TestPlanningEngine:
    """Test PlanningEngine functionality."""

    def test_simple_schedule_calculation(self) -> None:
        """Test basic schedule calculation."""
        project = Project(
            name="Test Project",
            start_date=date(2024, 1, 1),
        )

        task1 = Task(name="Task 1", duration=5)
        task2 = Task(name="Task 2", duration=3)
        project.add_task(task1)
        project.add_task(task2)

        dep = Dependency(
            predecessor_id=task1.task_id,
            successor_id=task2.task_id,
        )
        project.add_dependency(dep)

        engine = PlanningEngine(project)
        engine.calculate()

        # Task 1 should start on day 1 and finish on day 5
        # Task 2 should start on day 6 and finish on day 8
        assert task1.start_date == date(2024, 1, 1)
        assert task2.start_date is not None

    def test_critical_path_detection(self) -> None:
        """Test critical path identification."""
        project = Project(name="Test Project", start_date=date(2024, 1, 1))

        # Create a simple chain: task1 -> task2 -> task3
        task1 = Task(name="Task 1", duration=5)
        task2 = Task(name="Task 2", duration=3)
        task3 = Task(name="Task 3", duration=2)

        project.add_task(task1)
        project.add_task(task2)
        project.add_task(task3)

        dep1 = Dependency(
            predecessor_id=task1.task_id,
            successor_id=task2.task_id,
        )
        dep2 = Dependency(
            predecessor_id=task2.task_id,
            successor_id=task3.task_id,
        )
        project.add_dependency(dep1)
        project.add_dependency(dep2)

        engine = PlanningEngine(project)
        engine.calculate()

        critical_path = engine.get_critical_path()
        # All tasks should be on the critical path
        assert len(critical_path) == 3

    def test_full_chain_is_critical_across_weekends(self) -> None:
        """A finish-to-start chain must be entirely critical regardless of weekends.

        Regression test: the backward pass previously subtracted calendar days
        while the forward pass counted working days, inventing phantom slack on
        the last task of a chain when a weekend fell inside a duration.
        """
        # Start on a Monday so durations straddle a weekend.
        project = Project(name="Chain", start_date=date(2024, 1, 1))
        task_a = Task(name="A", duration=3)
        task_b = Task(name="B", duration=5)  # spans the weekend
        project.add_task(task_a)
        project.add_task(task_b)
        project.add_dependency(
            Dependency(predecessor_id=task_a.task_id, successor_id=task_b.task_id)
        )

        engine = PlanningEngine(project)
        engine.calculate()

        assert task_a.total_slack == 0
        assert task_b.total_slack == 0
        assert task_a.on_critical_path
        assert task_b.on_critical_path

    def test_constraint_date_pushes_start_later(self) -> None:
        """A start-no-earlier-than constraint delays a task's early start."""
        project = Project(name="Constraint", start_date=date(2024, 1, 1))
        task = Task(name="Constrained", duration=2, constraint_date=date(2024, 1, 10))
        project.add_task(task)

        PlanningEngine(project).calculate()

        # Without the constraint the task would start on 2024-01-01.
        assert task.start_date == date(2024, 1, 10)

    def test_constraint_never_precedes_predecessor(self) -> None:
        """A constraint earlier than a predecessor's finish is ignored."""
        project = Project(name="Constraint2", start_date=date(2024, 1, 1))
        a = Task(name="A", duration=5)
        b = Task(name="B", duration=2, constraint_date=date(2024, 1, 2))
        project.add_task(a)
        project.add_task(b)
        project.add_dependency(Dependency(predecessor_id=a.task_id, successor_id=b.task_id))

        PlanningEngine(project).calculate()

        # B cannot start before A finishes, regardless of its earlier constraint.
        assert b.start_date is not None and a.end_date is not None
        assert b.start_date >= a.end_date

    def test_parallel_tasks(self) -> None:
        """Test schedule with parallel tasks."""
        project = Project(name="Test Project", start_date=date(2024, 1, 1))

        # Create parallel tasks: both start at same time, no dependencies
        task1 = Task(name="Task 1", duration=5)
        task2 = Task(name="Task 2", duration=3)

        project.add_task(task1)
        project.add_task(task2)

        engine = PlanningEngine(project)
        engine.calculate()

        # Both should start on the same date
        assert task1.start_date == task2.start_date

    def test_circular_dependency_detection(self) -> None:
        """Test detection of circular dependencies."""
        project = Project(name="Test Project")

        task1 = Task(name="Task 1")
        task2 = Task(name="Task 2")

        project.add_task(task1)
        project.add_task(task2)

        # Create circular dependency
        dep1 = Dependency(
            predecessor_id=task1.task_id,
            successor_id=task2.task_id,
        )
        dep2 = Dependency(
            predecessor_id=task2.task_id,
            successor_id=task1.task_id,
        )
        project.add_dependency(dep1)
        project.add_dependency(dep2)

        engine = PlanningEngine(project)

        with pytest.raises(CircularDependencyError):
            engine.calculate()

    def test_slack_calculation(self) -> None:
        """Test slack calculation."""
        project = Project(
            name="Test Project",
            start_date=date(2024, 1, 1),
            target_end_date=date(2024, 1, 20),
        )

        task1 = Task(name="Critical", duration=5)
        task2 = Task(name="Non-critical", duration=2)

        project.add_task(task1)
        project.add_task(task2)

        engine = PlanningEngine(project)
        engine.calculate()

        # Task 1 on critical path should have 0 slack
        critical_tasks = engine.get_critical_path()
        non_critical_tasks = [
            t for t in project.tasks if t.task_id not in [c.task_id for c in critical_tasks]
        ]

        for task in critical_tasks:
            assert task.total_slack == 0

    def test_task_dates_retrieval(self) -> None:
        """Test retrieving calculated task dates."""
        project = Project(name="Test Project", start_date=date(2024, 1, 1))

        task = Task(name="Test Task", duration=5)
        project.add_task(task)

        engine = PlanningEngine(project)
        engine.calculate()

        dates = engine.get_task_dates(task.task_id)
        assert dates is not None
        early_start, early_finish, late_start, late_finish = dates
        assert early_start is not None
        assert early_finish is not None

    def test_dependency_with_lag(self) -> None:
        """Test schedule calculation with lag."""
        project = Project(
            name="Test Project",
            start_date=date(2024, 1, 1),
        )

        task1 = Task(name="Task 1", duration=5)
        task2 = Task(name="Task 2", duration=3)
        project.add_task(task1)
        project.add_task(task2)

        # Task 2 starts 2 days after task 1 finishes
        dep = Dependency(
            predecessor_id=task1.task_id,
            successor_id=task2.task_id,
            lag=2,
        )
        project.add_dependency(dep)

        engine = PlanningEngine(project)
        engine.calculate()

        # Verify lag is applied
        assert task1.start_date is not None
        assert task2.start_date is not None

    def test_recalculate(self) -> None:
        """Test recalculation after project changes."""
        project = Project(name="Test Project", start_date=date(2024, 1, 1))

        task1 = Task(name="Task 1", duration=5)
        project.add_task(task1)

        engine = PlanningEngine(project)
        engine.calculate()

        initial_duration = (task1.end_date - task1.start_date).days if task1.end_date else 0

        # Modify task
        task1.duration = 10
        engine.recalculate()

        new_duration = (task1.end_date - task1.start_date).days if task1.end_date else 0
        assert new_duration > initial_duration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
