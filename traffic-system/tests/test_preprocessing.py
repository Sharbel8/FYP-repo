"""Unit tests for preprocessing features and aggregator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mongomock import MongoClient as MockMongoClient

from database import (
    AggregateRepository,
    DetectionRepository,
    SignalStateRepository,
    ensure_indexes,
)
from preprocessing import FeatureAggregator, compute_features


def test_compute_features_labels() -> None:
    low = compute_features(vehicle_count=1, window_seconds=10, red_duration_s=5)
    assert low.congestion_label == "low"
    assert low.flow_rate_per_min == 6.0

    high = compute_features(
        vehicle_count=18,
        window_seconds=10,
        red_duration_s=40,
        density_capacity=20,
    )
    assert high.congestion_label in {"medium", "high"}
    assert 0.0 <= high.congestion_score <= 1.0
    assert high.waiting_time_proxy > 0


def test_feature_aggregator_persists_window() -> None:
    db = MockMongoClient()["traffic_test"]
    ensure_indexes(db)
    detections = DetectionRepository(db)
    signals = SignalStateRepository(db)
    aggregates = AggregateRepository(db)

    now = datetime.now(timezone.utc)
    detections.insert_counts(
        timestamp=now - timedelta(seconds=3),
        counts={"car": 4, "bus": 1, "person": 2},
        lane_id="default",
        source="test",
    )
    signals.insert_state(
        state="RED",
        elapsed_s=10,
        durations={"RED": 35, "YELLOW": 3, "GREEN": 25},
        timestamp=now - timedelta(seconds=1),
        source="mock",
    )

    aggregator = FeatureAggregator(
        detections,
        signals,
        aggregates,
        window_seconds=10,
        lane_id="default",
    )
    doc_id = aggregator.persist_window(window_end=now)
    assert doc_id

    rows = aggregates.latest(limit=1)
    assert len(rows) == 1
    features = rows[0]["features"]
    assert features["vehicle_count"] == 5
    assert features["pedestrian_count"] == 2
    assert features["congestion_label"] in {"low", "medium", "high"}
    assert rows[0]["signal_state"] == "RED"
