"""Step 5 smoke test: track and count objects crossing a supplied line."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0, str(PROJECT_ROOT))

from camera import CameraStream
from config import get_settings
from database import DetectionRepository, get_database
from detection import YoloDetector
from tracking import CentroidTracker, CountingLine, LineCrossingCounter, TrafficCountingWorker
from utils import get_logger, setup_logging

def main() -> int:
    parser = argparse.ArgumentParser(description="Tracking and counting smoke test")
    parser.add_argument("--source", required=True, help="Camera index or video file path")
    parser.add_argument("--line", required=True, nargs=4, type=float, metavar=("X1", "Y1", "X2", "Y2"))
    parser.add_argument("--frames", type=int, default=300); parser.add_argument("--lane-id", default="default")
    args = parser.parse_args(); settings = get_settings()
    setup_logging(level=settings.app.log_level, log_dir=settings.app.log_dir)
    source = int(args.source) if args.source.isdigit() else args.source
    worker = TrafficCountingWorker(YoloDetector.from_settings(settings), CentroidTracker(), LineCrossingCounter(CountingLine(tuple(args.line[:2]), tuple(args.line[2:]))), DetectionRepository(get_database()), lane_id=args.lane_id, count_interval_seconds=settings.tracking.count_interval_seconds)
    with CameraStream(source=source, width=settings.camera.width, height=settings.camera.height) as camera:
        for _ in range(args.frames):
            ok, frame = camera.read()
            if not ok or frame is None: break
            worker.process_frame(frame)
    get_logger("smoke_step5").info("Step 5 smoke test complete: counts=%s", worker.counter.counts)
    return 0

if __name__ == "__main__": raise SystemExit(main())
