"""Step 4 smoke test: run YOLO detection on a camera or video source."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0, str(PROJECT_ROOT))

from camera import CameraStream
from config import get_settings
from detection import YoloDetector
from utils import get_logger, setup_logging

def main() -> int:
    parser = argparse.ArgumentParser(description="YOLO detection smoke test")
    parser.add_argument("--source", default=None, help="Camera index or video file path")
    parser.add_argument("--frames", type=int, default=60)
    args = parser.parse_args(); settings = get_settings()
    setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    source = args.source if args.source is not None else settings.camera.source
    source = int(source) if isinstance(source, str) and source.isdigit() else source
    detector, logger, detected = YoloDetector.from_settings(settings), get_logger("smoke_step4"), 0
    with CameraStream(source=source, width=settings.camera.width, height=settings.camera.height) as camera:
        for _ in range(args.frames):
            ok, frame = camera.read()
            if not ok or frame is None: break
            detected += len(detector.detect(frame))
    logger.info("Step 4 smoke test complete: detected_objects=%s", detected)
    return 0

if __name__ == "__main__": raise SystemExit(main())
