"""JSON serialization helpers for PlanningEz models.

Provides an encoder that understands the primitives used across PlanningEz
models (``Enum``, ``datetime`` and ``date``) so that dataclasses can be
round-tripped to and from JSON without bespoke code in every model.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Any


class PlanningEzJSONEncoder(json.JSONEncoder):
    """JSON encoder aware of PlanningEz value types."""

    def default(self, o: Any) -> Any:  # noqa: D102 - see base class
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, (date, time)):
            return o.isoformat()
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        return super().default(o)


def to_dict(obj: Any) -> Any:
    """Convert a dataclass (or nested structure) into JSON-safe primitives."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return _normalize(asdict(obj))
    return _normalize(obj)


def _normalize(value: Any) -> Any:
    """Recursively turn Enums/dates into JSON-safe primitives."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {_normalize_key(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return value


def _normalize_key(key: Any) -> str:
    """Turn a dict key (possibly an Enum) into a JSON-safe string key."""
    if isinstance(key, Enum):
        return str(key.value)
    return str(key)


def to_json(obj: Any, *, indent: int = 2) -> str:
    """Serialize any PlanningEz model or structure to a JSON string."""
    return json.dumps(obj, cls=PlanningEzJSONEncoder, indent=indent, ensure_ascii=False)


def from_json(text: str) -> Any:
    """Parse a JSON string into Python primitives."""
    return json.loads(text)


def parse_date(value: Any) -> date | None:
    """Parse an ISO date/datetime string into a ``date`` (or ``None``)."""
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value)
    # Accept both plain dates and full datetimes.
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return datetime.fromisoformat(text).date()
