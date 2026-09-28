"""Train congestion classifiers from Step 7 aggregate windows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler

from utils import get_logger

logger = get_logger("ml.training")

FEATURE_COLUMNS = (
    "vehicle_count", "pedestrian_count", "flow_rate_per_min", "vehicle_density",
    "red_duration_s", "yellow_duration_s", "green_duration_s", "current_state_code",
    "waiting_time_proxy", "congestion_score",
)


class ModelTrainingError(RuntimeError):
    """Raised when aggregate data cannot produce a valid congestion model."""


@dataclass(frozen=True)
class TrainingResult:
    """Information about a saved congestion-model artifact."""

    model_path: Path
    model_version: str
    samples: int
    classes: tuple[str, ...]
    training_accuracy: float


class CongestionTrainer:
    """Train a selected classifier to predict the next aggregate label."""

    def __init__(self, *, model_kind: str = "random_forest", random_state: int = 42, min_samples: int = 8) -> None:
        if min_samples < 3:
            raise ValueError("min_samples must be at least 3")
        if model_kind not in {"random_forest", "xgboost", "lightgbm"}:
            raise ValueError("model_kind must be random_forest, xgboost, or lightgbm")
        self.model_kind, self.random_state = model_kind, random_state
        self.min_samples = min_samples

    def train_from_documents(self, documents: list[dict[str, Any]], model_path: str | Path) -> TrainingResult:
        """Train and save a model from chronologically ordered Mongo aggregates.

        The label is shifted one window forward, so the model learns to forecast
        short-term congestion instead of repeating the current derived label.
        """
        frame = self._to_training_frame(documents)
        if len(frame) < self.min_samples:
            raise ModelTrainingError(f"Need at least {self.min_samples} aggregate windows; found {len(frame)}")
        targets = frame["next_congestion_label"]
        if targets.nunique() < 2:
            raise ModelTrainingError("Training data needs at least two congestion labels")

        label_encoder = LabelEncoder()
        encoded_targets = label_encoder.fit_transform(targets)
        pipeline = Pipeline([("scale", StandardScaler()), ("classifier", self._build_classifier())])
        features = frame.loc[:, FEATURE_COLUMNS]
        pipeline.fit(features, encoded_targets)
        accuracy = float(pipeline.score(features, encoded_targets))
        version = f"{self.model_kind}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        artifact = {"model": pipeline, "label_encoder": label_encoder, "feature_columns": FEATURE_COLUMNS, "model_version": version, "trained_at": datetime.now(timezone.utc).isoformat()}
        destination = Path(model_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(artifact, destination)
        classes = tuple(str(item) for item in label_encoder.classes_)
        logger.info("Saved congestion model path=%s samples=%s accuracy=%.3f", destination, len(frame), accuracy)
        return TrainingResult(destination, version, len(frame), classes, accuracy)

    def _build_classifier(self) -> Any:
        if self.model_kind == "random_forest":
            return RandomForestClassifier(n_estimators=200, random_state=self.random_state, class_weight="balanced")
        if self.model_kind == "xgboost":
            from xgboost import XGBClassifier
            return XGBClassifier(n_estimators=150, random_state=self.random_state, eval_metric="mlogloss")
        from lightgbm import LGBMClassifier
        return LGBMClassifier(n_estimators=150, random_state=self.random_state, verbosity=-1)

    def _to_training_frame(self, documents: list[dict[str, Any]]) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for document in documents:
            features = document.get("features")
            if not isinstance(features, dict) or any(field not in features for field in FEATURE_COLUMNS):
                continue
            row = {field: float(features[field]) for field in FEATURE_COLUMNS}
            row["congestion_label"] = str(features.get("congestion_label", ""))
            row["window_end"] = document.get("window_end")
            rows.append(row)
        if not rows:
            raise ModelTrainingError("No complete aggregate feature documents found")
        frame = pd.DataFrame(rows).sort_values("window_end", kind="stable").reset_index(drop=True)
        frame["next_congestion_label"] = frame["congestion_label"].shift(-1)
        return frame.iloc[:-1].dropna(subset=["next_congestion_label"])
