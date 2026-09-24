"""Arduino serial communication package (mock + hardware-ready)."""

from arduino.mock import MockTrafficLight
from arduino.protocol import ProtocolError, SignalMessage, format_signal_line, parse_signal_line
from arduino.reader import (
    MockSignalReader,
    SerialSignalReader,
    SignalReader,
    build_signal_reader,
)
from arduino.worker import SignalWorker

__all__ = [
    "MockSignalReader",
    "MockTrafficLight",
    "ProtocolError",
    "SerialSignalReader",
    "SignalMessage",
    "SignalReader",
    "SignalWorker",
    "build_signal_reader",
    "format_signal_line",
    "parse_signal_line",
]
