"""Work Package library service for PlanningEz.

Manages a collection of reusable Work Packages. Packages can be held in memory
and, optionally, persisted to a directory as JSON files (one file per package,
plus a ``versions`` sub-directory keeping every saved revision). JSON is the
canonical exchange format so packages can be shared between users.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from planningez.core.models.work_package import WorkPackage
from planningez.core.models.builders import build_work_package
from planningez.core.exceptions import ImportError as PlanningImportError
from planningez.utils.serialization import to_json


class WorkPackageLibrary:
    """A registry of reusable Work Packages, optionally backed by disk."""

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None) -> None:
        """Initialize the library.

        Args:
            storage_dir: Optional directory used to persist packages as JSON.
                When provided, existing packages are loaded eagerly.
        """
        self._packages: Dict[str, WorkPackage] = {}
        self.storage_dir: Optional[Path] = Path(storage_dir) if storage_dir else None
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            (self.storage_dir / "versions").mkdir(exist_ok=True)
            self._load_all()

    # ------------------------------------------------------------------ #
    # In-memory registry
    # ------------------------------------------------------------------ #
    def add(self, package: WorkPackage) -> WorkPackage:
        """Register a package in memory (and persist it if disk-backed)."""
        self._packages[package.work_package_id] = package
        if self.storage_dir:
            self._write(package)
        return package

    def get(self, work_package_id: str) -> Optional[WorkPackage]:
        """Return a package by id, or ``None``."""
        return self._packages.get(work_package_id)

    def get_by_code(self, code: str) -> Optional[WorkPackage]:
        """Return the first package matching an outline/library code."""
        for package in self._packages.values():
            if package.code == code:
                return package
        return None

    def remove(self, work_package_id: str) -> None:
        """Remove a package from the library (and disk if persisted)."""
        self._packages.pop(work_package_id, None)
        if self.storage_dir:
            path = self.storage_dir / f"{work_package_id}.json"
            if path.exists():
                path.unlink()

    def list(self) -> List[Dict[str, str]]:
        """Return lightweight metadata for every package."""
        return [
            {
                "work_package_id": wp.work_package_id,
                "name": wp.name,
                "code": wp.code,
                "discipline": wp.discipline.value,
                "version": wp.version,
                "tasks": str(len(wp.tasks)),
            }
            for wp in self._packages.values()
        ]

    def filter_by_discipline(self, discipline: str) -> List[WorkPackage]:
        """Return all packages belonging to a given discipline."""
        return [
            wp for wp in self._packages.values() if wp.discipline.value == discipline
        ]

    def __len__(self) -> int:
        """Return the number of packages in the library."""
        return len(self._packages)

    # ------------------------------------------------------------------ #
    # Versioning
    # ------------------------------------------------------------------ #
    def save_version(self, package: WorkPackage, level: str = "patch") -> WorkPackage:
        """Bump the version, register the package and archive the revision."""
        package.bump_version(level)
        self.add(package)
        if self.storage_dir:
            versions_dir = self.storage_dir / "versions"
            versions_dir.mkdir(exist_ok=True)
            archive = versions_dir / f"{package.work_package_id}_{package.version}.json"
            archive.write_text(to_json(package), encoding="utf-8")
        return package

    # ------------------------------------------------------------------ #
    # Import / export (JSON)
    # ------------------------------------------------------------------ #
    def export_to_json(self, work_package_id: str) -> str:
        """Serialize a package to a JSON string."""
        package = self.get(work_package_id)
        if package is None:
            raise KeyError(f"Work Package '{work_package_id}' not found")
        return to_json(package)

    def export_to_file(self, work_package_id: str, path: Union[str, Path]) -> Path:
        """Write a package to a JSON file and return the path."""
        path = Path(path)
        path.write_text(self.export_to_json(work_package_id), encoding="utf-8")
        return path

    def import_from_json(self, text: str, register: bool = True) -> WorkPackage:
        """Load a package from a JSON string.

        Args:
            text: JSON document describing a single Work Package.
            register: When True, add the package to the library.
        """
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise PlanningImportError(f"Invalid Work Package JSON: {exc}") from exc
        package = build_work_package(data)
        if register:
            self.add(package)
        return package

    def import_from_file(self, path: Union[str, Path], register: bool = True) -> WorkPackage:
        """Load a package from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise PlanningImportError(f"File not found: {path}")
        return self.import_from_json(path.read_text(encoding="utf-8"), register=register)

    # ------------------------------------------------------------------ #
    # Disk persistence internals
    # ------------------------------------------------------------------ #
    def _write(self, package: WorkPackage) -> None:
        """Persist a package to the storage directory."""
        assert self.storage_dir is not None
        path = self.storage_dir / f"{package.work_package_id}.json"
        path.write_text(to_json(package), encoding="utf-8")

    def _load_all(self) -> None:
        """Load every package JSON file found in the storage directory."""
        assert self.storage_dir is not None
        for path in self.storage_dir.glob("*.json"):
            try:
                package = build_work_package(json.loads(path.read_text(encoding="utf-8")))
                self._packages[package.work_package_id] = package
            except (json.JSONDecodeError, KeyError, TypeError):
                # Skip malformed files rather than failing the whole library load.
                continue
