"""Serial readers for live Arduino or software mock."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from arduino.mock import MockTrafficLight
from arduino.protocol import ProtocolError, SignalMessage, parse_signal_line
from utils import get_logger

logger = get_logger("arduino.reader")


class SignalReader(ABC):
    """Common interface for mock and hardware signal sources."""

    @abstractmethod
    def open(self) -> None:
        """Open the underlying source."""

    @abstractmethod
    def close(self) -> None:
        """Release resources."""

    @abstractmethod
    def read_message(self) -> SignalMessage | None:
        """
        Read one signal message.

        Returns ``None`` when no data is available yet (non-blocking hardware).
        """

    def __enter__(self) -> SignalReader:
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class MockSignalReader(SignalReader):
    """Reads synthetic R/Y/G timing messages without hardware."""

    def __init__(self, mock: MockTrafficLight | None = None) -> None:
        self._mock = mock or MockTrafficLight()
        self._opened = False

    def open(self) -> None:
        self._opened = True
        logger.info("Mock signal reader opened")

    def close(self) -> None:
        self._opened = False
        logger.info("Mock signal reader closed")

    def read_message(self) -> SignalMessage | None:
        if not self._opened:
            raise RuntimeError("MockSignalReader is not open")
        return self._mock.read_message()


class SerialSignalReader(SignalReader):
    """
    Reads lines from a real Arduino over USB serial.

    Requires ``pyserial``. Reconnects after disconnect using ``reconnect_delay_s``.
    """

    def __init__(
        self,
        port: str,
        *,
        baud_rate: int = 9600,
        reconnect_delay_s: float = 2.0,
        timeout_s: float = 1.0,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.reconnect_delay_s = reconnect_delay_s
        self.timeout_s = timeout_s
        self._serial: Any | None = None

    def open(self) -> None:
        self._connect()

    def close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:  # noqa: BLE001 - best-effort close
                logger.exception("Error while closing serial port %s", self.port)
            self._serial = None
            logger.info("Serial port %s closed", self.port)

    def read_message(self) -> SignalMessage | None:
        if self._serial is None or not getattr(self._serial, "is_open", False):
            self._reconnect()
            return None

        try:
            raw = self._serial.readline()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Serial read failed on %s: %s", self.port, exc)
            self._reconnect()
            return None

        if not raw:
            return None

        try:
            line = raw.decode("utf-8", errors="replace").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Serial decode failed: %s", exc)
            return None

        if not line:
            return None

        try:
            return parse_signal_line(line)
        except ProtocolError as exc:
            logger.warning("Ignoring bad serial line: %s", exc)
            return None

    def _connect(self) -> None:
        try:
            import serial  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is required for SerialSignalReader. "
                "pip install pyserial, or keep ARDUINO_MOCK_ENABLED=true."
            ) from exc

        self.close()
        self._serial = serial.Serial(
            self.port,
            self.baud_rate,
            timeout=self.timeout_s,
        )
        logger.info("Opened serial port %s @ %s", self.port, self.baud_rate)

    def _reconnect(self) -> None:
        logger.warning(
            "Reconnecting to %s in %.1fs",
            self.port,
            self.reconnect_delay_s,
        )
        self.close()
        time.sleep(self.reconnect_delay_s)
        try:
            self._connect()
        except Exception as exc:  # noqa: BLE001
            logger.error("Reconnect to %s failed: %s", self.port, exc)


def build_signal_reader(
    *,
    mock_enabled: bool = True,
    port: str = "COM3",
    baud_rate: int = 9600,
    reconnect_delay_s: float = 2.0,
    mock: MockTrafficLight | None = None,
) -> SignalReader:
    """Factory: mock reader when hardware is not connected."""
    if mock_enabled:
        return MockSignalReader(mock=mock)
    return SerialSignalReader(
        port,
        baud_rate=baud_rate,
        reconnect_delay_s=reconnect_delay_s,
    )
