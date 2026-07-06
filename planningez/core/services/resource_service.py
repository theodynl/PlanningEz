"""Resource management and allocation service."""

import logging
from typing import List, Dict, Tuple
from datetime import date

from planningez.core.models.project import Project
from planningez.core.models.resource import Resource
from planningez.core.models.task import Task

logger = logging.getLogger(__name__)


class ResourceService:
    """Service for resource management and allocation."""

    def __init__(self, project: Project) -> None:
        """Initialize resource service.

        Args:
            project: Project instance
        """
        self.project = project

    def get_resource_workload(self, resource_id: str) -> Dict[date, float]:
        """Calculate workload for a resource by date.

        Args:
            resource_id: Resource ID

        Returns:
            Dictionary with dates as keys and workload (in hours/days) as values
        """
        workload: Dict[date, float] = {}
        resource = self.project.get_resource(resource_id)

        if not resource:
            return workload

        # Get all tasks assigned to this resource
        tasks = self.project.get_tasks_by_responsible(resource_id)

        for task in tasks:
            if task.start_date and task.end_date:
                # Calculate daily workload
                daily_workload = task.duration / max(
                    (task.end_date - task.start_date).days, 1
                )

                # Distribute workload across task duration
                current_date = task.start_date
                while current_date <= task.end_date:
                    if current_date not in workload:
                        workload[current_date] = 0
                    workload[current_date] += daily_workload
                    current_date = current_date + __import__("datetime").timedelta(days=1)

        return workload

    def get_overallocated_resources(
        self, max_allocation: float = 8.0
    ) -> List[Tuple[Resource, Dict[date, float]]]:
        """Get resources that are overallocated.

        Args:
            max_allocation: Maximum allocation per day (default: 8 hours)

        Returns:
            List of (resource, overload_days) tuples
        """
        overallocated = []

        for resource in self.project.resources:
            workload = self.get_resource_workload(resource.resource_id)
            overload = {date_: hours for date_, hours in workload.items() if hours > max_allocation}

            if overload:
                overallocated.append((resource, overload))
                logger.warning(
                    "Resource %s is overallocated on %d days",
                    resource.name,
                    len(overload),
                )

        return overallocated

    def get_resource_availability(self, resource_id: str) -> float:
        """Get resource availability percentage.

        Args:
            resource_id: Resource ID

        Returns:
            Availability percentage (0-100)
        """
        resource = self.project.get_resource(resource_id)
        if resource:
            return resource.availability
        return 0.0

    def set_resource_availability(self, resource_id: str, availability: float) -> bool:
        """Set resource availability.

        Args:
            resource_id: Resource ID
            availability: Availability percentage (0-100)

        Returns:
            True if successful
        """
        resource = self.project.get_resource(resource_id)
        if resource:
            resource.set_availability(availability)
            logger.info("Updated %s availability to %.1f%%", resource.name, availability)
            return True
        return False

    def get_total_project_cost(self) -> float:
        """Calculate total project cost.

        Returns:
            Total cost in currency units
        """
        total_cost = 0.0

        for task in self.project.tasks:
            if task.responsible:
                resource = self.project.get_resource(task.responsible)
                if resource:
                    # Cost = duration * daily_cost * (availability / 100)
                    task_cost = (
                        task.duration
                        * resource.daily_cost
                        * (resource.availability / 100.0)
                    )
                    total_cost += task_cost

        return total_cost

    def get_resource_cost(self, resource_id: str) -> float:
        """Calculate cost for a specific resource.

        Args:
            resource_id: Resource ID

        Returns:
            Resource cost
        """
        cost = 0.0
        resource = self.project.get_resource(resource_id)

        if not resource:
            return cost

        # Get all tasks assigned to this resource
        tasks = self.project.get_tasks_by_responsible(resource_id)

        for task in tasks:
            task_cost = (
                task.duration
                * resource.daily_cost
                * (resource.availability / 100.0)
            )
            cost += task_cost

        return cost

    def assign_resource_to_task(self, task_id: str, resource_id: str) -> bool:
        """Assign a resource to a task.

        Args:
            task_id: Task ID
            resource_id: Resource ID

        Returns:
            True if successful
        """
        task = self.project.get_task(task_id)
        resource = self.project.get_resource(resource_id)

        if task and resource:
            task.responsible = resource_id
            self.project.updated_at = __import__("datetime").datetime.now()
            logger.info("Assigned %s to task %s", resource.name, task.name)
            return True

        return False

    def unassign_resource_from_task(self, task_id: str) -> bool:
        """Unassign resource from a task.

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        task = self.project.get_task(task_id)
        if task:
            task.responsible = None
            self.project.updated_at = __import__("datetime").datetime.now()
            logger.info("Unassigned resource from task %s", task.name)
            return True
        return False

    def get_tasks_by_resource(self, resource_id: str) -> List[Task]:
        """Get all tasks assigned to a resource.

        Args:
            resource_id: Resource ID

        Returns:
            List of tasks
        """
        return self.project.get_tasks_by_responsible(resource_id)

    def get_resource_utilization(self, resource_id: str) -> float:
        """Calculate resource utilization percentage.

        Args:
            resource_id: Resource ID

        Returns:
            Utilization percentage (0-100)
        """
        resource = self.project.get_resource(resource_id)
        if not resource:
            return 0.0

        # Get tasks assigned to resource
        tasks = self.get_tasks_by_resource(resource_id)

        if not tasks:
            return 0.0

        # Calculate total workload
        total_hours = sum(task.duration * 8 for task in tasks)  # Assuming 8-hour days

        # Calculate available hours
        available_hours = 0
        for task in tasks:
            if task.start_date and task.end_date:
                days = (task.end_date - task.start_date).days + 1
                available_hours += days * 8 * (resource.availability / 100.0)

        if available_hours == 0:
            return 0.0

        return (total_hours / available_hours) * 100

    def level_resources(self) -> Dict[str, List[Tuple[date, float]]]:
        """Apply resource leveling to resolve overallocations.

        Returns:
            Dictionary of resource ID -> adjusted workload
        """
        # This is a simplified implementation
        # A full implementation would reschedule tasks to level resources
        result: Dict[str, List[Tuple[date, float]]] = {}

        for resource in self.project.resources:
            workload = self.get_resource_workload(resource.resource_id)
            result[resource.resource_id] = sorted(workload.items())

        logger.info("Resource leveling completed")
        return result
