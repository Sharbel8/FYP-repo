# Smart Traffic Light FYP — Cursor AI Handoff

Share this file with your partner. Paste the **Master Prompt** into a new Cursor chat to stay aligned.

---

## Master Prompt (paste into Cursor first)

```
I am building a Final Year Project (FYP) called:

"A Hybrid Hardware–Software System for Traffic Pattern Analysis, Vehicle Counting, and Signal Duration Monitoring Using Machine Learning."

Act as my senior software engineer and AI assistant. Every solution should be modular, scalable, well-documented, and follow best coding practices.

Do NOT generate the entire project at once. Guide me step-by-step. At each stage:
1. Explain the architecture
2. Explain why we implement it
3. Write clean code
4. Explain how to test it
5. Wait for confirmation before the next module

PROJECT OBJECTIVES
• Detect vehicles using computer vision (YOLOv8)
• Detect pedestrians using computer vision
• Count vehicles crossing predefined lanes
• Count pedestrians
• Measure red, yellow, green traffic light durations via Arduino + 3 LDR sensors
• Store all data in MongoDB
• Preprocess data and engineer features (flow rate, congestion, density, waiting time)
• Train ML models (Random Forest, XGBoost, LightGBM) for short-term congestion prediction
• Display live data in a Streamlit dashboard

HARDWARE (baseline, low cost)
• USB webcam or IP camera
• Arduino Uno + 3 LDR sensors (R/Y/G) + resistors + breadboard
• Laptop runs Python, MongoDB, YOLO, Streamlit
• Lab mock setup first (3 LEDs + cardboard intersection) before real intersection

SOFTWARE STACK
Python 3.12+, OpenCV, Ultralytics YOLOv8, scikit-learn, XGBoost, LightGBM, Pandas, NumPy, MongoDB (pymongo), Streamlit, Plotly, PySerial

PROJECT FOLDER (traffic-system/)
camera/, detection/, tracking/, arduino/, database/, ml/, preprocessing/, dashboard/, models/, utils/, config/, tests/

CODING RULES
• Production-quality Python, OOP where appropriate
• Separate logic into modules
• Docstrings + comments where needed
• logging instead of print()
• Handle exceptions
• No hardcoded values — use config/ and .env
• Each module independently testable

IMPORTANT DECISIONS ALREADY MADE
• Software-first approach is OK (no hardware needed to start)
• Build order: config/utils → database → camera → detection → tracking → mock arduino → preprocessing → ML → dashboard
• Tracking is REQUIRED for accurate counting (not optional)
• MongoDB creates database automatically on first write (database name: traffic_system)
• Arduino mock_enabled=true in .env until hardware arrives
• Dashboard reads Mongo only (does not run YOLO inside Streamlit)

CURRENT PROGRESS
✅ Step 1: Scaffold, config, logging — DONE
✅ Step 2: MongoDB connection, repositories, indexes — DONE
✅ Step 3: Camera capture module — DONE (verify OpenCV installed)
⬜ Step 4: Detection (YOLO)
⬜ Step 5: Tracking + counting
⬜ Step 6: Mock Arduino → Mongo
⬜ Step 7: Preprocessing + features
⬜ Step 8: ML training/inference
⬜ Step 9: Streamlit dashboard

Workspace: c:\Users\user\Desktop\Smart Traffic Light FYP\traffic-system
```

---

## Original Project Prompt (full spec)

```
I am building a Final Year Project (FYP) called:

"A Hybrid Hardware–Software System for Traffic Pattern Analysis, Vehicle Counting, and Signal Duration Monitoring Using Machine Learning."

I want you to act as my senior software engineer and AI assistant throughout the development of this project. Every solution should be modular, scalable, well-documented, and follow best coding practices.

PROJECT OVERVIEW

The objective of this project is to develop a low-cost intelligent traffic monitoring system capable of collecting real-time traffic data, analyzing traffic behavior, predicting congestion, and visualizing the results through a dashboard.

Unlike traditional traffic systems that rely on historical datasets or expensive infrastructure, this project combines computer vision, hardware sensors, machine learning, and data visualization.

The project is intended for deployment at a single traffic intersection and will serve as the foundation for future intelligent traffic signal optimization.

PROJECT OBJECTIVES

• Detect vehicles using computer vision.
• Detect pedestrians using computer vision.
• Count vehicles crossing predefined lanes.
• Count pedestrians.
• Measure red, yellow, and green traffic light durations using hardware sensors connected to an Arduino.
• Store all collected data inside MongoDB.
• Preprocess and clean collected traffic data.
• Generate useful traffic features such as traffic flow rate and congestion indicators.
• Train machine learning models to predict short-term congestion.
• Display live traffic information and predictions inside a Streamlit dashboard.

PROJECT HARDWARE

Traffic Camera - USB Webcam or IP Camera
Arduino Uno - Connected to three LDR light sensors
Three LDR Sensors - One for Red, Yellow, Green
Laptop - Runs Python, MongoDB, YOLO and Streamlit

SOFTWARE STACK

Python 3.12+, OpenCV, YOLOv8 (Ultralytics), Scikit-learn, Random Forest, XGBoost, LightGBM, Pandas, NumPy, MongoDB, Streamlit, Plotly, PySerial

SYSTEM WORKFLOW

1. Camera captures live traffic video.
2. YOLO detects cars, trucks, buses, motorcycles, pedestrians.
3. Vehicles and pedestrians counted every few seconds.
4. Arduino measures traffic light durations (Red, Yellow, Green).
5. Python receives sensor data from Arduino.
6. All information stored in MongoDB.
7. Data preprocessing applied.
8. Feature engineering: flow rate, congestion indicator, vehicle density, waiting time.
9. ML models analyze traffic patterns.
10. Predict congestion and future traffic flow.
11. Display in Streamlit dashboard.

PROJECT FOLDER STRUCTURE

traffic-system/
  camera/, detection/, tracking/, arduino/, database/, ml/, preprocessing/, dashboard/, models/, utils/, config/, tests/

CODING REQUIREMENTS

• Production-quality Python, OOP where appropriate
• Separate logic into modules, docstrings, comments
• logging instead of print()
• Handle exceptions, reusable code, no hardcoding
• Each module independently testable

FUTURE EXTENSIONS (design for, don't build now)

• Reinforcement Learning for adaptive signal control
• Multi-intersection monitoring
• Cloud deployment, smart city integration, emergency vehicle prioritization

Do not generate the entire project at once. Guide step-by-step. Wait for confirmation before each module.
```

