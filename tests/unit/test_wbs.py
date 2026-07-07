"""Tests for the WBS model and importer."""

import pytest

from planningez.core.models.wbs import WBS, WBSNode
from planningez.core.models.project import Project
from planningez.import_.wbs_importer import WBSImporter, ColumnMapping


SAMPLE_TREE = {
    "Projet": {
        "Engineering": {
            "Process": {},
            "Mechanical": {},
            "Electrical": {},
            "Automation": {},
        },
        "Procurement": {
            "Long Lead Items": {},
            "Equipment": {},
        },
        "Manufacturing": {},
        "Installation": {},
        "Commissioning": {},
    }
}


def test_wbs_from_nested_dict_builds_hierarchy():
    wbs = WBS.from_dict(SAMPLE_TREE)
    assert len(wbs.roots) == 1
    root = wbs.roots[0]
    assert root.name == "Projet"
    assert root.code == "1"
    # Projet + 5 children + (4 eng + 2 proc) grandchildren = 12 nodes
    assert len(wbs.flatten()) == 12


def test_wbs_auto_numbering():
    wbs = WBS.from_dict(SAMPLE_TREE)
    eng = wbs.find_by_code("1.1")
    assert eng is not None
    assert eng.name == "Engineering"
    automation = wbs.find_by_code("1.1.4")
    assert automation is not None
    assert automation.name == "Automation"
    assert automation.level == 3


def test_wbs_max_depth():
    wbs = WBS.from_dict(SAMPLE_TREE)
    assert wbs.max_depth() == 3


def test_wbs_leaf_detection():
    wbs = WBS.from_dict(SAMPLE_TREE)
    process = wbs.find_by_code("1.1.1")
    assert process.is_leaf()
    root = wbs.roots[0]
    assert not root.is_leaf()


def test_importer_from_json_nested():
    importer = WBSImporter()
    import json

    wbs = importer.from_json(json.dumps(SAMPLE_TREE))
    assert len(wbs.flatten()) == 12


def test_importer_from_json_flat_rows():
    importer = WBSImporter()
    rows = [
        {"code": "1", "name": "Project"},
        {"code": "1.1", "name": "Engineering"},
        {"code": "1.2", "name": "Procurement"},
        {"code": "1.1.1", "name": "Process"},
    ]
    import json

    wbs = importer.from_json(json.dumps(rows))
    assert wbs.find_by_code("1.1.1").name == "Process"
    assert len(wbs.flatten()) == 4


def test_importer_from_csv_with_codes():
    importer = WBSImporter()
    csv_text = "code,name\n1,Project\n1.1,Engineering\n1.1.1,Process\n"
    wbs = importer.from_csv(csv_text)
    assert len(wbs.flatten()) == 3
    assert wbs.find_by_code("1.1.1").name == "Process"


def test_importer_from_csv_with_levels():
    importer = WBSImporter()
    csv_text = "level,name\n1,Project\n2,Engineering\n3,Process\n2,Procurement\n"
    mapping = ColumnMapping(name="name", code=None, level="level")
    wbs = importer.from_csv(csv_text, mapping)
    root = wbs.roots[0]
    assert root.name == "Project"
    # Engineering has one child (Process); Procurement is a sibling of Engineering
    engineering = root.children[0]
    assert engineering.name == "Engineering"
    assert engineering.children[0].name == "Process"


def test_importer_from_xml():
    importer = WBSImporter()
    xml = (
        '<wbs name="Root">'
        '<node name="Project">'
        '<node name="Engineering"><node name="Process"/></node>'
        "</node></wbs>"
    )
    wbs = importer.from_xml(xml)
    assert len(wbs.flatten()) == 3
    assert wbs.max_depth() == 3


def test_create_tasks_from_wbs():
    importer = WBSImporter()
    wbs = WBS.from_dict(SAMPLE_TREE)
    project = Project(name="Test")
    mapping = importer.create_tasks(wbs, project)
    assert len(project.tasks) == len(wbs.flatten())
    # Every node now references a task.
    for node in wbs.flatten():
        assert node.task_id is not None
        assert node.node_id in mapping


def test_invalid_json_raises():
    from planningez.core.exceptions import ImportError as PlanningImportError

    importer = WBSImporter()
    with pytest.raises(PlanningImportError):
        importer.from_json("{not valid json")
