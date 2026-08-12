"""Tests for logging setup."""

from __future__ import annotations

import logging
from pathlib import Path

from utils.logging_config import get_logger, setup_logging


def test_setup_logging_creates_file(tmp_path: Path) -> None:
    """setup_logging should create a log file and accept messages."""
    # Use a unique logger name so handlers from other tests do not interfere.
    logger = setup_logging(
        level="DEBUG",
        log_dir=tmp_path,
        logger_name="traffic_system_test_logging",
        log_file="test.log",
    )
    logger.info("hello from step 1")

    log_path = tmp_path / "test.log"
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "hello from step 1" in content

    # Cleanup handlers to avoid leaks across tests
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def test_get_logger_namespaced() -> None:
    """get_logger should nest under the traffic_system namespace."""
    logger = get_logger("config")
    assert logger.name == "traffic_system.config"
    assert isinstance(logger, logging.Logger)
