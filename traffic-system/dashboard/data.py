"""Read-only data adapter used by the Streamlit dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd

from database import AggregateRepository, DetectionRepository, PredictionRepository, SignalStateRepository


class DashboardDataService:
    """Convert MongoDB traffic documents into dashboard-ready frames."""

    def __init__(self, detections: DetectionRepository, signals: SignalStateRepository, aggregates: AggregateRepository, predictions: PredictionRepository) -> None:
        self.detections, self.signals = detections, signals
        self.aggregates, self.predictions = aggregates, predictions

    def latest_snapshot(self, *, lane_id: str = "default") -> dict[str, Any]:
        """Return the newest documents needed for dashboard headline metrics."""
        return {
            "detection": self._first(self.detections.latest(lane_id=lane_id, limit=1)),
            "signal": self._first(self.signals.latest(limit=1)),
            "aggregate": self._first(self.aggregates.latest(lane_id=lane_id, limit=1)),
            "prediction": self._first(self.predictions.latest(limit=1)),
        }

    def aggregate_history(self, *, lane_id: str = "default", limit: int = 100) -> pd.DataFrame:
        """Return oldest-to-newest feature rows for Plotly charts."""
        rows = list(reversed(self.aggregates.latest(lane_id=lane_id, limit=limit)))
        flattened = [{"window_end": row.get("window_end"), **row.get("features", {})} for row in rows]
        return pd.DataFrame(flattened)

    @staticmethod
    def _first(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        return rows[0] if rows else None
