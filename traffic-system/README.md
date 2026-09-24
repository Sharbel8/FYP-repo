"""
Smart Traffic Light System — Final Year Project

Hybrid hardware–software traffic monitoring: computer vision, Arduino signal
timing, MongoDB storage, ML congestion prediction, and a Streamlit dashboard.

## Current status

**Steps 6–7 complete:** mock Arduino signal timing + feature aggregation.

**Steps 4–5 complete:** YOLO detection plus tracking and line-crossing counts.

**Steps 1–3 complete:** scaffold, MongoDB, camera capture.

## Quick start

```bash
cd traffic-system
python -m venv .venv

# Windows (if Activate.ps1 is blocked, call python.exe directly)
.venv\\Scripts\\activate

pip install -r requirements.txt
copy .env.example .env

pytest -q
```

### Smoke tests

```bash
python scripts/smoke_step1.py
python scripts/smoke_step2.py          # needs MongoDB
python scripts/smoke_step3.py          # webcam / video
python scripts/smoke_step4.py          # YOLO detection
python scripts/smoke_step5.py          # tracking / counting
python scripts/smoke_step6.py          # mock Arduino → MongoDB
python scripts/smoke_step7.py          # features → aggregates
```

## Folder overview

| Folder | Role |
|--------|------|
| `config/` | YAML + env settings |
| `utils/` | Logging and shared helpers |
| `database/` | MongoDB |
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
- Keep `ARDUINO_MOCK_ENABLED=true` until hardware is connected

## Database collections

| Collection | Purpose |
|------------|---------|
| `detections` | Periodic vehicle / pedestrian counts |
| `signal_states` | R/Y/G phase timings |
| `aggregates` | Windowed features for ML / charts |
| `predictions` | Model outputs |
| `system_health` | Worker heartbeats |

## Next step

**Step 8 — `ml/`:** train and run congestion prediction models.
"""
