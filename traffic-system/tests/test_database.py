"""Unit tests for the database layer (mongomock — no live server required)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from mongomock import MongoClient as MockMongoClient

from database.indexes import ensure_indexes
from database.repositories import (
    AggregateRepository,
    DetectionRepository,
    PredictionRepository,
    SignalStateRepository,
    SystemHealthRepository,
    build_repositories,
)


@pytest.fixture()
def mock_db():
    """Provide an isolated in-memory MongoDB database."""
    client = MockMongoClient()
    return client["traffic_system_test"]


def test_detection_insert_and_latest(mock_db) -> None:
    repo = DetectionRepository(mock_db)
    doc_id = repo.insert_counts(
        counts={"car": 2, "truck": 1, "person": 3},
        lane_id="north",
    )
    assert doc_id

    rows = repo.latest(lane_id="north", limit=5)
    assert len(rows) == 1
    assert rows[0]["total_vehicles"] == 3
    assert rows[0]["total_pedestrians"] == 3
    assert rows[0]["counts"]["car"] == 2


def test_signal_state_insert(mock_db) -> None:
    repo = SignalStateRepository(mock_db)
    doc_id = repo.insert_state(
        state="red",
        elapsed_s=12.5,
        durations={"RED": 45.0, "YELLOW": 3.0, "GREEN": 30.0},
        source="mock",
    )
    assert doc_id
    latest = repo.latest(limit=1)
    assert latest[0]["state"] == "RED"
    assert latest[0]["elapsed_s"] == 12.5


def test_aggregate_and_prediction(mock_db) -> None:
    now = datetime.now(timezone.utc)
    aggregates = AggregateRepository(mock_db)
    predictions = PredictionRepository(mock_db)

    aggregates.insert_aggregate(
        window_start=now - timedelta(seconds=10),
        window_end=now,
        features={"flow_rate": 12.0, "congestion_score": 0.4},
    )
    predictions.insert_prediction(
        label="low",
        probability=0.82,
        model_version="rf-v0",
    )

    assert aggregates.count() == 1
    assert predictions.latest(limit=1)[0]["label"] == "low"


def test_system_health_upsert(mock_db) -> None:
    repo = SystemHealthRepository(mock_db)
    repo.upsert_heartbeat(component="vision_worker", status="ok", metrics={"fps": 14.2})
    repo.upsert_heartbeat(component="vision_worker", status="degraded", metrics={"fps": 5.0})

    rows = repo.get_all()
    assert len(rows) == 1
    assert rows[0]["status"] == "degraded"
    assert rows[0]["metrics"]["fps"] == 5.0


def test_build_repositories_and_indexes(mock_db) -> None:
    repos = build_repositories(mock_db)
    assert set(repos) == {
        "detections",
        "signal_states",
        "aggregates",
        "predictions",
        "system_health",
    }
    ensure_indexes(mock_db)
    # mongomock supports create_index; smoke that detections still works
    repos["detections"].insert_counts(counts={"car": 1})
    assert repos["detections"].count() == 1
