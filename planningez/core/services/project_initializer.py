"""Project initialization service for PlanningEz.

Offers several ways to start a new project, matching the "New Project" wizard:
an empty project, from a template, from one or more Work Packages, from an
existing WBS, or by importing a Microsoft Project, Primavera P6 or native
PlanningEz JSON file.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from planningez.core.models.project import Project
from planningez.core.models.wbs import WBS
from planningez.core.models.work_package import WorkPackage
from planningez.core.models.builders import build_project
from planningez.core.services.planning_generator import (
    PlanningGenerator,
    GenerationRules,
)
from planningez.import_.wbs_importer import WBSImporter
from planningez.import_.msproject_importer import MSProjectImporter
from planningez.import_.primavera_importer import PrimaveraImporter
from planningez.core.exceptions import ImportError as PlanningImportError


class StartMode(str, Enum):
    """Supported ways to initialize a new project."""

    EMPTY = "empty"
    TEMPLATE = "template"
    WORK_PACKAGE = "work_package"
    WBS = "wbs"
    MS_PROJECT = "ms_project"
    PRIMAVERA = "primavera"
    JSON = "json"


class ProjectInitializer:
    """Create new projects from a variety of starting points."""

    def __init__(self) -> None:
        """Initialize helper importers/generators."""
        self._wbs_importer = WBSImporter()
        self._msp_importer = MSProjectImporter()
        self._p6_importer = PrimaveraImporter()

    # ------------------------------------------------------------------ #
    # Simple modes
    # ------------------------------------------------------------------ #
    def create_empty(self, name: str = "New Project") -> Project:
        """Create a blank project with just the default calendar."""
        return Project(name=name)

    def from_template(self, template: Union[dict, str, Path], name: Optional[str] = None) -> Project:
        """Create a project from a template.

        The template is a native PlanningEz JSON structure (dict, JSON string or
        path). Any explicit ``name`` overrides the template's own name.
        """
        data = self._load_json(template)
        project = build_project(data)
        if name:
            project.name = name
        return project

    def from_json(self, source: Union[str, Path], name: Optional[str] = None) -> Project:
        """Create a project from a native PlanningEz JSON file or string."""
        data = self._load_json(source)
        project = build_project(data)
        if name:
            project.name = name
        return project

    # ------------------------------------------------------------------ #
    # Work Package / WBS modes
    # ------------------------------------------------------------------ #
    def from_work_packages(
        self,
        packages: List[WorkPackage],
        name: str = "New Project",
        rules: Optional[GenerationRules] = None,
    ) -> Project:
        """Create a project by assembling selected Work Packages."""
        if not packages:
            raise PlanningImportError("At least one Work Package is required")
        generator = PlanningGenerator(rules=rules)
        return generator.generate(packages, project_name=name)

    def from_wbs(
        self,
        wbs: WBS,
        name: str = "New Project",
        create_tasks: bool = True,
    ) -> Project:
        """Create a project from an existing WBS, optionally generating tasks."""
        project = Project(name=name)
        if create_tasks:
            self._wbs_importer.create_tasks(wbs, project)
        return project

    def from_wbs_json(
        self,
        source: Union[str, Path],
        name: str = "New Project",
        create_tasks: bool = True,
    ) -> Project:
        """Create a project from a WBS JSON document."""
        text = self._read_text(source)
        wbs = self._wbs_importer.from_json(text, name=name)
        return self.from_wbs(wbs, name=name, create_tasks=create_tasks)

    # ------------------------------------------------------------------ #
    # External file imports
    # ------------------------------------------------------------------ #
    def from_ms_project(self, path: Union[str, Path]) -> Project:
        """Create a project by importing a Microsoft Project XML file."""
        return self._msp_importer.from_file(path)

    def from_primavera(self, path: Union[str, Path]) -> Project:
        """Create a project by importing a Primavera P6 XML file."""
        return self._p6_importer.from_file(path)

    # ------------------------------------------------------------------ #
    # Dispatch
    # ------------------------------------------------------------------ #
    def create(self, mode: StartMode, **kwargs) -> Project:
        """Dispatch to the appropriate creation method for ``mode``.

        Keyword arguments are forwarded to the underlying method (e.g.
        ``name``, ``packages``, ``wbs``, ``path``, ``source``).
        """
        if mode == StartMode.EMPTY:
            return self.create_empty(kwargs.get("name", "New Project"))
        if mode == StartMode.TEMPLATE:
            return self.from_template(kwargs["template"], kwargs.get("name"))
        if mode == StartMode.WORK_PACKAGE:
            return self.from_work_packages(
                kwargs["packages"],
                kwargs.get("name", "New Project"),
                kwargs.get("rules"),
            )
        if mode == StartMode.WBS:
            if "wbs" in kwargs:
                return self.from_wbs(
                    kwargs["wbs"], kwargs.get("name", "New Project"),
                    kwargs.get("create_tasks", True),
                )
            return self.from_wbs_json(
                kwargs["source"], kwargs.get("name", "New Project"),
                kwargs.get("create_tasks", True),
            )
        if mode == StartMode.MS_PROJECT:
            return self.from_ms_project(kwargs["path"])
        if mode == StartMode.PRIMAVERA:
            return self.from_primavera(kwargs["path"])
        if mode == StartMode.JSON:
            return self.from_json(kwargs["source"], kwargs.get("name"))
        raise PlanningImportError(f"Unsupported start mode: {mode}")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _read_text(source: Union[str, Path]) -> str:
        """Read text from a path, or return the string as-is if not a file."""
        if isinstance(source, Path):
            return source.read_text(encoding="utf-8")
        path = Path(source)
        if len(source) < 260 and path.exists():
            return path.read_text(encoding="utf-8")
        return source

    def _load_json(self, source: Union[dict, str, Path]) -> dict:
        """Load JSON from a dict, JSON string or file path."""
        if isinstance(source, dict):
            return source
        text = self._read_text(source)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise PlanningImportError(f"Invalid PlanningEz JSON: {exc}") from exc
