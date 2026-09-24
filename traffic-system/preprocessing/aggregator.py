"""Join detections + signal states into windowed feature aggregates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from database import AggregateRepository, DetectionRepository, SignalStateRepository
from preprocessing.cleaner import (
    ensure_utc,
    extract_detection_totals,
    extract_signal_durations,
)
from preprocessing.features import TrafficFeatures, compute_features
from utils import get_logger

logger = get_logger("preprocessing.aggregator")


class FeatureAggregator:
    """
    Build one aggregate document from recent detections and the latest signal state.

    This is the bridge between raw collectors and ML / dashboard charts.
    """

    def __init__(
        self,
        detection_repo: DetectionRepository,
        signal_repo: SignalStateRepository,
        aggregate_repo: AggregateRepository,
        *,
        window_seconds: int = 10,
        lane_id: str = "default",
        density_capacity: float = 20.0,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.detection_repo = detection_repo
        self.signal_repo = signal_repo
        self.aggregate_repo = aggregate_repo
        self.window_seconds = window_seconds
        self.lane_id = lane_id
        self.density_capacity = density_capacity

    def build_window(
        self,
        *,
        window_end: datetime | None = None,
    ) -> tuple[TrafficFeatures, dict[str, Any]]:
        """
        Compute features for ``[window_end - window, window_end]``.

        Returns:
            ``(features, context)`` where context includes source document ids.
        """
        end = ensure_utc(window_end) or datetime.now(timezone.utc)
        start = end - timedelta(seconds=self.window_seconds)

        detections = self._detections_in_window(start, end)
        signal = self._latest_signal_at_or_before(end)

        vehicle_total = 0
        pedestrian_total = 0
        for doc in detections:
            v, p = extract_detection_totals(doc)
            vehicle_total += v
            pedestrian_total += p

        # If multiple snapshots landed in the window, use the latest snapshot
        # totals as the representative "density" view, but keep summed flow.
        latest_vehicles, latest_pedestrians = (0, 0)
        if detections:
            latest_vehicles, latest_pedestrians = extract_detection_totals(detections[0])

        state, durations = extract_signal_durations(signal)
        features = compute_features(
            vehicle_count=latest_vehicles if detections else vehicle_total,
            pedestrian_count=latest_pedestrians if detections else pedestrian_total,
            window_seconds=float(self.window_seconds),
            red_duration_s=durations["RED"],
            yellow_duration_s=durations["YELLOW"],
            green_duration_s=durations["GREEN"],
            current_state=state,
            density_capacity=self.density_capacity,
        )

        # Prefer summed vehicles for flow when multiple intervals exist
        if len(detections) > 1 and vehicle_total > 0:
            features = compute_features(
                vehicle_count=vehicle_total / len(detections),
                pedestrian_count=pedestrian_total / len(detections),
                window_seconds=float(self.window_seconds),
                red_duration_s=durations["RED"],
                yellow_duration_s=durations["YELLOW"],
                green_duration_s=durations["GREEN"],
                current_state=state,
                density_capacity=self.density_capacity,
            )

        context = {
            "window_start": start,
            "window_end": end,
            "lane_id": self.lane_id,
            "detection_count": len(detections),
            "signal_state": state,
            "signal_id": str(signal.get("_id")) if signal else None,
        }
        return features, context

    def persist_window(self, *, window_end: datetime | None = None) -> str:
        """Compute features for the latest window and store them in MongoDB."""
        features, context = self.build_window(window_end=window_end)
        doc_id = self.aggregate_repo.insert_aggregate(
            window_start=context["window_start"],
            window_end=context["window_end"],
            features=features.to_dict(),
            lane_id=self.lane_id,
            extra={
                "detection_count": context["detection_count"],
                "signal_state": context["signal_state"],
                "signal_id": context["signal_id"],
                "source": "feature_aggregator",
            },
        )
        logger.info(
            "Stored aggregate id=%s label=%s score=%.3f vehicles=%.1f",
            doc_id,
            features.congestion_label,
            features.congestion_score,
            features.vehicle_count,
        )
        return doc_id

    def _detections_in_window(
        self,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        # latest() already sorts newest-first; filter in Python for mongomock simplicity
        recent = self.detection_repo.latest(lane_id=self.lane_id, limit=200)
        selected: list[dict[str, Any]] = []
        for doc in recent:
            ts = ensure_utc(doc.get("timestamp"))
            if ts is None:
                continue
            if start <= ts <= end:
                selected.append(doc)
        return selected

    def _latest_signal_at_or_before(self, end: datetime) -> dict[str, Any] | None:
        recent = self.signal_repo.latest(limit=100)
        for doc in recent:
            ts = ensure_utc(doc.get("timestamp"))
            if ts is None:
                continue
            if ts <= end:
                return doc
        return recent[0] if recent else None
