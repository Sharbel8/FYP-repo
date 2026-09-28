"""Unit tests for Arduino protocol, mock light, and worker."""

from __future__ import annotations

import pytest
from mongomock import MongoClient as MockMongoClient

from arduino import (
    MockSignalReader,
    MockTrafficLight,
    ProtocolError,
    SignalWorker,
    format_signal_line,
    parse_signal_line,
)
from database import SignalStateRepository, SystemHealthRepository, ensure_indexes


def test_parse_csv_and_json_lines() -> None:
    csv_msg = parse_signal_line("STATE:RED,ELAPSED:12.5,RED:45,YELLOW:3,GREEN:30")
    assert csv_msg.state == "RED"
    assert csv_msg.elapsed_s == 12.5
    assert csv_msg.durations["GREEN"] == 30.0

    json_msg = parse_signal_line(
        '{"state":"GREEN","elapsed_s":4,"durations":{"RED":40,"YELLOW":3,"GREEN":25}}'
    )
    assert json_msg.state == "GREEN"
    assert json_msg.elapsed_s == 4.0


def test_parse_rejects_empty() -> None:
    with pytest.raises(ProtocolError):
        parse_signal_line("   ")


def test_format_roundtrip() -> None:
    line = format_signal_line("yellow", 2.0, {"RED": 1, "YELLOW": 2, "GREEN": 3})
    parsed = parse_signal_line(line)
    assert parsed.state == "YELLOW"
    assert parsed.elapsed_s == 2.0


def test_mock_light_advances_with_fake_clock() -> None:
    clock = {"t": 0.0}

    def time_fn() -> float:
        return clock["t"]

    mock = MockTrafficLight(
        phase_seconds={"GREEN": 5, "YELLOW": 2, "RED": 4},
        start_state="GREEN",
        time_fn=time_fn,
    )
    assert mock.read_message().state == "GREEN"
    clock["t"] = 5.5
    assert mock.read_message().state == "YELLOW"
    clock["t"] = 8.0
    assert mock.read_message().state == "RED"


def test_signal_worker_writes_to_mongo() -> None:
    db = MockMongoClient()["traffic_test"]
    ensure_indexes(db)
    signals = SignalStateRepository(db)
    health = SystemHealthRepository(db)

    clock = {"t": 0.0}
    mock = MockTrafficLight(
        phase_seconds={"GREEN": 10, "YELLOW": 2, "RED": 10},
        start_state="GREEN",
        time_fn=lambda: clock["t"],
    )
    reader = MockSignalReader(mock)
    worker = SignalWorker(
        reader,
        signals,
        health_repo=health,
        publish_interval_s=0.01,
        source="mock",
    )

    written = worker.run(max_iterations=3)
    assert written == 3
    assert signals.count() == 3
    assert health.get_all()[0]["component"] == "arduino_worker"
    assert signals.latest(limit=1)[0]["state"] == "GREEN"
