"""Arduino serial line protocol for traffic-light state messages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


VALID_STATES = frozenset({"RED", "YELLOW", "GREEN"})

# Example: STATE:RED,ELAPSED:12.5,RED:45,YELLOW:3,GREEN:30
_CSV_PATTERN = re.compile(
    r"STATE:(?P<state>RED|YELLOW|GREEN)"
    r"(?:,ELAPSED:(?P<elapsed>[0-9]+(?:\.[0-9]+)?))?"
    r"(?:,RED:(?P<red>[0-9]+(?:\.[0-9]+)?))?"
    r"(?:,YELLOW:(?P<yellow>[0-9]+(?:\.[0-9]+)?))?"
    r"(?:,GREEN:(?P<green>[0-9]+(?:\.[0-9]+)?))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SignalMessage:
    """Parsed traffic-light state message from Arduino or mock."""

    state: str
    elapsed_s: float
    durations: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging or debugging."""
        return {
            "state": self.state,
            "elapsed_s": self.elapsed_s,
            "durations": dict(self.durations),
        }


class ProtocolError(ValueError):
    """Raised when a serial line cannot be parsed."""


def parse_signal_line(line: str) -> SignalMessage:
    """
    Parse one serial line into a ``SignalMessage``.

    Accepted formats:
    - JSON: ``{"state":"RED","elapsed_s":12,"durations":{"RED":45,"YELLOW":3,"GREEN":30}}``
    - CSV-like: ``STATE:RED,ELAPSED:12,RED:45,YELLOW:3,GREEN:30``
    """
    text = (line or "").strip()
    if not text:
        raise ProtocolError("Empty serial line")

    if text.startswith("{"):
        return _parse_json(text)
    return _parse_csv(text)


def format_signal_line(
    state: str,
    elapsed_s: float,
    durations: dict[str, float] | None = None,
) -> str:
    """Format a message in the CSV-like wire format used by the mock and firmware."""
    durations = durations or {}
    parts = [
        f"STATE:{state.upper()}",
        f"ELAPSED:{float(elapsed_s):.1f}",
        f"RED:{float(durations.get('RED', 0.0)):.1f}",
        f"YELLOW:{float(durations.get('YELLOW', 0.0)):.1f}",
        f"GREEN:{float(durations.get('GREEN', 0.0)):.1f}",
    ]
    return ",".join(parts)


def _parse_json(text: str) -> SignalMessage:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON signal line: {text!r}") from exc

    if not isinstance(payload, dict):
        raise ProtocolError("JSON signal line must be an object")

    state = str(payload.get("state", "")).upper()
    if state not in VALID_STATES:
        raise ProtocolError(f"Invalid state: {state!r}")

    elapsed = float(payload.get("elapsed_s", payload.get("elapsed", 0.0)))
    raw_durations = payload.get("durations") or {}
    if not isinstance(raw_durations, dict):
        raise ProtocolError("durations must be an object")

    durations = {
        "RED": float(raw_durations.get("RED", raw_durations.get("red", 0.0))),
        "YELLOW": float(raw_durations.get("YELLOW", raw_durations.get("yellow", 0.0))),
        "GREEN": float(raw_durations.get("GREEN", raw_durations.get("green", 0.0))),
    }
    return SignalMessage(state=state, elapsed_s=elapsed, durations=durations)


def _parse_csv(text: str) -> SignalMessage:
    match = _CSV_PATTERN.fullmatch(text.replace(" ", ""))
    if not match:
        raise ProtocolError(f"Unrecognized signal line: {text!r}")

    state = match.group("state").upper()
    elapsed = float(match.group("elapsed") or 0.0)
    durations = {
        "RED": float(match.group("red") or 0.0),
        "YELLOW": float(match.group("yellow") or 0.0),
        "GREEN": float(match.group("green") or 0.0),
    }
    return SignalMessage(state=state, elapsed_s=elapsed, durations=durations)
