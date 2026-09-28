"""Tests for congestion model training and prediction persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mongomock import MongoClient as MockMongoClient

from database import AggregateRepository, PredictionRepository
from ml import CongestionPredictor, CongestionTrainer, ModelTrainingError, PredictionService


def _features(index: int, label: str) -> dict[str, float | str]:
    return {"vehicle_count": float(index + 1), "pedestrian_count": 1.0, "flow_rate_per_min": float((index + 1) * 6), "vehicle_density": (index + 1) / 20, "red_duration_s": 30.0, "yellow_duration_s": 3.0, "green_duration_s": 25.0, "current_state_code": 0.0, "waiting_time_proxy": float(index), "congestion_score": index / 20, "congestion_label": label}


def _documents() -> list[dict]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    labels = ["low", "medium", "high"] * 4
    return [{"window_end": start + timedelta(minutes=index), "features": _features(index, label)} for index, label in enumerate(labels)]


def test_trains_loads_and_predicts(tmp_path) -> None:
    path = tmp_path / "congestion.joblib"
    result = CongestionTrainer(min_samples=8).train_from_documents(_documents(), path)
    predictor = CongestionPredictor(path)
    label, probability = predictor.predict(_documents()[-1]["features"])
    assert result.model_path == path and result.samples == 11
    assert label in {"low", "medium", "high"} and 0 <= probability <= 1


def test_training_rejects_insufficient_data(tmp_path) -> None:
    try:
        CongestionTrainer(min_samples=8).train_from_documents(_documents()[:4], tmp_path / "model.joblib")
    except ModelTrainingError as exc:
        assert "Need at least" in str(exc)
    else:
        raise AssertionError("Expected ModelTrainingError")


def test_prediction_service_uses_latest_aggregate(tmp_path) -> None:
    path = tmp_path / "congestion.joblib"
    documents = _documents()
    CongestionTrainer(min_samples=8).train_from_documents(documents, path)
    db = MockMongoClient()["traffic_test"]
    aggregates, predictions = AggregateRepository(db), PredictionRepository(db)
    for item in documents:
        aggregates.insert_aggregate(window_start=item["window_end"] - timedelta(seconds=10), window_end=item["window_end"], features=item["features"])
    identifier = PredictionService(CongestionPredictor(path), aggregates, predictions).predict_latest()
    assert identifier and predictions.latest(limit=1)[0]["features_ref"]["lane_id"] == "default"
