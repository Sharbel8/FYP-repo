"""A lightweight, deterministic centroid tracker for traffic objects."""

from __future__ import annotations

from dataclasses import dataclass, replace

from detection import Detection


@dataclass(frozen=True)
class Track:
    """A detected object with a stable identifier across nearby frames."""

    track_id: int
    class_name: str
    centroid: tuple[float, float]
    detection: Detection
    missed_frames: int = 0


class CentroidTracker:
    """Associate same-class detections by nearest centroid distance."""

    def __init__(self, *, max_distance: float = 80.0, max_missed_frames: int = 15) -> None:
        if max_distance <= 0:
            raise ValueError("max_distance must be positive")
        if max_missed_frames < 0:
            raise ValueError("max_missed_frames must be non-negative")
        self.max_distance = max_distance
        self.max_missed_frames = max_missed_frames
        self._next_id = 1
        self._tracks: dict[int, Track] = {}

    @property
    def active_tracks(self) -> list[Track]:
        """Return active tracks ordered by identifier."""
        return [self._tracks[key] for key in sorted(self._tracks)]

    def update(self, detections: list[Detection]) -> list[Track]:
        """Update tracks and return tracks matched or created this frame."""
        pairs: list[tuple[float, int, int]] = []
        for track_id, track in self._tracks.items():
            for index, detection in enumerate(detections):
                if track.class_name != detection.class_name:
                    continue
                distance = self._distance(track.centroid, detection.centroid)
                if distance <= self.max_distance:
                    pairs.append((distance, track_id, index))
        pairs.sort()

        matched_tracks: set[int] = set()
        matched_detections: set[int] = set()
        current: list[Track] = []
        for _, track_id, index in pairs:
            if track_id in matched_tracks or index in matched_detections:
                continue
            detection = detections[index]
            track = Track(track_id, detection.class_name, detection.centroid, detection)
            self._tracks[track_id] = track
            matched_tracks.add(track_id)
            matched_detections.add(index)
            current.append(track)

        for track_id, track in list(self._tracks.items()):
            if track_id not in matched_tracks:
                self._tracks[track_id] = replace(track, missed_frames=track.missed_frames + 1)
                if self._tracks[track_id].missed_frames > self.max_missed_frames:
                    del self._tracks[track_id]

        for index, detection in enumerate(detections):
            if index in matched_detections:
                continue
            track = Track(self._next_id, detection.class_name, detection.centroid, detection)
            self._tracks[track.track_id] = track
            self._next_id += 1
            current.append(track)
        return sorted(current, key=lambda track: track.track_id)

    @staticmethod
    def _distance(first: tuple[float, float], second: tuple[float, float]) -> float:
        return ((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2) ** 0.5
