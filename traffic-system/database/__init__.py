"""MongoDB persistence package."""

from database.connection import (
    MongoConnectionError,
    close_client,
    get_client,
    get_database,
    ping,
)
from database.indexes import ensure_indexes
from database.repositories import (
    AggregateRepository,
    DetectionRepository,
    PredictionRepository,
    SignalStateRepository,
    SystemHealthRepository,
    build_repositories,
)

__all__ = [
    "AggregateRepository",
    "DetectionRepository",
    "MongoConnectionError",
    "PredictionRepository",
    "SignalStateRepository",
    "SystemHealthRepository",
    "build_repositories",
    "close_client",
    "ensure_indexes",
    "get_client",
    "get_database",
    "ping",
]
