"""Tests for the project initializer start modes."""

import json

import pytest

from planningez.core.models.work_package import WorkPackage, Discipline
from planningez.core.models.task import Task
from planningez.core.services.project_initializer import ProjectInitializer, StartMode
from planningez.core.exceptions import ImportError as PlanningImportError


WBS_TREE = {"Projet": {"Engineering": {"Process": {}}, "Procurement": {}}}


@pytest.fixture
def initializer():
    return ProjectInitializer()


def test_create_empty(initializer):
    project = initializer.create_empty("Blank")
    assert project.name == "Blank"
    assert project.tasks == []
    # A default calendar is always present.
    assert len(project.calendars) == 1


def test_from_wbs_json_creates_tasks(initializer):
    project = initializer.from_wbs_json(json.dumps(WBS_TREE), name="WBS Project")
    # Projet + Engineering + Process + Procurement = 4 nodes -> 4 tasks
    assert len(project.tasks) == 4


def test_from_work_packages(initializer):
    wp = WorkPackage(name="BE", code="BE", discipline=Discipline.ENGINEERING)
    wp.add_task(Task(name="Design", duration=5))
    project = initializer.from_work_packages([wp], name="From WP")
    assert project.name == "From WP"
    assert any(t.name == "Design" for t in project.tasks)


def test_from_work_packages_empty_raises(initializer):
    with pytest.raises(PlanningImportError):
        initializer.from_work_packages([], name="Empty")


def test_from_json_round_trip(initializer):
    original = initializer.create_empty("Original")
    original.add_task(Task(name="A", duration=3))
    from planningez.utils.serialization import to_json

    project = initializer.from_json(to_json(original))
    assert project.name == "Original"
    assert len(project.tasks) == 1


def test_from_template(initializer):
    template = {"name": "Template Base", "tasks": [{"name": "Setup", "duration": 2}]}
    project = initializer.from_template(template, name="My Project")
    assert project.name == "My Project"  # explicit name overrides template
    assert len(project.tasks) == 1


def test_dispatch_create_empty(initializer):
    project = initializer.create(StartMode.EMPTY, name="Dispatched")
    assert project.name == "Dispatched"


def test_dispatch_wbs(initializer):
    project = initializer.create(StartMode.WBS, source=json.dumps(WBS_TREE), name="D")
    assert len(project.tasks) == 4


def test_dispatch_work_package(initializer):
    wp = WorkPackage(name="BE", code="BE")
    wp.add_task(Task(name="Design", duration=5))
    project = initializer.create(StartMode.WORK_PACKAGE, packages=[wp], name="D")
    assert any(t.name == "Design" for t in project.tasks)


def test_ms_project_import(initializer, tmp_path):
    xml = """<?xml version="1.0"?>
<Project xmlns="http://schemas.microsoft.com/project">
  <Name>MSP Sample</Name>
  <Tasks>
    <Task><UID>1</UID><Name>Task One</Name><Duration>PT16H0M0S</Duration>
      <Milestone>0</Milestone><PercentComplete>25</PercentComplete></Task>
    <Task><UID>2</UID><Name>Task Two</Name><Duration>PT8H0M0S</Duration>
      <Milestone>0</Milestone><PercentComplete>0</PercentComplete>
      <PredecessorLink><PredecessorUID>1</PredecessorUID><Type>1</Type>
        <LinkLag>0</LinkLag></PredecessorLink></Task>
  </Tasks>
</Project>"""
    path = tmp_path / "sample.xml"
    path.write_text(xml)
    project = initializer.from_ms_project(path)
    assert project.name == "MSP Sample"
    assert len(project.tasks) == 2
    assert len(project.dependencies) == 1
    # 16 hours / 8 hours-per-day = 2 days.
    assert project.tasks[0].duration == 2.0


def test_primavera_import(initializer, tmp_path):
    xml = """<?xml version="1.0"?>
<APIBusinessObjects>
  <Project>
    <Name>P6 Sample</Name>
    <Activity><ObjectId>1</ObjectId><Name>Act One</Name>
      <Type>Task Dependent</Type><PlannedDuration>16</PlannedDuration>
      <PercentComplete>0</PercentComplete></Activity>
    <Activity><ObjectId>2</ObjectId><Name>Act Two</Name>
      <Type>Task Dependent</Type><PlannedDuration>8</PlannedDuration>
      <PercentComplete>0</PercentComplete></Activity>
    <Relationship><PredecessorActivityObjectId>1</PredecessorActivityObjectId>
      <SuccessorActivityObjectId>2</SuccessorActivityObjectId>
      <Type>Finish to Start</Type><Lag>0</Lag></Relationship>
  </Project>
</APIBusinessObjects>"""
    path = tmp_path / "sample_p6.xml"
    path.write_text(xml)
    project = initializer.from_primavera(path)
    assert project.name == "P6 Sample"
    assert len(project.tasks) == 2
    assert len(project.dependencies) == 1
    assert project.tasks[0].duration == 2.0  # 16h / 8h-per-day
