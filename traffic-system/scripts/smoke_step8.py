"""Step 8 smoke test: train a model and store one prediction from MongoDB aggregates."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings
from database import AggregateRepository, PredictionRepository, get_database
from ml import CongestionPredictor, CongestionTrainer, PredictionService
from utils import get_logger, setup_logging

def main() -> int:
    parser = argparse.ArgumentParser(description="Train congestion model from MongoDB aggregates")
    parser.add_argument("--model", choices=["random_forest", "xgboost", "lightgbm"], default="random_forest")
    args = parser.parse_args(); settings = get_settings()
    setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    database = get_database(); aggregates, predictions = AggregateRepository(database), PredictionRepository(database)
    rows = list(reversed(aggregates.latest(limit=10000)))
    result = CongestionTrainer(model_kind=args.model).train_from_documents(rows, settings.ml.model_path)
    prediction_id = PredictionService(CongestionPredictor(result.model_path), aggregates, predictions).predict_latest()
    get_logger("smoke_step8").info("Step 8 OK model=%s prediction=%s", result.model_version, prediction_id)
    return 0

if __name__ == "__main__": raise SystemExit(main())
