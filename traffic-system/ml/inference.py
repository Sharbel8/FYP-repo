"""Load a saved congestion model and persist predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from database import AggregateRepository, PredictionRepository
from ml.training import FEATURE_COLUMNS
from utils import get_logger

logger = get_logger("ml.inference")


class CongestionPredictor:
    """Predict the next congestion label from one aggregate's features."""

    def __init__(self, model_path: str | Path) -> None:
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file does not exist: {path}")
        artifact = joblib.load(path)
        self.model = artifact["model"]
        self.label_encoder = artifact["label_encoder"]
        self.feature_columns = tuple(artifact["feature_columns"])
        self.model_version = str(artifact["model_version"])

    def predict(self, features: dict[str, Any]) -> tuple[str, float]:
        """Return ``(label, probability)`` for one feature dictionary."""
        missing = [field for field in self.feature_columns if field not in features]
        if missing:
            raise ValueError(f"Aggregate is missing model features: {', '.join(missing)}")
        frame = pd.DataFrame([{field: float(features[field]) for field in self.feature_columns}])
        encoded_label = int(self.model.predict(frame)[0])
        label = str(self.label_encoder.inverse_transform([encoded_label])[0])
        probabilities = self.model.predict_proba(frame)[0]
        class_index = list(self.model.classes_).index(encoded_label)
        return label, float(probabilities[class_index])


class PredictionService:
    """Read the latest aggregate, predict it, and store the output in MongoDB."""

    def __init__(self, predictor: CongestionPredictor, aggregates: AggregateRepository, predictions: PredictionRepository, *, lane_id: str = "default") -> None:
        self.predictor, self.aggregates, self.predictions, self.lane_id = predictor, aggregates, predictions, lane_id

    def predict_latest(self) -> str:
        """Persist a prediction using the most recent aggregate for this lane."""
        rows = self.aggregates.latest(lane_id=self.lane_id, limit=1)
        if not rows:
            raise ValueError(f"No aggregate available for lane '{self.lane_id}'")
        aggregate = rows[0]
        label, probability = self.predictor.predict(aggregate["features"])
        identifier = self.predictions.insert_prediction(label=label, probability=probability, model_version=self.predictor.model_version, features_ref={"aggregate_id": str(aggregate.get("_id")), "window_end": aggregate.get("window_end"), "lane_id": self.lane_id})
        logger.info("Stored prediction id=%s label=%s probability=%.3f", identifier, label, probability)
        return identifier
