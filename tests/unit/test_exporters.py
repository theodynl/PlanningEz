"""Tests for the export abstraction layer and format exporters."""

import json

import pytest

from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType
from planningez.core.models.resource import Resource
from planningez.core.models.dependency import Dependency, DependencyType
from planningez.core.models.builders import build_project
from planningez import export
from planningez.export.base_exporter import (
    BaseExporter,
    register_exporter,
    get_exporter,
    available_formats,
)
from planningez.import_.msproject_importer import MSProjectImporter
from planningez.import_.primavera_importer import PrimaveraImporter
from planningez.core.exceptions import ExportError


@pytest.fixture
def sample_project():
    project = Project(name="Sample Plant")
    a = Task(name="Design", duration=5, progress=50)
    b = Task(name="Build", duration=10)
    ms = Task(name="Done", task_type=TaskType.MILESTONE, is_milestone=True, duration=0)
    project.add_task(a)
    project.add_task(b)
    project.add_task(ms)
    project.add_dependency(
        Dependency(predecessor_id=a.task_id, successor_id=b.task_id,
                   dependency_type=DependencyType.FINISH_TO_START)
    )
    engineer = Resource(name="Engineer", daily_cost=800)
    project.add_resource(engineer)
    a.responsible = engineer.resource_id
    return project


def test_registry_lists_builtin_formats():
    formats = available_formats()
    assert "json" in formats
    assert "msproject" in formats
    assert "primavera" in formats


def test_get_unknown_exporter_raises():
    with pytest.raises(ExportError):
        get_exporter("does-not-exist")


def test_json_export_round_trip(sample_project):
    text = get_exporter("json").export(sample_project)
    data = json.loads(text)
    restored = build_project(data)
    assert restored.name == "Sample Plant"
    assert len(restored.tasks) == 3
    assert len(restored.dependencies) == 1
    assert len(restored.resources) == 1


def test_msproject_export_is_valid_xml(sample_project):
    from xml.etree import ElementTree as ET

    text = get_exporter("msproject").export(sample_project)
    root = ET.fromstring(text)
    assert root.tag.endswith("Project")


def test_msproject_round_trip_task_count(sample_project):
    text = get_exporter("msproject").export(sample_project)
    reimported = MSProjectImporter().from_xml(text)
    assert len(reimported.tasks) == 3
    assert len(reimported.dependencies) == 1


def test_msproject_preserves_milestone(sample_project):
    text = get_exporter("msproject").export(sample_project)
    reimported = MSProjectImporter().from_xml(text)
    milestones = [t for t in reimported.tasks if t.is_milestone]
    assert len(milestones) == 1


def test_primavera_export_is_valid_xml(sample_project):
    from xml.etree import ElementTree as ET

    text = get_exporter("primavera").export(sample_project)
    root = ET.fromstring(text)
    assert root.tag.endswith("APIBusinessObjects")


def test_primavera_round_trip(sample_project):
    text = get_exporter("primavera").export(sample_project)
    reimported = PrimaveraImporter().from_xml(text)
    # 3 activities (no summary tasks in this project), 1 relationship.
    assert len(reimported.tasks) == 3
    assert len(reimported.dependencies) == 1


def test_export_to_file(tmp_path, sample_project):
    path = tmp_path / "out.json"
    export.export_project(sample_project, "json", path)
    assert path.exists()
    assert json.loads(path.read_text())["name"] == "Sample Plant"


def test_custom_exporter_registration(sample_project):
    @register_exporter
    class DummyExporter(BaseExporter):
        format_key = "dummy-test"
        file_extension = "txt"

        def export(self, project):
            return f"PROJECT:{project.name}"

    assert "dummy-test" in available_formats()
    assert get_exporter("dummy-test").export(sample_project) == "PROJECT:Sample Plant"


def test_exporter_without_format_key_raises():
    with pytest.raises(ExportError):

        @register_exporter
        class BadExporter(BaseExporter):
            def export(self, project):
                return ""
