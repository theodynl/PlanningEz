"""Unit tests for resource service."""

import pytest
from datetime import date
from planningez.core.models import Project, Task, Resource, ResourceRole
from planningez.core.services import ResourceService


class TestResourceService:
    """Test ResourceService functionality."""

    @pytest.fixture
    def project(self) -> Project:
        """Create a test project."""
        return Project(name="Test Project", start_date=date(2024, 1, 1))

    @pytest.fixture
    def resource(self) -> Resource:
        """Create a test resource."""
        return Resource(
            name="John Doe",
            role=ResourceRole.ENGINEER,
            daily_cost=200.0,
            availability=100.0,
        )

    @pytest.fixture
    def service(self, project: Project) -> ResourceService:
        """Create a resource service."""
        return ResourceService(project)

    def test_get_resource_workload(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test calculating resource workload."""
        project.add_resource(resource)

        task = Task(
            name="Task",
            duration=8,
            responsible=resource.resource_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 8),
        )
        project.add_task(task)

        workload = service.get_resource_workload(resource.resource_id)
        assert len(workload) > 0

    def test_get_overallocated_resources(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test identifying overallocated resources."""
        project.add_resource(resource)

        # Create overallocated tasks
        task1 = Task(
            name="Task 1",
            duration=8,
            responsible=resource.resource_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )
        task2 = Task(
            name="Task 2",
            duration=8,
            responsible=resource.resource_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )
        project.add_task(task1)
        project.add_task(task2)

        overallocated = service.get_overallocated_resources(max_allocation=10)
        assert len(overallocated) > 0

    def test_get_resource_availability(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test getting resource availability."""
        project.add_resource(resource)

        availability = service.get_resource_availability(resource.resource_id)
        assert availability == 100.0

    def test_set_resource_availability(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test setting resource availability."""
        project.add_resource(resource)

        success = service.set_resource_availability(resource.resource_id, 50.0)
        assert success
        assert resource.availability == 50.0

    def test_get_total_project_cost(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test calculating total project cost."""
        project.add_resource(resource)

        task = Task(
            name="Task",
            duration=5,
            responsible=resource.resource_id,
        )
        project.add_task(task)

        total_cost = service.get_total_project_cost()
        expected_cost = 5 * 200.0 * (100.0 / 100.0)
        assert total_cost == expected_cost

    def test_get_resource_cost(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test calculating resource cost."""
        project.add_resource(resource)

        task = Task(
            name="Task",
            duration=5,
            responsible=resource.resource_id,
        )
        project.add_task(task)

        cost = service.get_resource_cost(resource.resource_id)
        expected_cost = 5 * 200.0 * (100.0 / 100.0)
        assert cost == expected_cost

    def test_assign_resource_to_task(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test assigning resource to task."""
        project.add_resource(resource)

        task = Task(name="Task")
        project.add_task(task)

        success = service.assign_resource_to_task(task.task_id, resource.resource_id)
        assert success
        assert task.responsible == resource.resource_id

    def test_unassign_resource_from_task(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test unassigning resource from task."""
        project.add_resource(resource)

        task = Task(name="Task", responsible=resource.resource_id)
        project.add_task(task)

        success = service.unassign_resource_from_task(task.task_id)
        assert success
        assert task.responsible is None

    def test_get_tasks_by_resource(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test getting tasks by resource."""
        project.add_resource(resource)

        task1 = Task(name="Task 1", responsible=resource.resource_id)
        task2 = Task(name="Task 2", responsible=resource.resource_id)
        task3 = Task(name="Task 3")

        project.add_task(task1)
        project.add_task(task2)
        project.add_task(task3)

        tasks = service.get_tasks_by_resource(resource.resource_id)
        assert len(tasks) == 2

    def test_get_resource_utilization(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test calculating resource utilization."""
        project.add_resource(resource)

        task = Task(
            name="Task",
            duration=4,
            responsible=resource.resource_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 4),
        )
        project.add_task(task)

        utilization = service.get_resource_utilization(resource.resource_id)
        assert 0 <= utilization <= 100

    def test_level_resources(
        self, service: ResourceService, resource: Resource, project: Project
    ) -> None:
        """Test resource leveling."""
        project.add_resource(resource)

        task = Task(name="Task", duration=5, responsible=resource.resource_id)
        project.add_task(task)

        result = service.level_resources()
        assert resource.resource_id in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
