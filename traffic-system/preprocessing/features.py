"""Feature engineering for traffic windows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TrafficFeatures:
    """Numeric features for one aggregation window."""

    vehicle_count: float
    pedestrian_count: float
    flow_rate_per_min: float
    vehicle_density: float
    red_duration_s: float
    yellow_duration_s: float
    green_duration_s: float
    current_state_code: float
    waiting_time_proxy: float
    congestion_score: float
    congestion_label: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to a MongoDB-friendly dictionary."""
        return asdict(self)


STATE_CODES = {"RED": 0.0, "YELLOW": 1.0, "GREEN": 2.0}


def compute_features(
    *,
    vehicle_count: float,
    pedestrian_count: float = 0.0,
    window_seconds: float = 10.0,
    red_duration_s: float = 0.0,
    yellow_duration_s: float = 0.0,
    green_duration_s: float = 0.0,
    current_state: str = "GREEN",
    density_capacity: float = 20.0,
    congestion_low: float = 0.35,
    congestion_high: float = 0.70,
) -> TrafficFeatures:
    """
    Build traffic features from counts and signal timings.

    Definitions (FYP-friendly, documented for the report):
    - ``flow_rate_per_min``: vehicles scaled to a per-minute rate
    - ``vehicle_density``: vehicles / capacity (clipped to 1.0)
    - ``waiting_time_proxy``: density × red duration (seconds)
    - ``congestion_score``: weighted blend of density, inverse flow, and waiting
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if density_capacity <= 0:
        raise ValueError("density_capacity must be positive")

    vehicles = max(0.0, float(vehicle_count))
    pedestrians = max(0.0, float(pedestrian_count))
    flow_rate = vehicles * (60.0 / window_seconds)
    density = min(1.0, vehicles / density_capacity)

    red = max(0.0, float(red_duration_s))
    yellow = max(0.0, float(yellow_duration_s))
    green = max(0.0, float(green_duration_s))
    state = (current_state or "GREEN").upper()
    state_code = STATE_CODES.get(state, 2.0)

    waiting_proxy = density * red

    # Normalize helpers into [0, 1]-ish contributions
    flow_pressure = min(1.0, flow_rate / 60.0)  # 60 veh/min ≈ saturated for one lane
    wait_pressure = min(1.0, waiting_proxy / 30.0)
    congestion = min(
        1.0,
        0.50 * density + 0.25 * flow_pressure + 0.25 * wait_pressure,
    )

    if congestion < congestion_low:
        label = "low"
    elif congestion < congestion_high:
        label = "medium"
    else:
        label = "high"

    return TrafficFeatures(
        vehicle_count=vehicles,
        pedestrian_count=pedestrians,
        flow_rate_per_min=round(flow_rate, 3),
        vehicle_density=round(density, 3),
        red_duration_s=red,
        yellow_duration_s=yellow,
        green_duration_s=green,
        current_state_code=state_code,
        waiting_time_proxy=round(waiting_proxy, 3),
        congestion_score=round(congestion, 3),
        congestion_label=label,
    )
