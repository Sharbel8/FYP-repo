"""Helpers to clean raw MongoDB traffic documents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def ensure_utc(value: datetime | None) -> datetime | None:
    """Normalize datetimes to timezone-aware UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def safe_int(value: Any, default: int = 0) -> int:
    """Convert a value to int, falling back to ``default``."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float, falling back to ``default``."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sum_vehicle_counts(counts: dict[str, Any] | None) -> int:
    """Sum vehicle classes, excluding pedestrians."""
    if not counts:
        return 0
    total = 0
    for key, value in counts.items():
        if str(key).lower() == "person":
            continue
        total += safe_int(value, 0)
    return max(0, total)


def extract_detection_totals(document: dict[str, Any]) -> tuple[int, int]:
    """
    Return ``(vehicles, pedestrians)`` from a detection document.

    Prefers stored totals, then falls back to the ``counts`` map.
    """
    counts = document.get("counts") if isinstance(document.get("counts"), dict) else {}
    vehicles = document.get("total_vehicles")
    pedestrians = document.get("total_pedestrians")

    if vehicles is None:
        vehicles = sum_vehicle_counts(counts)
    if pedestrians is None:
        pedestrians = safe_int(counts.get("person", 0), 0)

    return safe_int(vehicles, 0), safe_int(pedestrians, 0)


def extract_signal_durations(document: dict[str, Any] | None) -> tuple[str, dict[str, float]]:
    """Return ``(state, durations)`` from a signal-state document."""
    if not document:
        return "GREEN", {"RED": 0.0, "YELLOW": 0.0, "GREEN": 0.0}

    state = str(document.get("state", "GREEN")).upper()
    raw = document.get("durations") if isinstance(document.get("durations"), dict) else {}
    durations = {
        "RED": safe_float(raw.get("RED", raw.get("red", 0.0))),
        "YELLOW": safe_float(raw.get("YELLOW", raw.get("yellow", 0.0))),
        "GREEN": safe_float(raw.get("GREEN", raw.get("green", 0.0))),
    }
    return state, durations
