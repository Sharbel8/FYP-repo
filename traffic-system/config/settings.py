"""Application configuration loaded from YAML and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root = parent of config/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parent / "settings.yaml"


@dataclass(frozen=True)
class AppSettings:
    """General application metadata and logging defaults."""

    name: str = "Smart Traffic Light System"
    environment: str = "development"
    log_level: str = "INFO"
    log_dir: str = "logs"


@dataclass(frozen=True)
class CameraSettings:
    """Video capture configuration."""

    source: int | str = 0
    width: int = 1280
    height: int = 720
    fps_target: int = 15
    frame_skip: int = 1


@dataclass(frozen=True)
class DetectionSettings:
    """YOLO detection configuration."""

    model_name: str = "yolov8n.pt"
    confidence: float = 0.40
    classes: tuple[str, ...] = ("car", "truck", "bus", "motorcycle", "person")


@dataclass(frozen=True)
class TrackingSettings:
    """Object tracking and counting configuration."""

    count_interval_seconds: int = 5
    counting_line: Any | None = None


@dataclass(frozen=True)
class ArduinoSettings:
    """Serial communication with the Arduino signal timer."""

    port: str = "COM3"
    baud_rate: int = 9600
    reconnect_delay_seconds: float = 2.0
    mock_enabled: bool = True


@dataclass(frozen=True)
class DatabaseSettings:
    """MongoDB connection settings."""

    uri: str = "mongodb://localhost:27017"
    name: str = "traffic_system"


@dataclass(frozen=True)
class AggregationSettings:
    """Time-window aggregation for feature engineering."""

    window_seconds: int = 10


@dataclass(frozen=True)
class MLSettings:
    """Machine learning inference defaults."""

    model_path: str = "models/congestion_model.joblib"
    prediction_interval_seconds: int = 60


@dataclass(frozen=True)
class DashboardSettings:
    """Streamlit dashboard refresh behaviour."""

    refresh_seconds: int = 5


@dataclass(frozen=True)
class Settings:
    """Root settings object shared across all modules."""

    app: AppSettings = field(default_factory=AppSettings)
    camera: CameraSettings = field(default_factory=CameraSettings)
    detection: DetectionSettings = field(default_factory=DetectionSettings)
    tracking: TrackingSettings = field(default_factory=TrackingSettings)
    arduino: ArduinoSettings = field(default_factory=ArduinoSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    aggregation: AggregationSettings = field(default_factory=AggregationSettings)
    ml: MLSettings = field(default_factory=MLSettings)
    dashboard: DashboardSettings = field(default_factory=DashboardSettings)


def _as_bool(value: str | bool) -> bool:
    """Convert common truthy/falsey string forms to bool."""
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_camera_source(value: str | int) -> int | str:
    """Parse camera source as an int index when possible, else keep as path string."""
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return text


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Settings file must contain a mapping: {path}")
    return data


def _build_settings(raw: dict[str, Any]) -> Settings:
    """Map a raw YAML dictionary into typed Settings dataclasses."""
    app_raw = raw.get("app", {})
    camera_raw = raw.get("camera", {})
    detection_raw = raw.get("detection", {})
    tracking_raw = raw.get("tracking", {})
    arduino_raw = raw.get("arduino", {})
    database_raw = raw.get("database", {})
    aggregation_raw = raw.get("aggregation", {})
    ml_raw = raw.get("ml", {})
    dashboard_raw = raw.get("dashboard", {})

    return Settings(
        app=AppSettings(
            name=str(app_raw.get("name", AppSettings.name)),
            environment=str(app_raw.get("environment", AppSettings.environment)),
            log_level=str(app_raw.get("log_level", AppSettings.log_level)),
            log_dir=str(app_raw.get("log_dir", AppSettings.log_dir)),
        ),
        camera=CameraSettings(
            source=_as_camera_source(camera_raw.get("source", CameraSettings.source)),
            width=int(camera_raw.get("width", CameraSettings.width)),
            height=int(camera_raw.get("height", CameraSettings.height)),
            fps_target=int(camera_raw.get("fps_target", CameraSettings.fps_target)),
            frame_skip=int(camera_raw.get("frame_skip", CameraSettings.frame_skip)),
        ),
        detection=DetectionSettings(
            model_name=str(detection_raw.get("model_name", DetectionSettings.model_name)),
            confidence=float(detection_raw.get("confidence", DetectionSettings.confidence)),
            classes=tuple(detection_raw.get("classes", list(DetectionSettings.classes))),
        ),
        tracking=TrackingSettings(
            count_interval_seconds=int(
                tracking_raw.get(
                    "count_interval_seconds",
                    TrackingSettings.count_interval_seconds,
                )
            ),
            counting_line=tracking_raw.get("counting_line"),
        ),
        arduino=ArduinoSettings(
            port=str(arduino_raw.get("port", ArduinoSettings.port)),
            baud_rate=int(arduino_raw.get("baud_rate", ArduinoSettings.baud_rate)),
            reconnect_delay_seconds=float(
                arduino_raw.get(
                    "reconnect_delay_seconds",
                    ArduinoSettings.reconnect_delay_seconds,
                )
            ),
            mock_enabled=_as_bool(
                arduino_raw.get("mock_enabled", ArduinoSettings.mock_enabled)
            ),
        ),
        database=DatabaseSettings(
            uri=str(database_raw.get("uri", DatabaseSettings.uri)),
            name=str(database_raw.get("name", DatabaseSettings.name)),
        ),
        aggregation=AggregationSettings(
            window_seconds=int(
                aggregation_raw.get("window_seconds", AggregationSettings.window_seconds)
            ),
        ),
        ml=MLSettings(
            model_path=str(ml_raw.get("model_path", MLSettings.model_path)),
            prediction_interval_seconds=int(
                ml_raw.get(
                    "prediction_interval_seconds",
                    MLSettings.prediction_interval_seconds,
                )
            ),
        ),
        dashboard=DashboardSettings(
            refresh_seconds=int(
                dashboard_raw.get("refresh_seconds", DashboardSettings.refresh_seconds)
            ),
        ),
    )


def _apply_env_overrides(settings: Settings) -> Settings:
    """Override YAML values with environment variables when present."""
    return Settings(
        app=AppSettings(
            name=settings.app.name,
            environment=os.getenv("APP_ENV", settings.app.environment),
            log_level=os.getenv("LOG_LEVEL", settings.app.log_level),
            log_dir=settings.app.log_dir,
        ),
        camera=CameraSettings(
            source=_as_camera_source(
                os.getenv("CAMERA_SOURCE", str(settings.camera.source))
            ),
            width=settings.camera.width,
            height=settings.camera.height,
            fps_target=settings.camera.fps_target,
            frame_skip=settings.camera.frame_skip,
        ),
        detection=settings.detection,
        tracking=settings.tracking,
        arduino=ArduinoSettings(
            port=os.getenv("ARDUINO_PORT", settings.arduino.port),
            baud_rate=int(os.getenv("ARDUINO_BAUD_RATE", settings.arduino.baud_rate)),
            reconnect_delay_seconds=settings.arduino.reconnect_delay_seconds,
            mock_enabled=_as_bool(
                os.getenv("ARDUINO_MOCK_ENABLED", str(settings.arduino.mock_enabled))
            ),
        ),
        database=DatabaseSettings(
            uri=os.getenv("MONGO_URI", settings.database.uri),
            name=os.getenv("MONGO_DB_NAME", settings.database.name),
        ),
        aggregation=settings.aggregation,
        ml=settings.ml,
        dashboard=settings.dashboard,
    )


def load_settings(
    settings_path: Path | str | None = None,
    *,
    env_file: Path | str | None = None,
) -> Settings:
    """
    Load settings from YAML, then apply `.env` / process environment overrides.

    Args:
        settings_path: Optional path to a YAML settings file.
        env_file: Optional path to a dotenv file. Defaults to project `.env`.

    Returns:
        Immutable Settings instance.
    """
    dotenv_path = Path(env_file) if env_file else PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path, override=False)

    path = Path(settings_path) if settings_path else DEFAULT_SETTINGS_PATH
    raw = _load_yaml(path)
    return _apply_env_overrides(_build_settings(raw))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings singleton for application use.

    Call ``get_settings.cache_clear()`` in tests after changing env vars.
    """
    return load_settings()
