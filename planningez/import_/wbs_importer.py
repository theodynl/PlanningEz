"""WBS importers for PlanningEz.

Supports importing a Work Breakdown Structure from several formats. JSON is the
priority format and comes in two shapes: a nested-dict tree and a flat list of
rows carrying outline codes or explicit levels. CSV, Excel and XML reuse the
same flat-row logic through a configurable column mapping, with automatic
hierarchy detection from either an outline ``code`` column or an indentation
``level`` column.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree as ET

from planningez.core.models.wbs import WBS, WBSNode
from planningez.core.models.project import Project
from planningez.core.models.task import Task, TaskType
from planningez.core.exceptions import ImportError as PlanningImportError


@dataclass
class ColumnMapping:
    """Maps source columns to WBS concepts for flat/tabular imports."""

    name: str = "name"
    code: Optional[str] = "code"
    level: Optional[str] = None
    parent_code: Optional[str] = None
    work_package_code: Optional[str] = None


class WBSImporter:
    """Import a :class:`WBS` from JSON, CSV, Excel or XML sources."""

    # ------------------------------------------------------------------ #
    # JSON
    # ------------------------------------------------------------------ #
    def from_json(self, text: str, name: str = "WBS") -> WBS:
        """Import a WBS from a JSON document (nested tree or flat rows)."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise PlanningImportError(f"Invalid WBS JSON: {exc}") from exc

        if isinstance(data, dict):
            # Allow an optional top-level wrapper: {"name": .., "wbs": {...}}
            tree = data.get("wbs", data) if "wbs" in data else data
            return WBS.from_dict(tree, name=data.get("name", name))
        if isinstance(data, list):
            return self.from_rows(data, ColumnMapping(), name=name)
        raise PlanningImportError("Unsupported JSON structure for WBS import")

    def from_json_file(self, path: Union[str, Path], name: str = "WBS") -> WBS:
        """Import a WBS from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise PlanningImportError(f"File not found: {path}")
        return self.from_json(path.read_text(encoding="utf-8"), name=name)

    # ------------------------------------------------------------------ #
    # Flat rows (shared by JSON-list, CSV, Excel, XML)
    # ------------------------------------------------------------------ #
    def from_rows(
        self,
        rows: List[Dict[str, Any]],
        mapping: ColumnMapping,
        name: str = "WBS",
    ) -> WBS:
        """Build a WBS from flat rows using a column mapping.

        Hierarchy is detected, in order of preference, from: an explicit
        ``parent_code`` column, an outline ``code`` column (``1.2.3``), or an
        indentation ``level`` column with document order.
        """
        if mapping.parent_code:
            return self._from_parent_refs(rows, mapping, name)
        if mapping.code and any(r.get(mapping.code) for r in rows):
            return self._from_codes(rows, mapping, name)
        if mapping.level:
            return self._from_levels(rows, mapping, name)
        # Fallback: treat every row as a root.
        wbs = WBS(name=name)
        for row in rows:
            wbs.roots.append(WBSNode(name=str(row.get(mapping.name, "")).strip()))
        wbs.renumber()
        return wbs

    def _from_codes(self, rows: List[Dict[str, Any]], mapping: ColumnMapping, name: str) -> WBS:
        """Build hierarchy from outline codes like ``1``, ``1.2``, ``1.2.3``."""
        wbs = WBS(name=name)
        nodes_by_code: Dict[str, WBSNode] = {}
        # Sort so parents are always created before children.
        ordered = sorted(rows, key=lambda r: str(r.get(mapping.code, "")))
        for row in ordered:
            code = str(row.get(mapping.code, "")).strip()
            if not code:
                continue
            node = WBSNode(name=str(row.get(mapping.name, "")).strip(), code=code)
            self._attach_work_package(node, row, mapping)
            nodes_by_code[code] = node
            parent_code = ".".join(code.split(".")[:-1])
            if parent_code and parent_code in nodes_by_code:
                nodes_by_code[parent_code].add_child(node)
            else:
                wbs.roots.append(node)
        wbs.renumber()
        return wbs

    def _from_levels(self, rows: List[Dict[str, Any]], mapping: ColumnMapping, name: str) -> WBS:
        """Build hierarchy from an indentation level column plus row order."""
        wbs = WBS(name=name)
        stack: List[WBSNode] = []
        for row in rows:
            level = int(row.get(mapping.level, 1) or 1)
            node = WBSNode(name=str(row.get(mapping.name, "")).strip())
            self._attach_work_package(node, row, mapping)
            while stack and stack[-1].level >= level:
                stack.pop()
            if stack:
                stack[-1].add_child(node)
            else:
                node.level = 1
                wbs.roots.append(node)
            node.level = level
            stack.append(node)
        wbs.renumber()
        return wbs

    def _from_parent_refs(
        self, rows: List[Dict[str, Any]], mapping: ColumnMapping, name: str
    ) -> WBS:
        """Build hierarchy from explicit parent-code references."""
        wbs = WBS(name=name)
        nodes: Dict[str, WBSNode] = {}
        for row in rows:
            code = str(row.get(mapping.code, "")).strip()
            node = WBSNode(name=str(row.get(mapping.name, "")).strip(), code=code)
            self._attach_work_package(node, row, mapping)
            nodes[code] = node
        for row in rows:
            code = str(row.get(mapping.code, "")).strip()
            parent_code = str(row.get(mapping.parent_code, "") or "").strip()
            node = nodes[code]
            if parent_code and parent_code in nodes:
                nodes[parent_code].add_child(node)
            else:
                wbs.roots.append(node)
        wbs.renumber()
        return wbs

    @staticmethod
    def _attach_work_package(node: WBSNode, row: Dict[str, Any], mapping: ColumnMapping) -> None:
        """Record a Work Package code reference on a node, if present."""
        if mapping.work_package_code:
            wp_code = row.get(mapping.work_package_code)
            if wp_code:
                node.work_package_id = str(wp_code).strip()

    # ------------------------------------------------------------------ #
    # CSV
    # ------------------------------------------------------------------ #
    def from_csv(
        self,
        text: str,
        mapping: Optional[ColumnMapping] = None,
        name: str = "WBS",
    ) -> WBS:
        """Import a WBS from CSV text."""
        mapping = mapping or ColumnMapping()
        reader = csv.DictReader(io.StringIO(text))
        rows = [dict(r) for r in reader]
        return self.from_rows(rows, mapping, name=name)

    def from_csv_file(
        self,
        path: Union[str, Path],
        mapping: Optional[ColumnMapping] = None,
        name: str = "WBS",
    ) -> WBS:
        """Import a WBS from a CSV file."""
        path = Path(path)
        if not path.exists():
            raise PlanningImportError(f"File not found: {path}")
        return self.from_csv(path.read_text(encoding="utf-8"), mapping, name=name)

    # ------------------------------------------------------------------ #
    # Excel (requires openpyxl)
    # ------------------------------------------------------------------ #
    def from_excel(
        self,
        path: Union[str, Path],
        mapping: Optional[ColumnMapping] = None,
        name: str = "WBS",
        sheet: Optional[str] = None,
    ) -> WBS:
        """Import a WBS from an Excel workbook (first row = headers)."""
        try:
            from openpyxl import load_workbook
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise PlanningImportError(
                "Excel import requires the 'openpyxl' package (pip install openpyxl)"
            ) from exc

        mapping = mapping or ColumnMapping()
        path = Path(path)
        if not path.exists():
            raise PlanningImportError(f"File not found: {path}")
        workbook = load_workbook(filename=str(path), read_only=True, data_only=True)
        worksheet = workbook[sheet] if sheet else workbook.active
        rows_iter = worksheet.iter_rows(values_only=True)
        try:
            headers = [str(h) if h is not None else "" for h in next(rows_iter)]
        except StopIteration:
            return WBS(name=name)
        rows = [dict(zip(headers, values)) for values in rows_iter]
        return self.from_rows(rows, mapping, name=name)

    # ------------------------------------------------------------------ #
    # XML
    # ------------------------------------------------------------------ #
    def from_xml(self, text: str, name: str = "WBS") -> WBS:
        """Import a WBS from a nested XML document.

        Each element becomes a node; its ``name``/``Name`` attribute (or tag)
        is used as the node name and child elements become child nodes.
        """
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise PlanningImportError(f"Invalid WBS XML: {exc}") from exc

        wbs = WBS(name=root.get("name", name))
        for child in list(root):
            wbs.roots.append(self._xml_node(child, level=1))
        wbs.renumber()
        return wbs

    def _xml_node(self, element: ET.Element, level: int) -> WBSNode:
        """Recursively convert an XML element into a WBS node."""
        node_name = element.get("name") or element.get("Name") or element.tag
        node = WBSNode(name=str(node_name), level=level)
        for child in list(element):
            node.add_child(self._xml_node(child, level + 1))
        return node

    # ------------------------------------------------------------------ #
    # Task generation
    # ------------------------------------------------------------------ #
    def create_tasks(
        self,
        wbs: WBS,
        project: Project,
        leaf_duration: float = 1.0,
    ) -> Dict[str, str]:
        """Create project tasks mirroring the WBS and link them to nodes.

        Summary tasks are created for branch nodes and standard tasks for
        leaves. Returns a mapping of ``wbs_node_id -> task_id``.
        """
        node_to_task: Dict[str, str] = {}
        for node in wbs.flatten():
            is_leaf = node.is_leaf()
            task = Task(
                name=f"{node.code} {node.name}".strip(),
                task_type=TaskType.TASK if is_leaf else TaskType.SUMMARY,
                duration=leaf_duration if is_leaf else 0.0,
            )
            if node.parent_id and node.parent_id in node_to_task:
                task.parent_id = node_to_task[node.parent_id]
            project.add_task(task)
            node.task_id = task.task_id
            node_to_task[node.node_id] = task.task_id
        return node_to_task
