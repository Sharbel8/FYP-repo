"""Unit tests for tracking, one-time crossing counts, and persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mongomock import MongoClient as MockMongoClient
import numpy as np

from database import DetectionRepository
from detection import Detection
from tracking import CentroidTracker, CountingLine, LineCrossingCounter, TrafficCountingWorker


def _detection(x: float, *, class_name: str = "car") -> Detection:
    return Detection(class_name, .9, x - 5, 10, x + 5, 30)


def test_tracker_keeps_an_id_for_nearby_same_class_object() -> None:
    tracker = CentroidTracker(max_distance=30)
    first, second = tracker.update([_detection(10)])[0], tracker.update([_detection(20)])[0]
    assert first.track_id == second.track_id and second.centroid == (20, 20)


def test_line_crossing_counts_a_track_only_once() -> None:
    tracker, counter = CentroidTracker(max_distance=30), LineCrossingCounter(CountingLine((0, 0), (0, 100)))
    assert counter.update(tracker.update([_detection(-10)])) == []
    assert len(counter.update(tracker.update([_detection(10)]))) == 1
    assert counter.counts == {"car": 1}
    assert counter.update(tracker.update([_detection(-10)])) == [] and counter.counts == {"car": 1}


class _SequenceDetector:
    def __init__(self) -> None: self.frames = [[_detection(-10)], [_detection(10)]]
    def detect(self, frame): return self.frames.pop(0)


def test_worker_persists_counts_at_configured_interval() -> None:
    repository = DetectionRepository(MockMongoClient()["traffic_system_test"])
    worker = TrafficCountingWorker(_SequenceDetector(), CentroidTracker(max_distance=30), LineCrossingCounter(CountingLine((0, 0), (0, 100))), repository, lane_id="north", count_interval_seconds=5)  # type: ignore[arg-type]
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    worker.process_frame(np.zeros((2, 2, 3), dtype=np.uint8), timestamp=started)
    worker.process_frame(np.zeros((2, 2, 3), dtype=np.uint8), timestamp=started + timedelta(seconds=5))
    snapshots = repository.latest(lane_id="north")
    assert len(snapshots) == 2 and snapshots[0]["counts"] == {"car": 1} and snapshots[0]["source"] == "vision_tracking"
