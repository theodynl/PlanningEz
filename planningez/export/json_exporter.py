"""Native PlanningEz JSON exporter.

Serializes a project to the canonical PlanningEz JSON format, which round-trips
losslessly through :func:`planningez.core.models.builders.build_project`.
"""

from __future__ import annotations

from planningez.core.models.project import Project
from planningez.export.base_exporter import BaseExporter, register_exporter
from planningez.utils.serialization import to_json


@register_exporter
class JSONExporter(BaseExporter):
    """Export a project to native PlanningEz JSON."""

    format_key = "json"
    file_extension = "json"
    display_name = "PlanningEz JSON"

    def export(self, project: Project) -> str:
        """Serialize the project to a JSON string."""
        return to_json(project)
