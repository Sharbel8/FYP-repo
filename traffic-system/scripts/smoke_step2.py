"""Step 2 smoke test: connect to live MongoDB and exercise repositories."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings
from database import (
    DetectionRepository,
    MongoConnectionError,
    SignalStateRepository,
    SystemHealthRepository,
    close_client,
    ensure_indexes,
    get_database,
    ping,
)
from utils import get_logger, setup_logging


def main() -> int:
    """Ping MongoDB, ensure indexes, insert sample docs, then clean them up."""
    settings = get_settings()
    setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    logger = get_logger("smoke_step2")

    try:
        response = ping()
        logger.info("MongoDB ping OK: %s", response)
    except MongoConnectionError as exc:
        logger.error("%s", exc)
        logger.error(
            "Install and start MongoDB Community, or set MONGO_URI in .env. "
            "Unit tests still pass with mongomock without a live server."
        )
        return 1

    db = get_database()
    ensure_indexes(db)

    detections = DetectionRepository(db)
    signals = SignalStateRepository(db)
    health = SystemHealthRepository(db)

    det_id = detections.insert_counts(
        counts={"car": 4, "bus": 1, "person": 2},
        lane_id="smoke_lane",
        source="smoke_step2",
    )
    sig_id = signals.insert_state(
        state="GREEN",
        elapsed_s=8.0,
        durations={"RED": 40.0, "YELLOW": 3.0, "GREEN": 25.0},
        source="smoke_step2",
    )
    health.upsert_heartbeat(
        component="smoke_step2",
        status="ok",
        metrics={"inserted_detections": 1},
        message="Step 2 smoke test",
    )

    logger.info("Inserted detection id=%s", det_id)
    logger.info("Inserted signal state id=%s", sig_id)
    logger.info("Latest detection: %s", detections.latest(lane_id="smoke_lane", limit=1)[0]["counts"])
    logger.info("Health: %s", health.get_all())

    # Cleanup smoke documents so the DB stays tidy
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    detections.delete_many({"source": "smoke_step2", "created_at": {"$gte": cutoff}})
    signals.delete_many({"source": "smoke_step2", "created_at": {"$gte": cutoff}})
    health.delete_many({"component": "smoke_step2"})

    close_client()
    logger.info("Step 2 smoke test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
