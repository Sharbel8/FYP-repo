"""Unit tests for the camera capture module."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from camera import CameraOpenError, CameraReadError, CameraStream


@pytest.fixture()
def sample_video(tmp_path: Path) -> Path:
    """Create a tiny synthetic AVI used as a file camera source."""
    path = tmp_path / "sample.avi"
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        10.0,
        (64, 48),
    )
    assert writer.isOpened(), "Failed to create test video writer"
    for i in range(12):
        frame = np.full((48, 64, 3), (i * 10) % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    assert path.exists()
    return path


def test_open_and_read_video_file(sample_video: Path) -> None:
    stream = CameraStream(str(sample_video), width=64, height=48, frame_skip=1)
    stream.open()
    assert stream.is_opened

    ok, frame = stream.read()
    assert ok is True
    assert frame is not None
    assert frame.shape[0] == 48
    assert frame.shape[1] == 64

    props = stream.get_properties()
    assert props["opened"] is True
    assert props["is_file"] is True
    stream.release()
    assert stream.is_opened is False


def test_context_manager_reads_until_eof(sample_video: Path) -> None:
    frames = 0
    with CameraStream(str(sample_video), frame_skip=1) as stream:
        while True:
            ok, frame = stream.read()
            if not ok:
                break
            assert frame is not None
            frames += 1
    assert frames >= 1


def test_frame_skip_reduces_returned_frames(sample_video: Path) -> None:
    with CameraStream(str(sample_video), frame_skip=2) as stream:
        frames = 0
        while True:
            ok, _ = stream.read()
            if not ok:
                break
            frames += 1
    # 12 written frames, skip=2 → about 6 returned
    assert 4 <= frames <= 7


def test_missing_file_raises() -> None:
    stream = CameraStream("does_not_exist.mp4")
    with pytest.raises(CameraOpenError):
        stream.open()


def test_read_before_open_raises(sample_video: Path) -> None:
    stream = CameraStream(str(sample_video))
    with pytest.raises(CameraReadError):
        stream.read()
