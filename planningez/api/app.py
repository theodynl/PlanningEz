"""PlanningEz FastAPI application.

Exposes the PlanningEz core (projects, WBS, Work Packages, planning generation,
scheduling and multi-format export) as a REST API consumed by the React web
frontend. When a built frontend is present at ``frontend/dist`` it is served as
static files so the whole app runs from a single ``python -m planningez``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType, TaskStatus
from planningez.core.models.dependency import Dependency, DependencyType
from planningez.core.models.resource import Resource, ResourceRole
from planningez.core.models.work_package import Discipline
from planningez.core.models.builders import build_work_package
from planningez.core.services.planning_engine import PlanningEngine
from planningez.core.services.planning_generator import (
    PlanningGenerator,
    GenerationRules,
    ConnectMode,
)
from planningez.core.services.project_initializer import ProjectInitializer, StartMode
from planningez.import_.wbs_importer import WBSImporter
from planningez.core.exceptions import PlanningEzException, CircularDependencyError
from planningez.utils.serialization import to_dict, to_json, parse_date
from planningez import export as export_pkg

from planningez.api.store import store
from planningez.api.schemas import (
    CreateProjectRequest,
    GenerateRequest,
    TaskCreateRequest,
    TaskUpdateRequest,
    DependencyCreateRequest,
    ResourceCreateRequest,
    WBSPreviewRequest,
    WorkPackageImportRequest,
)

app = FastAPI(title="PlanningEz API", version="0.1.0")

# Allow the Vite dev server (and any local origin) to call the API in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_initializer = ProjectInitializer()
_wbs_importer = WBSImporter()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _serialize_project(project: Project) -> Dict[str, Any]:
    """Serialize a project to a JSON-safe dict for API responses."""
    return to_dict(project)


def _project_summary(project: Project) -> Dict[str, Any]:
    """Return lightweight project metadata for list views."""
    return {
        "project_id": project.project_id,
        "name": project.name,
        "tasks": len(project.tasks),
        "resources": len(project.resources),
        "start_date": project.start_date.isoformat() if project.start_date else None,
    }


def _require_project(project_id: str) -> Project:
    """Fetch a project or raise 404."""
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return project


# --------------------------------------------------------------------------- #
# Meta / health
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health() -> Dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok", "service": "planningez"}


@app.get("/api/meta")
def meta() -> Dict[str, List[str]]:
    """Return enum choices used to populate UI dropdowns."""
    return {
        "start_modes": [m.value for m in StartMode],
        "disciplines": [d.value for d in Discipline],
        "resource_roles": [r.value for r in ResourceRole],
        "task_types": [t.value for t in TaskType],
        "task_statuses": [s.value for s in TaskStatus],
        "dependency_types": [d.value for d in DependencyType],
        "connect_modes": [c.value for c in ConnectMode],
        "export_formats": export_pkg.available_formats(),
    }


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
@app.get("/api/projects")
def list_projects() -> List[Dict[str, Any]]:
    """List all projects (summary view)."""
    return [_project_summary(p) for p in store.list_projects()]


@app.post("/api/projects")
def create_project(req: CreateProjectRequest) -> Dict[str, Any]:
    """Create a project using one of the supported start modes."""
    try:
        if req.mode == "empty":
            project = _initializer.create_empty(req.name)
        elif req.mode == "wbs":
            if not req.wbs_content:
                raise HTTPException(status_code=400, detail="wbs_content is required")
            wbs = _parse_wbs(req.wbs_format, req.wbs_content, req.name)
            project = _initializer.from_wbs(wbs, name=req.name, create_tasks=req.create_tasks)
        elif req.mode == "work_package":
            packages = _resolve_packages(req.work_package_ids)
            rules = GenerationRules(connect_mode=ConnectMode(req.connect_mode))
            project = _initializer.from_work_packages(packages, name=req.name, rules=rules)
        elif req.mode in ("template", "json"):
            if req.document is None:
                raise HTTPException(status_code=400, detail="document is required")
            project = _initializer.from_template(req.document, name=req.name)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported mode: {req.mode}")
    except HTTPException:
        raise
    except PlanningEzException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.add_project(project)
    return _serialize_project(project)


@app.post("/api/projects/generate")
def generate_project(req: GenerateRequest) -> Dict[str, Any]:
    """Generate a project by assembling selected Work Packages."""
    packages = _resolve_packages(req.work_package_ids)
    if not packages:
        raise HTTPException(status_code=400, detail="At least one Work Package is required")
    rules = GenerationRules(connect_mode=ConnectMode(req.connect_mode))
    project = PlanningGenerator(rules).generate(packages, project_name=req.name)
    store.add_project(project)
    return _serialize_project(project)


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> Dict[str, Any]:
    """Return the full project."""
    return _serialize_project(_require_project(project_id))


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str) -> Dict[str, str]:
    """Delete a project."""
    _require_project(project_id)
    store.remove_project(project_id)
    return {"status": "deleted", "project_id": project_id}


@app.get("/api/projects/{project_id}/schedule")
def schedule_project(project_id: str) -> Dict[str, Any]:
    """Run the planning engine and return the scheduled project."""
    project = _require_project(project_id)
    try:
        PlanningEngine(project).calculate()
    except CircularDependencyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _serialize_project(project)


# --------------------------------------------------------------------------- #
# Tasks / dependencies / resources
# --------------------------------------------------------------------------- #
@app.post("/api/projects/{project_id}/tasks")
def add_task(project_id: str, req: TaskCreateRequest) -> Dict[str, Any]:
    """Add a task to a project."""
    project = _require_project(project_id)
    task = Task(
        name=req.name,
        duration=req.duration,
        task_type=TaskType(req.task_type),
        parent_id=req.parent_id,
        responsible=req.responsible,
        progress=req.progress,
        is_milestone=req.is_milestone,
    )
    project.add_task(task)
    return to_dict(task)


@app.patch("/api/projects/{project_id}/tasks/{task_id}")
def update_task(project_id: str, task_id: str, req: TaskUpdateRequest) -> Dict[str, Any]:
    """Update fields of an existing task."""
    project = _require_project(project_id)
    task = project.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if req.name is not None:
        task.name = req.name
    if req.duration is not None:
        task.duration = req.duration
    if req.status is not None:
        task.status = TaskStatus(req.status)
    if req.progress is not None:
        task.update_progress(req.progress)
    if req.responsible is not None:
        task.responsible = req.responsible
    if req.parent_id is not None:
        task.parent_id = req.parent_id
    if req.clear_constraint:
        task.constraint_date = None
    elif req.constraint_date is not None:
        task.constraint_date = parse_date(req.constraint_date)
    return to_dict(task)


@app.delete("/api/projects/{project_id}/tasks/{task_id}")
def delete_task(project_id: str, task_id: str) -> Dict[str, str]:
    """Remove a task (and its dependencies) from a project."""
    project = _require_project(project_id)
    if project.get_task(task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    project.remove_task(task_id)
    return {"status": "deleted", "task_id": task_id}


@app.post("/api/projects/{project_id}/dependencies")
def add_dependency(project_id: str, req: DependencyCreateRequest) -> Dict[str, Any]:
    """Add a dependency between two tasks."""
    project = _require_project(project_id)
    if project.get_task(req.predecessor_id) is None or project.get_task(req.successor_id) is None:
        raise HTTPException(status_code=404, detail="Predecessor or successor task not found")
    try:
        dep = Dependency(
            predecessor_id=req.predecessor_id,
            successor_id=req.successor_id,
            dependency_type=DependencyType(req.dependency_type),
            lag=req.lag,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    project.add_dependency(dep)
    return to_dict(dep)


@app.post("/api/projects/{project_id}/resources")
def add_resource(project_id: str, req: ResourceCreateRequest) -> Dict[str, Any]:
    """Add a resource to a project."""
    project = _require_project(project_id)
    resource = Resource(
        name=req.name,
        role=ResourceRole(req.role),
        daily_cost=req.daily_cost,
        availability=req.availability,
    )
    project.add_resource(resource)
    return to_dict(resource)


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
_MEDIA_TYPES = {"json": "application/json", "xml": "application/xml"}


@app.get("/api/projects/{project_id}/export/{format_key}")
def export_project(project_id: str, format_key: str) -> Response:
    """Export a project in a registered format as a downloadable file."""
    project = _require_project(project_id)
    try:
        exporter = export_pkg.get_exporter(format_key)
        content = exporter.export(project)
    except PlanningEzException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    safe_name = project.name.replace(" ", "_")
    filename = f"{safe_name}.{exporter.file_extension}"
    return Response(
        content=content,
        media_type=_MEDIA_TYPES.get(exporter.file_extension, "text/plain"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------------------------------- #
# WBS
# --------------------------------------------------------------------------- #
@app.post("/api/wbs/preview")
def preview_wbs(req: WBSPreviewRequest) -> Dict[str, Any]:
    """Parse WBS content and return the resulting tree for preview."""
    try:
        wbs = _parse_wbs(req.format, req.content, req.name)
    except PlanningEzException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"wbs": wbs.to_dict(), "node_count": len(wbs.flatten()), "depth": wbs.max_depth()}


# --------------------------------------------------------------------------- #
# Work Packages
# --------------------------------------------------------------------------- #
@app.get("/api/work-packages")
def list_work_packages() -> List[Dict[str, str]]:
    """List Work Packages in the library."""
    return store.library.list()


@app.get("/api/work-packages/{wp_id}")
def get_work_package(wp_id: str) -> Dict[str, Any]:
    """Return a full Work Package."""
    wp = store.library.get(wp_id)
    if wp is None:
        raise HTTPException(status_code=404, detail="Work Package not found")
    return to_dict(wp)


@app.post("/api/work-packages")
def create_work_package(req: WorkPackageImportRequest) -> Dict[str, Any]:
    """Create or import a Work Package from a JSON document."""
    try:
        wp = build_work_package(req.document)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Work Package: {exc}") from exc
    store.library.add(wp)
    return to_dict(wp)


@app.delete("/api/work-packages/{wp_id}")
def delete_work_package(wp_id: str) -> Dict[str, str]:
    """Remove a Work Package from the library."""
    if store.library.get(wp_id) is None:
        raise HTTPException(status_code=404, detail="Work Package not found")
    store.library.remove(wp_id)
    return {"status": "deleted", "work_package_id": wp_id}


@app.get("/api/work-packages/{wp_id}/export")
def export_work_package(wp_id: str) -> Response:
    """Download a Work Package as JSON."""
    wp = store.library.get(wp_id)
    if wp is None:
        raise HTTPException(status_code=404, detail="Work Package not found")
    filename = f"{(wp.code or wp.name).replace(' ', '_')}.json"
    return Response(
        content=to_json(wp),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _parse_wbs(fmt: str, content: str, name: str):
    """Parse WBS content in the requested format."""
    fmt = (fmt or "json").lower()
    if fmt == "json":
        return _wbs_importer.from_json(content, name=name)
    if fmt == "csv":
        return _wbs_importer.from_csv(content, name=name)
    if fmt == "xml":
        return _wbs_importer.from_xml(content, name=name)
    raise HTTPException(status_code=400, detail=f"Unsupported WBS format: {fmt}")


def _resolve_packages(ids: List[str]):
    """Resolve Work Package ids to instances, raising 404 for unknown ids."""
    packages = []
    for wp_id in ids:
        wp = store.library.get(wp_id)
        if wp is None:
            raise HTTPException(status_code=404, detail=f"Work Package '{wp_id}' not found")
        packages.append(wp)
    return packages


# --------------------------------------------------------------------------- #
# Static frontend (served when built)
# --------------------------------------------------------------------------- #
def _resolve_frontend_dist() -> Path:
    """Locate the built frontend, working both from source and when frozen.

    Resolution order: an explicit ``PLANNINGEZ_FRONTEND_DIST`` override, the
    PyInstaller bundle directory (``sys._MEIPASS``) when running as a packaged
    executable, then the in-repo ``frontend/dist``.
    """
    override = os.environ.get("PLANNINGEZ_FRONTEND_DIST")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):  # packaged with PyInstaller
        return Path(getattr(sys, "_MEIPASS", ".")) / "frontend" / "dist"
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


_FRONTEND_DIST = _resolve_frontend_dist()
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
