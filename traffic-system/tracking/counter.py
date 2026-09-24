"""Counting-line geometry and exactly-once crossing counts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from tracking.tracker import Track


@dataclass(frozen=True)
class CountingLine:
    """Directed line segment used to count objects moving across it."""

    start: tuple[float, float]
    end: tuple[float, float]

    def side(self, point: tuple[float, float]) -> float:
        """Return the signed side-of-line value for a point."""
        return ((self.end[0] - self.start[0]) * (point[1] - self.start[1])) - (
            (self.end[1] - self.start[1]) * (point[0] - self.start[0])
        )


class LineCrossingCounter:
    """Count each track once when it moves from one side of a line to the other."""

    def __init__(self, line: CountingLine) -> None:
        self.line = line
        self._previous_side: dict[int, float] = {}
        self._counted_ids: set[int] = set()
        self._counts: Counter[str] = Counter()

    @property
    def counts(self) -> dict[str, int]:
        """Return cumulative class counts, including no unconfigured classes."""
        return dict(self._counts)

    def update(self, tracks: list[Track]) -> list[Track]:
        """Return tracks that crossed the line in this frame."""
        crossings: list[Track] = []
        for track in tracks:
            current_side = self.line.side(track.centroid)
            previous_side = self._previous_side.get(track.track_id)
            self._previous_side[track.track_id] = current_side
            if track.track_id in self._counted_ids or previous_side is None:
                continue
            if previous_side == 0 or current_side == 0:
                continue
            if (previous_side < 0) != (current_side < 0):
                self._counted_ids.add(track.track_id)
                self._counts[track.class_name] += 1
                crossings.append(track)
        return crossings
