"""Export subsystem for PlanningEz.

Importing this package registers the built-in exporters (JSON, Microsoft
Project, Primavera P6) with the registry in :mod:`base_exporter`.
"""

from planningez.export.base_exporter import (
    BaseExporter,
    register_exporter,
    get_exporter,
    available_formats,
    export_project,
)

# Importing the concrete exporters triggers their @register_exporter decorators.
from planningez.export.json_exporter import JSONExporter
from planningez.export.msproject_exporter import MSProjectExporter
from planningez.export.primavera_exporter import PrimaveraExporter

__all__ = [
    "BaseExporter",
    "register_exporter",
    "get_exporter",
    "available_formats",
    "export_project",
    "JSONExporter",
    "MSProjectExporter",
    "PrimaveraExporter",
]
