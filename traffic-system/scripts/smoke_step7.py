"""Step 7 smoke test: build feature aggregates from MongoDB data."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings
from database import (
    AggregateRepository,
    DetectionRepository,
    MongoConnectionError,
    SignalStateRepository,
    close_client,
    ensure_indexes,
    get_database,
    ping,
)
from preprocessing import FeatureAggregator
from utils import get_logger, setup_logging


def main() -> int:
    settings = get_settings()
    setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    logger = get_logger("smoke_step7")

    try:
        ping()
    except MongoConnectionError as exc:
        logger.error("%s", exc)
        return 1

    db = get_database()
    ensure_indexes(db)
    detections = DetectionRepository(db)
    signals = SignalStateRepository(db)
    aggregates = AggregateRepository(db)

    now = datetime.now(timezone.utc)
    detections.insert_counts(
        timestamp=now - timedelta(seconds=4),
        counts={"car": 6, "truck": 1, "person": 3},
        lane_id="default",
        source="smoke_step7",
    )
    signals.insert_state(
        state="RED",
        elapsed_s=15,
        durations={"RED": 40.0, "YELLOW": 3.0, "GREEN": 25.0},
        timestamp=now - timedelta(seconds=2),
        source="smoke_step7",
    )

    aggregator = FeatureAggregator(
        detections,
        signals,
        aggregates,
        window_seconds=settings.aggregation.window_seconds,
        lane_id="default",
    )
    doc_id = aggregator.persist_window(window_end=now)
    row = aggregates.latest(limit=1)[0]
    logger.info("Aggregate id=%s", doc_id)
    logger.info("Features: %s", row.get("features"))

    close_client()
    logger.info("Step 7 smoke test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
