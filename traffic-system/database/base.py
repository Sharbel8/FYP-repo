"""Base repository helpers for MongoDB collections."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from utils import get_logger


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class BaseRepository:
    """
    Thin CRUD wrapper around a MongoDB collection.

    Subclasses set ``collection_name`` and may add domain-specific methods.
    """

    collection_name: str = ""

    def __init__(self, database: Database) -> None:
        if not self.collection_name:
            raise ValueError(f"{type(self).__name__} must define collection_name")
        self._db = database
        self._collection: Collection = database[self.collection_name]
        self._logger = get_logger(f"database.{self.collection_name}")

    @property
    def collection(self) -> Collection:
        """Expose the underlying PyMongo collection."""
        return self._collection

    def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        """Insert a single document, adding ``created_at`` when missing."""
        payload = dict(document)
        payload.setdefault("created_at", utc_now())
        result = self._collection.insert_one(payload)
        self._logger.debug("Inserted document id=%s", result.inserted_id)
        return result

    def find_one(self, query: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Return one matching document, or ``None``."""
        return self._collection.find_one(query or {})

    def find_many(
        self,
        query: dict[str, Any] | None = None,
        *,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return matching documents.

        Args:
            query: MongoDB filter.
            limit: Maximum documents to return.
            sort: Optional list of (field, direction) pairs.
        """
        cursor = self._collection.find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> UpdateResult:
        """Update a single document matching ``query``."""
        payload = dict(update)
        if "$set" in payload:
            payload["$set"] = dict(payload["$set"])
            payload["$set"].setdefault("updated_at", utc_now())
        return self._collection.update_one(query, payload, upsert=upsert)

    def delete_many(self, query: dict[str, Any]) -> DeleteResult:
        """Delete all documents matching ``query``."""
        result = self._collection.delete_many(query)
        self._logger.debug("Deleted %s documents", result.deleted_count)
        return result

    def count(self, query: dict[str, Any] | None = None) -> int:
        """Count documents matching ``query``."""
        return self._collection.count_documents(query or {})
