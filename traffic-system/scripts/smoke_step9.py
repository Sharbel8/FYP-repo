"""Step 9 smoke test: verify dashboard data can be read from MongoDB."""

from __future__ import annotations
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0, str(PROJECT_ROOT))

from dashboard import DashboardDataService
from database import AggregateRepository, DetectionRepository, PredictionRepository, SignalStateRepository, get_database
from utils import get_logger, setup_logging
from config import get_settings

def main() -> int:
    settings = get_settings(); setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    database = get_database()
    service = DashboardDataService(DetectionRepository(database), SignalStateRepository(database), AggregateRepository(database), PredictionRepository(database))
    snapshot, history = service.latest_snapshot(), service.aggregate_history()
    get_logger("smoke_step9").info("Step 9 OK snapshot_keys=%s aggregate_rows=%s", list(snapshot), len(history))
    return 0

if __name__ == "__main__": raise SystemExit(main())
