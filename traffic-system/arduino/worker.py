"""Persist Arduino / mock signal states into MongoDB."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from arduino.reader import SignalReader
from database import SignalStateRepository, SystemHealthRepository
from utils import get_logger

logger = get_logger("arduino.worker")


class SignalWorker:
    """
    Poll a ``SignalReader`` and write states to MongoDB.

    Designed for a long-running process (mock or real Arduino).
    """

    def __init__(
        self,
        reader: SignalReader,
        signal_repo: SignalStateRepository,
        *,
        health_repo: SystemHealthRepository | None = None,
        publish_interval_s: float = 1.0,
        source: str = "mock",
    ) -> None:
        if publish_interval_s <= 0:
            raise ValueError("publish_interval_s must be positive")
        self.reader = reader
        self.signal_repo = signal_repo
        self.health_repo = health_repo
        self.publish_interval_s = publish_interval_s
        self.source = source
        self._running = False
        self._messages_written = 0

    def run_once(self, *, timestamp: datetime | None = None) -> str | None:
        """Read one message and persist it. Returns inserted id or ``None``."""
        message = self.reader.read_message()
        if message is None:
            return None

        doc_id = self.signal_repo.insert_state(
            state=message.state,
            elapsed_s=message.elapsed_s,
            durations=message.durations,
            timestamp=timestamp or datetime.now(timezone.utc),
            source=self.source,
        )
        self._messages_written += 1
        logger.info(
            "Stored signal state=%s elapsed=%.1fs id=%s",
            message.state,
            message.elapsed_s,
            doc_id,
        )

        if self.health_repo is not None:
            self.health_repo.upsert_heartbeat(
                component="arduino_worker",
                status="ok",
                metrics={
                    "messages_written": self._messages_written,
                    "state": message.state,
                    "elapsed_s": message.elapsed_s,
                },
                message=f"source={self.source}",
            )
        return doc_id

    def run(self, *, max_iterations: int | None = None) -> int:
        """
        Poll until stopped or ``max_iterations`` is reached.

        Returns the number of documents written.
        """
        self._running = True
        iterations = 0
        self.reader.open()
        try:
            while self._running:
                self.run_once()
                iterations += 1
                if max_iterations is not None and iterations >= max_iterations:
                    break
                time.sleep(self.publish_interval_s)
        finally:
            self._running = False
            self.reader.close()
        return self._messages_written

    def stop(self) -> None:
        """Request a graceful stop of ``run()``."""
        self._running = False
