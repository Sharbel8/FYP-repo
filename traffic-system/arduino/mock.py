"""Software mock of Arduino traffic-light phase timing."""

from __future__ import annotations

import time
from typing import Iterator

from arduino.protocol import SignalMessage, format_signal_line
from utils import get_logger

logger = get_logger("arduino.mock")

DEFAULT_PHASE_SECONDS = {
    "RED": 30.0,
    "YELLOW": 3.0,
    "GREEN": 25.0,
}

PHASE_ORDER = ("GREEN", "YELLOW", "RED")


class MockTrafficLight:
    """
    Cycles through GREEN → YELLOW → RED and emits the same wire format
    the real Arduino will send over serial.
    """

    def __init__(
        self,
        *,
        phase_seconds: dict[str, float] | None = None,
        start_state: str = "GREEN",
        time_fn=time.monotonic,
    ) -> None:
        self.phase_seconds = {
            key: float(phase_seconds.get(key, DEFAULT_PHASE_SECONDS[key]))
            if phase_seconds
            else DEFAULT_PHASE_SECONDS[key]
            for key in DEFAULT_PHASE_SECONDS
        }
        for key, value in self.phase_seconds.items():
            if value <= 0:
                raise ValueError(f"phase duration for {key} must be positive")

        state = start_state.upper()
        if state not in DEFAULT_PHASE_SECONDS:
            raise ValueError(f"Invalid start_state: {start_state!r}")

        self._time_fn = time_fn
        self._state = state
        self._phase_started_at = self._time_fn()
        self._last_completed = dict(self.phase_seconds)
        logger.info(
            "Mock traffic light started state=%s phases=%s",
            self._state,
            self.phase_seconds,
        )

    @property
    def state(self) -> str:
        """Current light phase."""
        self._advance_if_needed()
        return self._state

    def read_message(self) -> SignalMessage:
        """Return the current signal state as a parsed message."""
        self._advance_if_needed()
        elapsed = max(0.0, self._time_fn() - self._phase_started_at)
        return SignalMessage(
            state=self._state,
            elapsed_s=elapsed,
            durations=dict(self._last_completed),
        )

    def read_line(self) -> str:
        """Return the current signal state as a serial wire line."""
        message = self.read_message()
        return format_signal_line(message.state, message.elapsed_s, message.durations)

    def iter_lines(self, *, interval_s: float = 1.0) -> Iterator[str]:
        """
        Yield wire lines forever, sleeping ``interval_s`` between emissions.

        Useful for a long-running mock worker loop.
        """
        if interval_s <= 0:
            raise ValueError("interval_s must be positive")
        while True:
            yield self.read_line()
            time.sleep(interval_s)

    def _advance_if_needed(self) -> None:
        now = self._time_fn()
        while True:
            elapsed = now - self._phase_started_at
            limit = self.phase_seconds[self._state]
            if elapsed < limit:
                return
            self._last_completed[self._state] = limit
            overflow = elapsed - limit
            self._state = self._next_state(self._state)
            self._phase_started_at = now - overflow
            logger.debug("Mock light advanced to %s", self._state)

    @staticmethod
    def _next_state(current: str) -> str:
        index = PHASE_ORDER.index(current)
        return PHASE_ORDER[(index + 1) % len(PHASE_ORDER)]
