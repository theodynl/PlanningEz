"""Tests for intelligent planning generation from Work Packages."""

import pytest

from planningez.core.models.work_package import WorkPackage, Discipline, Milestone
from planningez.core.models.task import Task, TaskType
from planningez.core.models.dependency import Dependency
from planningez.core.services.planning_generator import (
    PlanningGenerator,
    GenerationRules,
    ConnectMode,
)


def _make_package(name, code, task_names):
    wp = WorkPackage(name=name, code=code, discipline=Discipline.ENGINEERING)
    tasks = [Task(name=n, duration=2) for n in task_names]
    for t in tasks:
        wp.add_task(t)
    # Chain tasks internally.
    for a, b in zip(tasks, tasks[1:]):
        wp.add_dependency(Dependency(predecessor_id=a.task_id, successor_id=b.task_id))
    return wp, tasks


def test_generate_creates_summary_tasks():
    wp_a, _ = _make_package("Basic Engineering", "BE", ["Design", "Review"])
    wp_b, _ = _make_package("FAT", "FAT", ["Prepare", "Execute"])
    gen = PlanningGenerator()
    project = gen.generate([wp_a, wp_b], project_name="Plant")
    summaries = [t for t in project.tasks if t.task_type == TaskType.SUMMARY]
    assert len(summaries) == 2
    assert {s.name for s in summaries} == {"Basic Engineering", "FAT"}


def test_generate_preserves_internal_dependencies():
    wp_a, _ = _make_package("BE", "BE", ["A", "B", "C"])
    gen = PlanningGenerator(GenerationRules(create_summary_tasks=False))
    project = gen.generate([wp_a])
    # Two internal dependencies preserved (A->B, B->C).
    assert len(project.dependencies) == 2


def test_generate_sequential_connects_packages():
    wp_a, _ = _make_package("BE", "BE", ["A1", "A2"])
    wp_b, _ = _make_package("FAT", "FAT", ["B1", "B2"])
    gen = PlanningGenerator(GenerationRules(connect_mode=ConnectMode.SEQUENTIAL))
    project = gen.generate([wp_a, wp_b])
    # Internal: 1 per package = 2. Cross-link: exit(A2) -> entry(B1) = 1. Total 3.
    assert len(project.dependencies) == 3


def test_generate_parallel_no_cross_links():
    wp_a, _ = _make_package("BE", "BE", ["A1", "A2"])
    wp_b, _ = _make_package("FAT", "FAT", ["B1", "B2"])
    gen = PlanningGenerator(GenerationRules(connect_mode=ConnectMode.PARALLEL))
    project = gen.generate([wp_a, wp_b])
    # Only internal dependencies, no cross-package links.
    assert len(project.dependencies) == 2


def test_generate_custom_links():
    wp_a, _ = _make_package("BE", "BE", ["A1"])
    wp_b, _ = _make_package("FAT", "FAT", ["B1"])
    rules = GenerationRules(
        connect_mode=ConnectMode.CUSTOM,
        custom_links=[("BE", "FAT")],
    )
    gen = PlanningGenerator(rules)
    project = gen.generate([wp_a, wp_b])
    assert len(project.dependencies) == 1


def test_generate_inserts_milestones():
    wp = WorkPackage(name="BE", code="BE", discipline=Discipline.ENGINEERING)
    wp.add_task(Task(name="Design", duration=5))
    wp.add_milestone(Milestone(name="BE Complete"))
    gen = PlanningGenerator()
    project = gen.generate([wp])
    milestones = [t for t in project.tasks if t.task_type == TaskType.MILESTONE]
    assert len(milestones) == 1
    assert milestones[0].name == "BE Complete"


def test_generate_carries_default_resources():
    from planningez.core.models.resource import Resource

    wp = WorkPackage(name="BE", code="BE", discipline=Discipline.ENGINEERING)
    wp.add_task(Task(name="Design", duration=5))
    wp.default_resources.append(Resource(name="Lead Engineer"))
    gen = PlanningGenerator()
    project = gen.generate([wp])
    assert any(r.name == "Lead Engineer" for r in project.resources)


def test_generate_fresh_task_ids():
    wp_a, tasks_a = _make_package("BE", "BE", ["A"])
    gen = PlanningGenerator(GenerationRules(create_summary_tasks=False))
    project = gen.generate([wp_a])
    # The cloned task should have a different id than the source task.
    assert project.tasks[0].task_id != tasks_a[0].task_id
    assert project.tasks[0].name == "A"
