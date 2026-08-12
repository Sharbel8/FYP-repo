"""Domain repositories for traffic system collections."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo.database import Database

from database.base import BaseRepository, utc_now
from database import collections


class DetectionRepository(BaseRepository):
    """Stores periodic vehicle/pedestrian count snapshots."""

    collection_name = collections.DETECTIONS

    def insert_counts(
        self,
        *,
        timestamp: datetime | None = None,
        counts: dict[str, int],
        lane_id: str = "default",
        source: str = "vision",
        extra: dict[str, Any] | None = None,
    ) -> str:
        """
        Insert a detection/count document.

        Args:
            timestamp: Observation time (UTC). Defaults to now.
            counts: Mapping of class name → count (e.g. ``{"car": 3}``).
            lane_id: Logical lane or approach identifier.
            source: Data origin label.
            extra: Optional additional fields.

        Returns:
            Inserted document id as a string.
        """
        document: dict[str, Any] = {
            "timestamp": timestamp or utc_now(),
            "lane_id": lane_id,
            "counts": counts,
            "total_vehicles": sum(
                v for k, v in counts.items() if k != "person"
            ),
            "total_pedestrians": int(counts.get("person", 0)),
            "source": source,
        }
        if extra:
            document.update(extra)
        result = self.insert_one(document)
        return str(result.inserted_id)

    def latest(self, *, lane_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent detection documents."""
        query: dict[str, Any] = {}
        if lane_id is not None:
            query["lane_id"] = lane_id
        return self.find_many(query, limit=limit, sort=[("timestamp", -1)])


class SignalStateRepository(BaseRepository):
    """Stores traffic-light phase timings from Arduino (or mock)."""

    collection_name = collections.SIGNAL_STATES

    def insert_state(
        self,
        *,
        state: str,
        elapsed_s: float,
        durations: dict[str, float] | None = None,
        timestamp: datetime | None = None,
        source: str = "arduino",
        extra: dict[str, Any] | None = None,
    ) -> str:
        """
        Insert a signal-state document.

        Args:
            state: Current phase (``RED``, ``YELLOW``, ``GREEN``).
            elapsed_s: Seconds spent in the current phase so far.
            durations: Optional cumulative/last full-phase durations.
            timestamp: Observation time (UTC).
            source: ``arduino`` or ``mock``.
            extra: Optional additional fields.
        """
        document: dict[str, Any] = {
            "timestamp": timestamp or utc_now(),
            "state": state.upper(),
            "elapsed_s": float(elapsed_s),
            "durations": durations or {},
            "source": source,
        }
        if extra:
            document.update(extra)
        result = self.insert_one(document)
        return str(result.inserted_id)

    def latest(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent signal-state documents."""
        return self.find_many({}, limit=limit, sort=[("timestamp", -1)])


class AggregateRepository(BaseRepository):
    """Stores windowed traffic features for ML and charts."""

    collection_name = collections.AGGREGATES

    def insert_aggregate(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        features: dict[str, Any],
        lane_id: str = "default",
        extra: dict[str, Any] | None = None,
    ) -> str:
        """Insert a feature aggregate for a time window."""
        document: dict[str, Any] = {
            "window_start": window_start,
            "window_end": window_end,
            "lane_id": lane_id,
            "features": features,
        }
        if extra:
            document.update(extra)
        result = self.insert_one(document)
        return str(result.inserted_id)

    def latest(self, *, lane_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent aggregate windows."""
        query: dict[str, Any] = {}
        if lane_id is not None:
            query["lane_id"] = lane_id
        return self.find_many(query, limit=limit, sort=[("window_end", -1)])


class PredictionRepository(BaseRepository):
    """Stores model predictions for congestion / flow."""

    collection_name = collections.PREDICTIONS

    def insert_prediction(
        self,
        *,
        label: str,
        probability: float,
        model_version: str,
        features_ref: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        """Insert a prediction document."""
        document: dict[str, Any] = {
            "timestamp": timestamp or utc_now(),
            "label": label,
            "probability": float(probability),
            "model_version": model_version,
            "features_ref": features_ref or {},
        }
        if extra:
            document.update(extra)
        result = self.insert_one(document)
        return str(result.inserted_id)

    def latest(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent predictions."""
        return self.find_many({}, limit=limit, sort=[("timestamp", -1)])


class SystemHealthRepository(BaseRepository):
    """Stores worker heartbeats and health metrics."""

    collection_name = collections.SYSTEM_HEALTH

    def upsert_heartbeat(
        self,
        *,
        component: str,
        status: str,
        metrics: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        """
        Upsert the latest health record for a component.

        Args:
            component: e.g. ``vision_worker``, ``arduino_worker``, ``dashboard``.
            status: e.g. ``ok``, ``degraded``, ``error``.
            metrics: Optional numeric/string metrics (FPS, serial errors, …).
            message: Optional human-readable note.
        """
        payload = {
            "component": component,
            "status": status,
            "metrics": metrics or {},
            "message": message,
            "updated_at": utc_now(),
        }
        self.update_one(
            {"component": component},
            {"$set": payload, "$setOnInsert": {"created_at": utc_now()}},
            upsert=True,
        )

    def get_all(self) -> list[dict[str, Any]]:
        """Return health documents for all known components."""
        return self.find_many({}, limit=100, sort=[("component", 1)])


def build_repositories(database: Database) -> dict[str, BaseRepository]:
    """Construct the standard set of repositories for a database handle."""
    return {
        "detections": DetectionRepository(database),
        "signal_states": SignalStateRepository(database),
        "aggregates": AggregateRepository(database),
        "predictions": PredictionRepository(database),
        "system_health": SystemHealthRepository(database),
    }
