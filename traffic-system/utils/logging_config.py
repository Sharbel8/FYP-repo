"""Centralized logging configuration for the traffic system."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_dir: str | Path = "logs",
    logger_name: str = "traffic_system",
    *,
    console: bool = True,
    log_file: str = "traffic_system.log",
) -> logging.Logger:
    """
    Configure application-wide logging to console and an optional rotating file.

    Safe to call multiple times: handlers are not duplicated for the same logger.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory where log files are written.
        logger_name: Root logger name for this application.
        console: Whether to emit logs to stderr.
        log_file: Filename inside ``log_dir``.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(logger_name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    if logger.handlers:
        logger.setLevel(numeric_level)
        return logger

    formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    if console:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(numeric_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(directory / log_file, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    logger.debug("Logging initialised (level=%s, dir=%s)", level.upper(), directory)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a child logger under the application root logger.

    Prefer this over ``print()`` in all modules.
    """
    if name is None:
        return logging.getLogger("traffic_system")
    if name.startswith("traffic_system"):
        return logging.getLogger(name)
    return logging.getLogger(f"traffic_system.{name}")
