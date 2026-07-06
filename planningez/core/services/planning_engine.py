"""Planning engine for critical path and schedule calculation."""

import logging
from typing import Dict, List, Tuple, Set, Optional
from datetime import date, timedelta
from collections import defaultdict, deque

from planningez.core.models.project import Project
from planningez.core.models.task import Task
from planningez.core.models.dependency import Dependency, DependencyType
from planningez.core.models.calendar import Calendar
from planningez.core.exceptions import CircularDependencyError, DependencyError

logger = logging.getLogger(__name__)


class PlanningEngine:
    """Core planning calculation engine."""

    def __init__(self, project: Project) -> None:
        """Initialize planning engine.

        Args:
            project: Project instance to calculate
        """
        self.project = project
        self.calendar = project.get_default_calendar()

        # Calculation caches
        self._early_start: Dict[str, date] = {}
        self._early_finish: Dict[str, date] = {}
        self._late_start: Dict[str, date] = {}
        self._late_finish: Dict[str, date] = {}
        self._total_slack: Dict[str, float] = {}
        self._free_slack: Dict[str, float] = {}
        self._critical_path: List[str] = []
        self._is_calculated = False

    def calculate(self) -> None:
        """Run complete schedule calculation."""
        try:
            self._detect_circular_dependencies()
            self._calculate_forward_pass()
            self._calculate_backward_pass()
            self._calculate_slack()
            self._identify_critical_path()
            self._update_project_dates()
            self._is_calculated = True
            logger.info("Schedule calculation completed successfully")
        except Exception as e:
            logger.error("Schedule calculation failed: %s", e)
            raise

    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies using DFS."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def visit(task_id: str) -> None:
            visited.add(task_id)
            rec_stack.add(task_id)

            _, outgoing = self.project.get_dependencies_for_task(task_id)
            for dep in outgoing:
                if dep.successor_id not in visited:
                    visit(dep.successor_id)
                elif dep.successor_id in rec_stack:
                    raise CircularDependencyError(
                        f"Circular dependency detected: {task_id} -> {dep.successor_id}"
                    )

            rec_stack.remove(task_id)

        for task in self.project.tasks:
            if task.task_id not in visited:
                visit(task.task_id)

    def _add_working_days(self, start: date, duration: float) -> date:
        """Return the finish date `duration` working days from `start` (inclusive).

        The start day itself counts as the first working day when it is a
        working day. This is the canonical duration convention used by both the
        forward and backward passes so that early/late dates stay symmetric.
        """
        working_days = 0.0
        current = start
        while working_days < duration:
            if self.calendar.is_working_day(current):
                working_days += 1
            if working_days < duration:
                current += timedelta(days=1)
        return current

    def _subtract_working_days(self, finish: date, duration: float) -> date:
        """Inverse of :meth:`_add_working_days`: the start for a given finish.

        Steps backward from ``finish`` counting working days so that
        ``_add_working_days(start, duration) == finish``.
        """
        working_days = 0.0
        current = finish
        while working_days < duration:
            if self.calendar.is_working_day(current):
                working_days += 1
            if working_days < duration:
                current -= timedelta(days=1)
        return current

    def _calculate_forward_pass(self) -> None:
        """Calculate early start and early finish dates (forward pass)."""
        self._early_start.clear()
        self._early_finish.clear()

        # Initialize with project start date or today
        project_start = self.project.start_date or date.today()

        # Topological sort
        in_degree = defaultdict(int)
        for task in self.project.tasks:
            in_degree[task.task_id] = 0

        for dep in self.project.dependencies:
            in_degree[dep.successor_id] += 1

        # Queue of tasks ready to process
        queue = deque([task.task_id for task in self.project.tasks if in_degree[task.task_id] == 0])

        while queue:
            task_id = queue.popleft()
            task = self.project.get_task(task_id)
            if not task:
                continue

            # Calculate start date
            incoming, _ = self.project.get_dependencies_for_task(task_id)
            if not incoming:
                self._early_start[task_id] = task.start_date or project_start
            else:
                max_finish = project_start
                for dep in incoming:
                    pred_finish = self._early_finish.get(dep.predecessor_id, project_start)
                    adjusted_finish = pred_finish + timedelta(days=dep.lag)
                    max_finish = max(max_finish, adjusted_finish)
                self._early_start[task_id] = max_finish

            # Calculate finish date (skip if it's a milestone with no duration)
            if task.duration > 0:
                self._early_finish[task_id] = self._add_working_days(
                    self._early_start[task_id], task.duration
                )
            else:
                self._early_finish[task_id] = self._early_start[task_id]

            # Process successors
            _, outgoing = self.project.get_dependencies_for_task(task_id)
            for dep in outgoing:
                in_degree[dep.successor_id] -= 1
                if in_degree[dep.successor_id] == 0:
                    queue.append(dep.successor_id)

    def _calculate_backward_pass(self) -> None:
        """Calculate late start and late finish dates (backward pass)."""
        self._late_start.clear()
        self._late_finish.clear()

        # Initialize with project end date or max early finish
        if self.project.target_end_date:
            project_end = self.project.target_end_date
        else:
            project_end = max(self._early_finish.values()) if self._early_finish else date.today()

        # Reverse topological sort
        in_degree = defaultdict(int)
        for task in self.project.tasks:
            in_degree[task.task_id] = 0

        for dep in self.project.dependencies:
            in_degree[dep.predecessor_id] += 1

        # Queue of tasks ready to process (end tasks first)
        queue = deque(
            [task.task_id for task in self.project.tasks if in_degree[task.task_id] == 0]
        )

        while queue:
            task_id = queue.popleft()

            # Calculate late finish
            _, outgoing = self.project.get_dependencies_for_task(task_id)
            if not outgoing:
                self._late_finish[task_id] = project_end
            else:
                min_start = project_end
                for dep in outgoing:
                    succ_start = self._late_start.get(dep.successor_id, project_end)
                    adjusted_start = succ_start - timedelta(days=dep.lag)
                    min_start = min(min_start, adjusted_start)
                self._late_finish[task_id] = min_start

            # Calculate late start (working-day aware, symmetric with forward pass)
            task = self.project.get_task(task_id)
            if task and task.duration > 0:
                self._late_start[task_id] = self._subtract_working_days(
                    self._late_finish[task_id], task.duration
                )
            else:
                self._late_start[task_id] = self._late_finish[task_id]

            # Process predecessors
            incoming, _ = self.project.get_dependencies_for_task(task_id)
            for dep in incoming:
                in_degree[dep.predecessor_id] -= 1
                if in_degree[dep.predecessor_id] == 0:
                    queue.append(dep.predecessor_id)

    def _calculate_slack(self) -> None:
        """Calculate total and free slack for each task."""
        self._total_slack.clear()
        self._free_slack.clear()

        for task_id in self._early_start:
            # Total slack = Late Start - Early Start
            total_slack_days = (
                self._late_start.get(task_id, date.today())
                - self._early_start.get(task_id, date.today())
            ).days
            self._total_slack[task_id] = max(0, total_slack_days)

            # Free slack = min(successor early start) - early finish
            _, outgoing = self.project.get_dependencies_for_task(task_id)
            if outgoing:
                min_succ_start = min(
                    self._early_start.get(dep.successor_id, date.today())
                    for dep in outgoing
                )
                free_slack_days = (
                    min_succ_start - self._early_finish.get(task_id, date.today())
                ).days
                self._free_slack[task_id] = max(0, free_slack_days)
            else:
                self._free_slack[task_id] = self._total_slack[task_id]

    def _identify_critical_path(self) -> None:
        """Identify tasks on the critical path (slack = 0)."""
        self._critical_path = [
            task_id for task_id, slack in self._total_slack.items() if slack == 0
        ]

    def _update_project_dates(self) -> None:
        """Update project and task with calculated dates."""
        # Update project dates
        if self._early_start:
            self.project.start_date = min(self._early_start.values())
        if self._early_finish:
            self.project.total_duration = (
                max(self._early_finish.values()) - self.project.start_date
            ).days if self.project.start_date else 0

        self.project.critical_path_tasks = self._critical_path

        # Update task fields
        for task in self.project.tasks:
            task_id = task.task_id
            if task_id in self._early_start:
                task.start_date = self._early_start[task_id]
            if task_id in self._early_finish:
                task.end_date = self._early_finish[task_id]
            if task_id in self._total_slack:
                task.total_slack = self._total_slack[task_id]
            if task_id in self._free_slack:
                task.free_slack = self._free_slack[task_id]
            if task_id in self._critical_path:
                task.on_critical_path = True

    def get_critical_path(self) -> List[Task]:
        """Get tasks on the critical path."""
        if not self._is_calculated:
            self.calculate()
        return [
            task for task in self.project.tasks
            if task.task_id in self._critical_path
        ]

    def get_task_dates(self, task_id: str) -> Optional[Tuple[date, date, date, date]]:
        """Get calculated dates for a task.

        Returns:
            Tuple of (early_start, early_finish, late_start, late_finish) or None
        """
        if not self._is_calculated:
            self.calculate()

        if task_id in self._early_start:
            return (
                self._early_start[task_id],
                self._early_finish[task_id],
                self._late_start.get(task_id),
                self._late_finish.get(task_id),
            )
        return None

    def recalculate(self) -> None:
        """Force recalculation of the schedule."""
        self._is_calculated = False
        self.calculate()
