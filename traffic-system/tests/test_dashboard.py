"""Tests for the dashboard's read-only MongoDB data adapter."""

from __future__ import annotations

from datetime import datetime, timezone

from mongomock import MongoClient as MockMongoClient

from dashboard import DashboardDataService
from database import AggregateRepository, DetectionRepository, PredictionRepository, SignalStateRepository


def test_dashboard_adapter_returns_snapshot_and_history() -> None:
    db = MockMongoClient()["traffic_test"]
    detections, signals = DetectionRepository(db), SignalStateRepository(db)
    aggregates, predictions = AggregateRepository(db), PredictionRepository(db)
    now = datetime.now(timezone.utc)
    detections.insert_counts(counts={"car": 3, "person": 1})
    signals.insert_state(state="GREEN", elapsed_s=4)
    aggregates.insert_aggregate(window_start=now, window_end=now, features={"vehicle_count": 3, "flow_rate_per_min": 18, "congestion_score": .2})
    predictions.insert_prediction(label="low", probability=.8, model_version="test")
    service = DashboardDataService(detections, signals, aggregates, predictions)
    assert service.latest_snapshot()["prediction"]["label"] == "low"
    history = service.aggregate_history()
    assert len(history) == 1 and history.iloc[0]["vehicle_count"] == 3
