"""Camera capture package."""

from camera.exceptions import CameraError, CameraOpenError, CameraReadError
from camera.stream import CameraStream

__all__ = [
    "CameraError",
    "CameraOpenError",
    "CameraReadError",
    "CameraStream",
]