---

## Follow-up prompts used in this project (chronological)

1. **Hardware list:** "Give me all the hardware needed to begin, at the lowest cost and the baseline in order to reach my goal."

2. **Full process:** "From Step A to whatever step it takes — give me the full process to begin the project."

3. **Software first?:** "So I can't start with the software first right?"

4. **Create folders:** "Create the necessary folders for me please."

5. **Folder roles:** "Explain each folder what it contains, especially arduino."

6. **Coding start:** "From these folders, where can I start if we're speaking coding wise?"

7. **Step 1:** "Start step 1"

8. **Step 2:** "To step 2"

9. **MongoDB setup:** "How shall I start managing MongoDB or at least create the database? I have MongoDB installed but don't have the data yet."

10. **After smoke test:** "I ran smoke_step2.py — what comes next?"

11. **Step 3:** "Step 3 do it please"

12. **Redo Step 3:** "Redo step 3 for me please"

13. **Partner sync:** "Give me all the previous prompts so my partner can re-prompt his AI tool to stay on track."

---

## Prompts to continue from current state

### Verify setup (run before new work)

```
Read PROJECT_HANDOFF.md and README.md in traffic-system/.
Confirm Steps 1–3 are complete. Run pytest and smoke scripts.
Tell me what's missing before we continue.
```

### Step 4 — Detection

```
We are on Step 4. Steps 1–3 are done (config, database, camera).
Implement detection/ with YOLOv8 wrapper:
- Load model from config (yolov8n.pt)
- Filter classes: car, truck, bus, motorcycle, person
- Confidence threshold from config
- Unit tests + scripts/smoke_step4.py
Follow existing patterns in config/, utils/, database/, camera/.
Wait for my confirmation before Step 5.
```

### Step 5 — Tracking + counting

```
Implement tracking/ with object tracking and line-crossing counts.
Write counts to MongoDB detections collection every N seconds (from config).
Tracking is required — detection alone double-counts.
Unit tests + smoke script. Wait before Step 6.
```

### Step 6 — Mock Arduino

```
Implement arduino/ with a mock serial feeder (ARDUINO_MOCK_ENABLED=true).
Write R/Y/G state and durations to signal_states collection.
Match format expected by dashboard later. Real firmware comes when hardware arrives.
```

---

## Key decisions (do not re-debate)

| Topic | Decision |
|-------|----------|
| Start without hardware? | Yes — laptop webcam + mock Arduino |
| Database name | `traffic_system` |
| MongoDB create DB | Automatic on first document insert |
| Arduino until hardware | `ARDUINO_MOCK_ENABLED=true` in `.env` |
| Accurate counting | Requires tracking (Step 5), not detection alone |
| Dashboard | Reads Mongo only; no YOLO inside Streamlit |
| PowerShell venv issue | Use `.\.venv\Scripts\python.exe` directly if activate fails |

---

## Commands

```powershell
cd "c:\Users\user\Desktop\Smart Traffic Light FYP\traffic-system"

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\smoke_step1.py
.\.venv\Scripts\python.exe scripts\smoke_step2.py
.\.venv\Scripts\python.exe scripts\smoke_step3.py
.\.venv\Scripts\python.exe scripts\smoke_step3.py --show
```

MongoDB Compass: `mongodb://localhost:27017` → database `traffic_system`

---

## Build order reference

| Step | Module | Status |
|------|--------|--------|
| 1 | config/ + utils/ | ✅ Done |
| 2 | database/ | ✅ Done |
| 3 | camera/ | ✅ Done |
| 4 | detection/ | ⬜ Next |
| 5 | tracking/ | ⬜ |
| 6 | arduino/ (mock first) | ⬜ |
| 7 | preprocessing/ | ⬜ |
| 8 | ml/ + models/ | ⬜ |
| 9 | dashboard/ | ⬜ |
