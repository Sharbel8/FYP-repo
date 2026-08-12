"""Tests for configuration loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config.settings import get_settings, load_settings


SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.yaml"


def test_load_settings_from_yaml() -> None:
    """Settings YAML should load into typed dataclasses."""
    settings = load_settings(SETTINGS_PATH)
    assert settings.app.name == "Smart Traffic Light System"
    assert settings.detection.model_name == "yolov8n.pt"
    assert "car" in settings.detection.classes
    assert settings.arduino.mock_enabled is True


def test_env_overrides_database_and_arduino(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should override YAML defaults."""
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27018")
    monkeypatch.setenv("MONGO_DB_NAME", "traffic_test")
    monkeypatch.setenv("ARDUINO_PORT", "COM9")
    monkeypatch.setenv("ARDUINO_MOCK_ENABLED", "false")
    monkeypatch.setenv("CAMERA_SOURCE", "1")

    get_settings.cache_clear()
    settings = load_settings(SETTINGS_PATH)

    assert settings.database.uri == "mongodb://localhost:27018"
    assert settings.database.name == "traffic_test"
    assert settings.arduino.port == "COM9"
    assert settings.arduino.mock_enabled is False
    assert settings.camera.source == 1

    get_settings.cache_clear()


def test_get_settings_is_cached() -> None:
    """get_settings should return the same cached instance."""
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()
