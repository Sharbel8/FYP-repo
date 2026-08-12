"""Step 1 smoke test: load settings and emit a log line."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_settings
from utils import get_logger, setup_logging


def main() -> None:
    """Load configuration and write a sample log entry."""
    settings = get_settings()
    logger = setup_logging(
        level=settings.app.log_level,
        log_dir=settings.app.log_dir,
    )
    module_logger = get_logger("smoke_step1")

    module_logger.info("App: %s", settings.app.name)
    module_logger.info("Environment: %s", settings.app.environment)
    module_logger.info("MongoDB: %s / %s", settings.database.uri, settings.database.name)
    module_logger.info("Camera source: %s", settings.camera.source)
    module_logger.info(
        "Arduino: port=%s mock=%s",
        settings.arduino.port,
        settings.arduino.mock_enabled,
    )
    module_logger.info("Step 1 smoke test OK")


if __name__ == "__main__":
    main()
