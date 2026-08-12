"""Index creation for traffic system collections."""

from __future__ import annotations

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from database import collections
from utils import get_logger

logger = get_logger("database.indexes")


def ensure_indexes(database: Database) -> None:
    """
    Create indexes used by queries and dashboards.

    Safe to call repeatedly — MongoDB create_index is idempotent for the
    same key specification.
    """
    database[collections.DETECTIONS].create_index(
        [("timestamp", DESCENDING), ("lane_id", ASCENDING)],
        name="detections_timestamp_lane",
    )
    database[collections.SIGNAL_STATES].create_index(
        [("timestamp", DESCENDING)],
        name="signal_states_timestamp",
    )
    database[collections.SIGNAL_STATES].create_index(
        [("state", ASCENDING), ("timestamp", DESCENDING)],
        name="signal_states_state_timestamp",
    )
    database[collections.AGGREGATES].create_index(
        [("window_end", DESCENDING), ("lane_id", ASCENDING)],
        name="aggregates_window_lane",
    )
    database[collections.PREDICTIONS].create_index(
        [("timestamp", DESCENDING)],
        name="predictions_timestamp",
    )
    database[collections.SYSTEM_HEALTH].create_index(
        [("component", ASCENDING)],
        unique=True,
        name="system_health_component_unique",
    )
    logger.info("MongoDB indexes ensured for database '%s'", database.name)
