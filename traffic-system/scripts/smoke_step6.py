"""Step 6 smoke test: mock Arduino signal worker → MongoDB."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arduino import MockTrafficLight, MockSignalReader, SignalWorker
from config import get_settings
from database import (
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
    settings = get_settings()
    setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    logger = get_logger("smoke_step6")

    try:
        ping()
    except MongoConnectionError as exc:
        logger.error("%s", exc)
        return 1

    db = get_database()
    ensure_indexes(db)

    mock = MockTrafficLight(
        phase_seconds={"RED": 8.0, "YELLOW": 2.0, "GREEN": 6.0},
        start_state="GREEN",
    )
    reader = MockSignalReader(mock)
    worker = SignalWorker(
        reader,
        SignalStateRepository(db),
        health_repo=SystemHealthRepository(db),
        publish_interval_s=0.5,
        source="mock",
    )

    written = worker.run(max_iterations=5)
    latest = SignalStateRepository(db).latest(limit=3)
    logger.info("Wrote %s signal documents", written)
    for row in latest:
        logger.info(
            "state=%s elapsed=%.1f durations=%s",
            row.get("state"),
            row.get("elapsed_s"),
            row.get("durations"),
        )

    close_client()
    logger.info("Step 6 smoke test OK")
    return 0 if written > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
