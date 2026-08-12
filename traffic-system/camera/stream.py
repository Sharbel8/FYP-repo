"""Video capture abstraction for webcams and video files."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from camera.exceptions import CameraOpenError, CameraReadError
from config import Settings, get_settings
from utils import get_logger

logger = get_logger("camera.stream")


class CameraStream:
    """
    Thin OpenCV wrapper for consistent frame capture.

    Supports:
    - Webcam index (e.g. ``0``)
    - Video file path (e.g. ``data/sample.mp4``)

    Usage::

        with CameraStream.from_settings() as cam:
            ok, frame = cam.read()
    """

    def __init__(
        self,
        source: int | str = 0,
        *,
        width: int = 1280,
        height: int = 720,
        fps_target: int = 15,
        frame_skip: int = 1,
        backend: int | None = None,
    ) -> None:
        """
        Args:
            source: Webcam index or path to a video file.
            width: Requested capture width (webcams; files keep native size).
            height: Requested capture height.
            fps_target: Target processing rate used for optional pacing.
            frame_skip: Read every Nth frame (1 = every frame).
            backend: Optional OpenCV capture backend flag.
        """
        if frame_skip < 1:
            raise ValueError("frame_skip must be >= 1")

        self.source = source
        self.width = width
        self.height = height
        self.fps_target = fps_target
        self.frame_skip = frame_skip
        self.backend = backend

        self._capture: cv2.VideoCapture | None = None
        self._frame_index = 0
        self._frames_returned = 0
        self._started_at: float | None = None
        self._last_frame_at: float | None = None
        self._is_file_source = isinstance(source, str) and not str(source).isdigit()

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> CameraStream:
        """Build a ``CameraStream`` from application settings."""
        cfg = settings or get_settings()
        return cls(
            source=cfg.camera.source,
            width=cfg.camera.width,
            height=cfg.camera.height,
            fps_target=cfg.camera.fps_target,
            frame_skip=cfg.camera.frame_skip,
        )

    @property
    def is_opened(self) -> bool:
        """Whether the underlying capture device is open."""
        return self._capture is not None and self._capture.isOpened()

    @property
    def average_fps(self) -> float:
        """Average returned-frame rate since ``open()``."""
        if self._started_at is None or self._frames_returned == 0:
            return 0.0
        elapsed = time.perf_counter() - self._started_at
        if elapsed <= 0:
            return 0.0
        return self._frames_returned / elapsed

    def open(self) -> None:
        """Open the configured camera or video file."""
        if self.is_opened:
            return

        source = self._resolve_source(self.source)
        backend = self._resolve_backend(source)

        logger.info("Opening camera source=%s backend=%s", source, backend)
        if backend is None:
            capture = cv2.VideoCapture(source)
        else:
            capture = cv2.VideoCapture(source, backend)

        if not capture.isOpened():
            capture.release()
            raise CameraOpenError(
                f"Unable to open camera source: {source!r}. "
                "Check CAMERA_SOURCE in .env or try another index/path."
            )

        if not self._is_file_source:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.width))
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.height))
            if self.fps_target > 0:
                capture.set(cv2.CAP_PROP_FPS, float(self.fps_target))

        self._capture = capture
        self._frame_index = 0
        self._frames_returned = 0
        self._started_at = time.perf_counter()
        self._last_frame_at = None

        actual_w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        actual_h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        logger.info("Camera opened (%sx%s)", actual_w, actual_h)

    def read(self) -> tuple[bool, np.ndarray | None]:
        """
        Read the next processed frame.

        Returns:
            ``(True, frame)`` on success, ``(False, None)`` on end-of-stream
            or a recoverable empty read.
        """
        if not self.is_opened or self._capture is None:
            raise CameraReadError("Camera is not open. Call open() first.")

        frame: np.ndarray | None = None
        ok = False

        # Honor frame_skip by grabbing intermediate frames cheaply.
        for _ in range(self.frame_skip):
            ok = self._capture.grab()
            if not ok:
                break
            self._frame_index += 1

        if ok:
            ok, frame = self._capture.retrieve()

        if not ok or frame is None:
            if self._is_file_source:
                logger.info("End of video file reached")
                return False, None
            logger.warning("Failed to read frame from live camera")
            return False, None

        self._frames_returned += 1
        self._last_frame_at = time.perf_counter()
        self._pace_if_needed()
        return True, frame

    def release(self) -> None:
        """Release the capture device and reset counters."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            logger.info(
                "Camera released (frames=%s avg_fps=%.2f)",
                self._frames_returned,
                self.average_fps,
            )

    def get_properties(self) -> dict[str, Any]:
        """Return useful capture properties for logging/health checks."""
        if not self.is_opened or self._capture is None:
            return {"opened": False}

        return {
            "opened": True,
            "source": self.source,
            "width": int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
            "height": int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
            "reported_fps": float(self._capture.get(cv2.CAP_PROP_FPS) or 0.0),
            "average_fps": self.average_fps,
            "frames_returned": self._frames_returned,
            "is_file": self._is_file_source,
        }

    def __enter__(self) -> CameraStream:
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    def _pace_if_needed(self) -> None:
        """Sleep lightly to approximate ``fps_target`` for live sources."""
        if self._is_file_source or self.fps_target <= 0 or self._last_frame_at is None:
            return
        # Only pace when we have at least two returned frames.
        if self._frames_returned < 2 or self._started_at is None:
            return
        expected = self._frames_returned / float(self.fps_target)
        elapsed = time.perf_counter() - self._started_at
        delay = expected - elapsed
        if delay > 0:
            time.sleep(min(delay, 0.05))

    @staticmethod
    def _resolve_source(source: int | str) -> int | str:
        """Normalise source to an int index or an existing file path string."""
        if isinstance(source, int):
            return source
        text = str(source).strip()
        if text.isdigit():
            return int(text)
        path = Path(text)
        if not path.exists():
            raise CameraOpenError(f"Video file does not exist: {path}")
        return str(path)

    def _resolve_backend(self, source: int | str) -> int | None:
        """Pick a capture backend; prefer DirectShow for Windows webcams."""
        if self.backend is not None:
            return self.backend
        if isinstance(source, int):
            # CAP_DSHOW is more reliable than MSMF on many Windows laptops.
            return getattr(cv2, "CAP_DSHOW", None)
        return None
