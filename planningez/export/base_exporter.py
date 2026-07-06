"""Export abstraction layer for PlanningEz.

Defines a common :class:`BaseExporter` interface plus a registry so that new
export formats (Asta Powerproject, Power BI, Smartsheet, Oracle Primavera
Cloud, ...) can be plugged in without touching calling code. Register a new
exporter with the :func:`register_exporter` decorator and it becomes available
through :func:`get_exporter` / :func:`export_project`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type, Union

from planningez.core.models.project import Project
from planningez.core.exceptions import ExportError


class BaseExporter(ABC):
    """Abstract base class for all project exporters."""

    #: Short format key, e.g. ``"json"`` or ``"msproject"``.
    format_key: str = ""
    #: Default file extension (without the dot).
    file_extension: str = "txt"
    #: Human-readable label for UIs.
    display_name: str = "Base Exporter"

    @abstractmethod
    def export(self, project: Project) -> str:
        """Serialize a project to a string in the target format."""
        raise NotImplementedError

    def export_to_file(self, project: Project, path: Union[str, Path]) -> Path:
        """Serialize a project and write it to ``path``."""
        path = Path(path)
        try:
            path.write_text(self.export(project), encoding="utf-8")
        except OSError as exc:
            raise ExportError(f"Failed to write export to {path}: {exc}") from exc
        return path


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
_REGISTRY: Dict[str, Type[BaseExporter]] = {}


def register_exporter(cls: Type[BaseExporter]) -> Type[BaseExporter]:
    """Class decorator registering an exporter by its ``format_key``."""
    if not cls.format_key:
        raise ExportError(f"{cls.__name__} must define a non-empty 'format_key'")
    _REGISTRY[cls.format_key] = cls
    return cls


def get_exporter(format_key: str) -> BaseExporter:
    """Instantiate a registered exporter for ``format_key``."""
    exporter_cls = _REGISTRY.get(format_key)
    if exporter_cls is None:
        raise ExportError(
            f"No exporter registered for '{format_key}'. "
            f"Available: {', '.join(sorted(_REGISTRY)) or '(none)'}"
        )
    return exporter_cls()


def available_formats() -> List[str]:
    """Return the sorted list of registered format keys."""
    return sorted(_REGISTRY)


def export_project(project: Project, format_key: str, path: Union[str, Path]) -> Path:
    """Convenience: export a project to a file using a registered format."""
    return get_exporter(format_key).export_to_file(project, path)
