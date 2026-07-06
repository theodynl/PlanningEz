"""Tests for the PlanningEz FastAPI backend."""

import pytest
from fastapi.testclient import TestClient

from planningez.api.app import app


WBS_JSON = '{"Projet": {"Engineering": {"Process": {}, "Mechanical": {}}, "Procurement": {}}}'


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_meta_lists_formats_and_enums(client):
    data = client.get("/api/meta").json()
    assert "json" in data["export_formats"]
    assert "msproject" in data["export_formats"]
    assert "primavera" in data["export_formats"]
    assert "engineering" in data["disciplines"]
    assert set(data["connect_modes"]) >= {"sequential", "parallel", "custom"}


def test_library_is_seeded(client):
    packages = client.get("/api/work-packages").json()
    codes = {p["code"] for p in packages}
    assert {"BE-001", "FAT-001", "SAT-001"} <= codes


def test_create_empty_project(client):
    resp = client.post("/api/projects", json={"mode": "empty", "name": "Blank"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Blank"
    assert body["tasks"] == []


def test_create_project_from_wbs(client):
    resp = client.post(
        "/api/projects",
        json={"mode": "wbs", "name": "Plant", "wbs_content": WBS_JSON},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Projet + Engineering + Process + Mechanical + Procurement = 5 nodes
    assert len(body["tasks"]) == 5


def test_wbs_preview(client):
    resp = client.post("/api/wbs/preview", json={"format": "json", "content": WBS_JSON})
    assert resp.status_code == 200
    body = resp.json()
    assert body["node_count"] == 5
    assert body["depth"] == 3


def test_wbs_preview_invalid_json(client):
    resp = client.post("/api/wbs/preview", json={"format": "json", "content": "{bad"})
    assert resp.status_code == 400


def test_generate_from_work_packages(client):
    packages = client.get("/api/work-packages").json()
    ids = [p["work_package_id"] for p in packages[:3]]
    resp = client.post(
        "/api/projects/generate",
        json={"name": "Assembled", "work_package_ids": ids, "connect_mode": "sequential"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["tasks"]) > 0
    assert len(body["dependencies"]) > 0


def test_generate_requires_packages(client):
    resp = client.post("/api/projects/generate", json={"name": "X", "work_package_ids": []})
    assert resp.status_code == 400


def test_schedule_marks_critical_path(client):
    packages = client.get("/api/work-packages").json()
    ids = [p["work_package_id"] for p in packages[:2]]
    project = client.post(
        "/api/projects/generate",
        json={"name": "Sched", "work_package_ids": ids, "connect_mode": "sequential"},
    ).json()
    scheduled = client.get(f"/api/projects/{project['project_id']}/schedule").json()
    critical = [t for t in scheduled["tasks"] if t["on_critical_path"]]
    assert len(critical) > 0


def test_task_crud_flow(client):
    project = client.post("/api/projects", json={"mode": "empty", "name": "CRUD"}).json()
    pid = project["project_id"]

    task = client.post(
        f"/api/projects/{pid}/tasks", json={"name": "Task 1", "duration": 4}
    ).json()
    tid = task["task_id"]

    updated = client.patch(
        f"/api/projects/{pid}/tasks/{tid}", json={"progress": 50, "name": "Task 1b"}
    ).json()
    assert updated["progress"] == 50
    assert updated["name"] == "Task 1b"

    deleted = client.delete(f"/api/projects/{pid}/tasks/{tid}")
    assert deleted.status_code == 200
    full = client.get(f"/api/projects/{pid}").json()
    assert full["tasks"] == []


def test_dependency_creation_and_cycle_detection(client):
    project = client.post("/api/projects", json={"mode": "empty", "name": "Deps"}).json()
    pid = project["project_id"]
    a = client.post(f"/api/projects/{pid}/tasks", json={"name": "A", "duration": 2}).json()
    b = client.post(f"/api/projects/{pid}/tasks", json={"name": "B", "duration": 2}).json()

    dep = client.post(
        f"/api/projects/{pid}/dependencies",
        json={"predecessor_id": a["task_id"], "successor_id": b["task_id"]},
    )
    assert dep.status_code == 200

    # Create the reverse edge, then scheduling should detect the cycle.
    client.post(
        f"/api/projects/{pid}/dependencies",
        json={"predecessor_id": b["task_id"], "successor_id": a["task_id"]},
    )
    resp = client.get(f"/api/projects/{pid}/schedule")
    assert resp.status_code == 409


def test_export_endpoints(client):
    project = client.post("/api/projects", json={"mode": "empty", "name": "Exp"}).json()
    pid = project["project_id"]
    client.post(f"/api/projects/{pid}/tasks", json={"name": "T", "duration": 3})

    for fmt in ("json", "msproject", "primavera"):
        resp = client.get(f"/api/projects/{pid}/export/{fmt}")
        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]


def test_export_unknown_format(client):
    project = client.post("/api/projects", json={"mode": "empty", "name": "Exp2"}).json()
    resp = client.get(f"/api/projects/{project['project_id']}/export/nope")
    assert resp.status_code == 400


def test_get_missing_project_404(client):
    assert client.get("/api/projects/deadbeef").status_code == 404


def test_work_package_round_trip_via_api(client):
    packages = client.get("/api/work-packages").json()
    wp_id = packages[0]["work_package_id"]
    full = client.get(f"/api/work-packages/{wp_id}").json()

    created = client.post("/api/work-packages", json={"document": full})
    assert created.status_code == 200
    assert created.json()["name"] == full["name"]
