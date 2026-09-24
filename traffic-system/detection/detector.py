"""Configurable wrapper around an Ultralytics YOLO model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from config import Settings, get_settings
from utils import get_logger

logger = get_logger("detection.detector")


class DetectorError(RuntimeError):
    """Raised when a YOLO model cannot be loaded or used."""


@dataclass(frozen=True)
class Detection:
    """One object detected in an image, using pixel coordinates."""

    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def centroid(self) -> tuple[float, float]:
        """Return the centre point of the bounding box."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def as_dict(self) -> dict[str, float | str]:
        """Return a serialisable representation for logs or APIs."""
        return {
            "class_name": self.class_name,
            "confidence": self.confidence,
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
        }


class YoloDetector:
    """Run YOLO inference and keep only configured road-user classes."""

    def __init__(
        self,
        *,
        model_name: str | None = None,
        confidence: float | None = None,
        classes: Iterable[str] | None = None,
        settings: Settings | None = None,
        model: Any | None = None,
    ) -> None:
        cfg = settings or get_settings()
        self.model_name = model_name or cfg.detection.model_name
        self.confidence = confidence if confidence is not None else cfg.detection.confidence
        self.classes = frozenset(cfg.detection.classes if classes is None else classes)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.classes:
            raise ValueError("at least one detection class is required")
        self._model = model

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "YoloDetector":
        """Create a detector using application settings."""
        return cls(settings=settings)

    @property
    def is_loaded(self) -> bool:
        """Whether the YOLO model has already been loaded."""
        return self._model is not None

    def load(self) -> None:
        """Load model weights lazily, downloading them if Ultralytics needs to."""
        if self._model is not None:
            return
        try:
            from ultralytics import YOLO

            self._model = YOLO(self.model_name)
        except Exception as exc:  # Ultralytics provides several runtime-specific errors.
            raise DetectorError(f"Unable to load YOLO model '{self.model_name}': {exc}") from exc
        logger.info("Loaded YOLO model '%s'", self.model_name)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Detect configured classes in one BGR OpenCV frame."""
        if frame is None or frame.size == 0:
            raise ValueError("frame must be a non-empty image")
        self.load()
        assert self._model is not None
        try:
            results = self._model.predict(frame, conf=self.confidence, verbose=False)
        except Exception as exc:
            raise DetectorError(f"YOLO inference failed: {exc}") from exc
        detections = self._parse_results(results)
        logger.debug("Detected %s configured objects", len(detections))
        return detections

    def _parse_results(self, results: Iterable[Any]) -> list[Detection]:
        """Convert Ultralytics results to stable application detections."""
        parsed: list[Detection] = []
        for result in results:
            names = result.names
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls[0].item())
                class_name = str(names[class_id])
                score = float(box.conf[0].item())
                if class_name not in self.classes or score < self.confidence:
                    continue
                x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
                parsed.append(Detection(class_name, score, x1, y1, x2, y2))
        return parsed
