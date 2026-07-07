"""Work Breakdown Structure (WBS) model for PlanningEz.

A WBS is a hierarchical decomposition of the total scope of work. Each node
carries an outline ``code`` (e.g. ``1.2.3``), a ``level`` (depth, root = 1),
and can be associated with a generated task and/or an existing Work Package.
"""

from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class WBSNode:
    """A single node in a Work Breakdown Structure."""

    name: str
    node_id: str = field(default_factory=lambda: str(uuid4())[:8])
    code: str = ""
    level: int = 1
    parent_id: Optional[str] = None
    children: List["WBSNode"] = field(default_factory=list)

    # Optional associations
    task_id: Optional[str] = None
    work_package_id: Optional[str] = None

    comments: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def add_child(self, child: "WBSNode") -> "WBSNode":
        """Attach a child node and link it back to this node."""
        child.parent_id = self.node_id
        child.level = self.level + 1
        self.children.append(child)
        return child

    def is_leaf(self) -> bool:
        """Return True when the node has no children."""
        return not self.children

    def iter_descendants(self) -> List["WBSNode"]:
        """Return this node plus all descendants in depth-first order."""
        nodes: List["WBSNode"] = [self]
        for child in self.children:
            nodes.extend(child.iter_descendants())
        return nodes

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the node (and its subtree) to a plain dict."""
        return {
            "name": self.name,
            "node_id": self.node_id,
            "code": self.code,
            "level": self.level,
            "parent_id": self.parent_id,
            "task_id": self.task_id,
            "work_package_id": self.work_package_id,
            "comments": self.comments,
            "children": [c.to_dict() for c in self.children],
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return f"WBSNode(code={self.code!r}, name={self.name!r}, children={len(self.children)})"


@dataclass
class WBS:
    """Container for a Work Breakdown Structure tree."""

    name: str = "WBS"
    roots: List[WBSNode] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], name: str = "WBS") -> "WBS":
        """Build a WBS from a nested-dict tree.

        The expected shape is a mapping where each key is a node name and each
        value is another mapping of children (an empty ``{}`` marks a leaf)::

            {"Project": {"Engineering": {"Process": {}}}}

        Args:
            data: Nested-dict representation of the hierarchy.
            name: Human-readable name for the resulting WBS.

        Returns:
            A fully built, numbered :class:`WBS`.
        """
        wbs = cls(name=name)
        wbs.roots = [cls._build_node(key, value, level=1) for key, value in data.items()]
        wbs.renumber()
        return wbs

    @staticmethod
    def _build_node(node_name: str, value: Any, level: int) -> WBSNode:
        """Recursively build a node and its children from nested-dict data."""
        node = WBSNode(name=node_name, level=level)
        if isinstance(value, dict):
            for child_name, child_value in value.items():
                child = WBS._build_node(child_name, child_value, level + 1)
                node.add_child(child)
        return node

    def renumber(self) -> None:
        """(Re)generate outline codes and levels for the whole tree."""
        for index, root in enumerate(self.roots, start=1):
            self._number_node(root, prefix="", index=index, level=1)

    def _number_node(self, node: WBSNode, prefix: str, index: int, level: int) -> None:
        """Assign an outline code such as ``1.2.3`` to a node and recurse."""
        node.code = f"{prefix}{index}"
        node.level = level
        for child_index, child in enumerate(node.children, start=1):
            self._number_node(child, prefix=f"{node.code}.", index=child_index, level=level + 1)

    def flatten(self) -> List[WBSNode]:
        """Return all nodes in depth-first order."""
        nodes: List[WBSNode] = []
        for root in self.roots:
            nodes.extend(root.iter_descendants())
        return nodes

    def get_node(self, node_id: str) -> Optional[WBSNode]:
        """Find a node by its id."""
        for node in self.flatten():
            if node.node_id == node_id:
                return node
        return None

    def find_by_code(self, code: str) -> Optional[WBSNode]:
        """Find a node by its outline code."""
        for node in self.flatten():
            if node.code == code:
                return node
        return None

    def max_depth(self) -> int:
        """Return the deepest level present in the tree."""
        return max((node.level for node in self.flatten()), default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the WBS to a plain dict."""
        return {"name": self.name, "roots": [r.to_dict() for r in self.roots]}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"WBS(name={self.name!r}, nodes={len(self.flatten())}, depth={self.max_depth()})"
