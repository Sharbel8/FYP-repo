"""Connect detection, tracking, counting, and MongoDB count snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from database import DetectionRepository
from detection import YoloDetector
from tracking.counter import LineCrossingCounter
from tracking.tracker import CentroidTracker, Track
from utils import get_logger

logger = get_logger("tracking.worker")


class TrafficCountingWorker:
    """Process frames and periodically persist cumulative line-crossing counts."""

    def __init__(
        self,
        detector: YoloDetector,
        tracker: CentroidTracker,
        counter: LineCrossingCounter,
        repository: DetectionRepository,
        *,
        lane_id: str = "default",
        count_interval_seconds: float = 5.0,
    ) -> None:
        if count_interval_seconds <= 0:
            raise ValueError("count_interval_seconds must be positive")
        self.detector = detector
        self.tracker = tracker
        self.counter = counter
        self.repository = repository
        self.lane_id = lane_id
        self.count_interval_seconds = count_interval_seconds
        self._last_persisted_at: datetime | None = None

    def process_frame(self, frame: np.ndarray, *, timestamp: datetime | None = None) -> tuple[list[Track], list[Track]]:
        """Detect, track, count crossings, and persist when the interval elapses."""
        observed_at = timestamp or datetime.now(timezone.utc)
        tracks = self.tracker.update(self.detector.detect(frame))
        crossings = self.counter.update(tracks)
        if self._should_persist(observed_at):
            self.repository.insert_counts(
                timestamp=observed_at,
                counts=self.counter.counts,
                lane_id=self.lane_id,
                source="vision_tracking",
                extra={"crossings_in_frame": len(crossings)},
            )
            self._last_persisted_at = observed_at
            logger.info("Persisted counts lane=%s counts=%s", self.lane_id, self.counter.counts)
        return tracks, crossings

    def _should_persist(self, observed_at: datetime) -> bool:
        return self._last_persisted_at is None or (
            observed_at - self._last_persisted_at
        ).total_seconds() >= self.count_interval_seconds
