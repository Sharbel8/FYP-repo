"""MongoDB collection name constants."""

from __future__ import annotations

DETECTIONS = "detections"
SIGNAL_STATES = "signal_states"
AGGREGATES = "aggregates"
PREDICTIONS = "predictions"
SYSTEM_HEALTH = "system_health"

ALL_COLLECTIONS: tuple[str, ...] = (
    DETECTIONS,
    SIGNAL_STATES,
    AGGREGATES,
    PREDICTIONS,
    SYSTEM_HEALTH,
)
