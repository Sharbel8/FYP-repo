"""Step 3 smoke test: open camera/video and report FPS."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2

from camera import CameraOpenError, CameraStream
from config import get_settings
from utils import get_logger, setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Camera smoke test")
    parser.add_argument(
        "--frames",
        type=int,
        default=60,
        help="Number of frames to capture before exiting (default: 60)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show a preview window (press Q to quit early)",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Override camera source (index or video path)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    logger = get_logger("smoke_step3")

    source = args.source if args.source is not None else settings.camera.source
    if isinstance(source, str) and source.isdigit():
        source = int(source)

    stream = CameraStream(
        source=source,
        width=settings.camera.width,
        height=settings.camera.height,
        fps_target=settings.camera.fps_target,
        frame_skip=settings.camera.frame_skip,
    )

    try:
        stream.open()
    except CameraOpenError as exc:
        logger.error("%s", exc)
        logger.error(
            "Tips: set CAMERA_SOURCE=0 in .env, close apps using the webcam, "
            "or pass --source path\\to\\video.mp4"
        )
        return 1

    logger.info("Properties: %s", stream.get_properties())
    captured = 0

    try:
        while captured < args.frames:
            ok, frame = stream.read()
            if not ok or frame is None:
                logger.warning("Frame read failed at count=%s", captured)
                break

            captured += 1
            if captured % 15 == 0:
                logger.info(
                    "Captured %s frames | avg_fps=%.2f",
                    captured,
                    stream.average_fps,
                )

            if args.show:
                cv2.imshow("Step 3 Camera Smoke Test", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    logger.info("Quit requested from preview window")
                    break
    finally:
        stream.release()
        if args.show:
            cv2.destroyAllWindows()

    logger.info(
        "Step 3 smoke test done (frames=%s avg_fps=%.2f)",
        captured,
        stream.average_fps,
    )
    return 0 if captured > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
