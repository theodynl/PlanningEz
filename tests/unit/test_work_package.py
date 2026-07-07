"""Tests for the Work Package model and library service."""

import pytest

from planningez.core.models.work_package import (
    WorkPackage,
    Discipline,
    Milestone,
    Deliverable,
    Risk,
)
from planningez.core.models.task import Task, TaskType
from planningez.core.models.dependency import Dependency
from planningez.core.services.work_package_library import WorkPackageLibrary


@pytest.fixture
def sample_package():
    wp = WorkPackage(
        name="Basic Engineering",
        code="BE-001",
        discipline=Discipline.ENGINEERING,
    )
    kickoff = Task(name="Kickoff", duration=1)
    design = Task(name="Design", duration=10)
    review = Task(name="Review", duration=2)
    wp.add_task(kickoff)
    wp.add_task(design)
    wp.add_task(review)
    wp.add_dependency(Dependency(predecessor_id=kickoff.task_id, successor_id=design.task_id))
    wp.add_dependency(Dependency(predecessor_id=design.task_id, successor_id=review.task_id))
    wp.add_milestone(Milestone(name="BE Complete", offset_days=13))
    wp.deliverables.append(Deliverable(name="PFD"))
    wp.risks.append(Risk(name="Scope creep", probability=0.4, impact=0.6))
    wp.assumptions.append("Client provides P&IDs")
    wp.suppliers.append("Vendor A")
    return wp


def test_work_package_estimated_duration(sample_package):
    total = sample_package.compute_estimated_duration()
    assert total == 13  # 1 + 10 + 2


def test_work_package_version_bump(sample_package):
    assert sample_package.version == "1.0.0"
    assert sample_package.bump_version("minor") == "1.1.0"
    assert sample_package.bump_version("major") == "2.0.0"
    assert sample_package.bump_version("patch") == "2.0.1"


def test_risk_severity(sample_package):
    risk = sample_package.risks[0]
    assert risk.severity == pytest.approx(0.24)


def test_library_add_and_get(sample_package):
    lib = WorkPackageLibrary()
    lib.add(sample_package)
    assert len(lib) == 1
    assert lib.get(sample_package.work_package_id) is sample_package
    assert lib.get_by_code("BE-001") is sample_package


def test_library_list(sample_package):
    lib = WorkPackageLibrary()
    lib.add(sample_package)
    listing = lib.list()
    assert listing[0]["name"] == "Basic Engineering"
    assert listing[0]["tasks"] == "3"


def test_library_filter_by_discipline(sample_package):
    lib = WorkPackageLibrary()
    lib.add(sample_package)
    assert len(lib.filter_by_discipline("engineering")) == 1
    assert len(lib.filter_by_discipline("mechanical")) == 0


def test_library_json_round_trip(sample_package):
    lib = WorkPackageLibrary()
    lib.add(sample_package)
    text = lib.export_to_json(sample_package.work_package_id)

    reloaded = lib.import_from_json(text, register=False)
    assert reloaded.name == sample_package.name
    assert reloaded.code == sample_package.code
    assert reloaded.discipline == Discipline.ENGINEERING
    assert len(reloaded.tasks) == 3
    assert len(reloaded.dependencies) == 2
    assert len(reloaded.milestones) == 1
    assert len(reloaded.deliverables) == 1
    assert len(reloaded.risks) == 1
    assert reloaded.assumptions == ["Client provides P&IDs"]
    assert reloaded.suppliers == ["Vendor A"]


def test_library_disk_persistence(tmp_path, sample_package):
    lib = WorkPackageLibrary(storage_dir=tmp_path)
    lib.add(sample_package)
    # A fresh library pointed at the same dir loads the package back.
    lib2 = WorkPackageLibrary(storage_dir=tmp_path)
    assert len(lib2) == 1
    loaded = lib2.get(sample_package.work_package_id)
    assert loaded is not None
    assert loaded.name == "Basic Engineering"


def test_library_versioning_archives(tmp_path, sample_package):
    lib = WorkPackageLibrary(storage_dir=tmp_path)
    lib.add(sample_package)
    lib.save_version(sample_package, "minor")
    assert sample_package.version == "1.1.0"
    archives = list((tmp_path / "versions").glob("*.json"))
    assert len(archives) == 1


def test_library_remove(sample_package):
    lib = WorkPackageLibrary()
    lib.add(sample_package)
    lib.remove(sample_package.work_package_id)
    assert len(lib) == 0


def test_import_invalid_json_raises():
    from planningez.core.exceptions import ImportError as PlanningImportError

    lib = WorkPackageLibrary()
    with pytest.raises(PlanningImportError):
        lib.import_from_json("{bad json")
