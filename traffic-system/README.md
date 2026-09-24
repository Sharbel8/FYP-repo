"""
Smart Traffic Light System — Final Year Project

Hybrid hardware–software traffic monitoring: computer vision, Arduino signal
timing, MongoDB storage, ML congestion prediction, and a Streamlit dashboard.

## Current status

**Steps 4–5 complete:** YOLO detection plus tracking and line-crossing counts.

**Step 2 complete:** MongoDB connection, repositories, and indexes.

**Step 1 complete:** project scaffold, configuration, and logging.

## Quick start (Step 1)

```bash
cd traffic-system
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux

pytest -q
```

Smoke-check settings + logging:

```bash
python scripts/smoke_step1.py
```

Smoke-check MongoDB (requires a running MongoDB server):

```bash
python scripts/smoke_step2.py
```

Unit tests use **mongomock** and do not need a live MongoDB instance.

Camera smoke test (uses webcam by default):

```bash
python scripts/smoke_step3.py
python scripts/smoke_step3.py --show
python scripts/smoke_step3.py --source path\to\video.mp4
```

## Folder overview

| Folder | Role |
|--------|------|
| `config/` | YAML + env settings |
| `utils/` | Logging and shared helpers |
| `database/` | MongoDB (Step 2) |
| `camera/` | Video capture |
| `detection/` | YOLO detection |
| `tracking/` | Tracking & counting |
| `arduino/` | Serial / LDR light timing (mock first) |
| `preprocessing/` | Features & cleaning |
| `ml/` | Model training & inference |
| `models/` | Saved model files |
| `dashboard/` | Streamlit UI |
| `tests/` | Automated tests |

## Configuration

- Defaults: `config/settings.yaml`
- Local overrides: `.env` (see `.env.example`)
- Access in code: `from config import get_settings`

## Database collections

| Collection | Purpose |
|------------|---------|
| `detections` | Periodic vehicle / pedestrian counts |
| `signal_states` | R/Y/G phase timings |
| `aggregates` | Windowed features for ML / charts |
| `predictions` | Model outputs |
| `system_health` | Worker heartbeats |

## Next step

**Step 4 — `detection/`:** YOLOv8 vehicle and pedestrian detection.
"""
