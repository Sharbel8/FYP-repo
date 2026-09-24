"""Unit tests for the YOLO detector wrapper without model downloads."""

from __future__ import annotations

import numpy as np
import pytest

from detection import Detection, YoloDetector


class _Value:
    def __init__(self, value): self.value = value
    def item(self): return self.value


class _Coordinates:
    def __init__(self, values): self.values = values
    def tolist(self): return self.values


class _Box:
    def __init__(self, class_id: int, confidence: float, coordinates: list[float]):
        self.cls, self.conf, self.xyxy = [_Value(class_id)], [_Value(confidence)], [_Coordinates(coordinates)]


class _Result:
    names = {0: "person", 2: "car", 16: "dog"}
    boxes = [_Box(2, .91, [10, 20, 50, 80]), _Box(0, .80, [100, 40, 140, 120]), _Box(16, .99, [0, 0, 10, 10]), _Box(2, .20, [1, 1, 2, 2])]


class _Model:
    def predict(self, frame, *, conf: float, verbose: bool):
        assert frame.shape == (100, 100, 3) and conf == .4 and verbose is False
        return [_Result()]


def test_detection_centroid_and_serialisation() -> None:
    detection = Detection("car", .9, 10, 20, 30, 60)
    assert detection.centroid == (20, 40)
    assert detection.as_dict()["class_name"] == "car"


def test_detector_filters_classes_and_confidence() -> None:
    detector = YoloDetector(confidence=.4, classes=["car", "person"], model=_Model())
    detections = detector.detect(np.zeros((100, 100, 3), dtype=np.uint8))
    assert [(item.class_name, item.confidence) for item in detections] == [("car", .91), ("person", .8)]


def test_detector_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="confidence"): YoloDetector(confidence=1.1, model=_Model())
    with pytest.raises(ValueError, match="at least one"): YoloDetector(classes=[], model=_Model())
