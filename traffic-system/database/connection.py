"""MongoDB connection management."""

from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import get_settings
from utils import get_logger

logger = get_logger("database.connection")

_client: MongoClient | None = None


class MongoConnectionError(RuntimeError):
    """Raised when MongoDB cannot be reached or initialised."""


def get_client(
    uri: str | None = None,
    *,
    server_selection_timeout_ms: int = 5000,
) -> MongoClient:
    """
    Return a shared MongoClient instance.

    Args:
        uri: Optional MongoDB URI. Defaults to configured ``MONGO_URI``.
        server_selection_timeout_ms: How long to wait when selecting a server.

    Returns:
        Connected ``MongoClient``.

    Raises:
        MongoConnectionError: If the server cannot be reached.
    """
    global _client

    settings = get_settings()
    resolved_uri = uri or settings.database.uri

    if _client is not None:
        return _client

    try:
        client = MongoClient(
            resolved_uri,
            serverSelectionTimeoutMS=server_selection_timeout_ms,
        )
        # Force an immediate round-trip so failures surface early.
        client.admin.command("ping")
    except (ConnectionFailure, ServerSelectionTimeoutError, OSError) as exc:
        logger.error("Failed to connect to MongoDB at %s: %s", resolved_uri, exc)
        raise MongoConnectionError(
            f"Cannot connect to MongoDB at {resolved_uri}. "
            "Is mongod running?"
        ) from exc

    _client = client
    logger.info("Connected to MongoDB (%s)", resolved_uri)
    return _client


def get_database(
    name: str | None = None,
    *,
    client: MongoClient | None = None,
) -> Database:
    """
    Return the application database handle.

    Args:
        name: Optional database name. Defaults to configured name.
        client: Optional existing client (useful in tests).
    """
    settings = get_settings()
    active_client = client or get_client()
    db_name = name or settings.database.name
    return active_client[db_name]


def close_client() -> None:
    """Close the shared MongoClient if it exists."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB client closed")


def ping(client: MongoClient | None = None) -> dict[str, Any]:
    """
    Ping MongoDB and return the server response document.

    Raises:
        MongoConnectionError: If the ping fails.
    """
    active = client or get_client()
    try:
        return dict(active.admin.command("ping"))
    except (ConnectionFailure, ServerSelectionTimeoutError, OSError) as exc:
        raise MongoConnectionError("MongoDB ping failed") from exc
