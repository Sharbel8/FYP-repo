"""Camera-related exceptions."""


class CameraError(RuntimeError):
    """Base error for camera capture failures."""


class CameraOpenError(CameraError):
    """Raised when the camera or video source cannot be opened."""


class CameraReadError(CameraError):
    """Raised when frame reading fails unexpectedly."""
