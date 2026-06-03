# Adaptive Cognitive-State Pomodoro Study Buddy

A real-time AI productivity tool that continuously senses your cognitive state — gaze, posture, blink rate, ambient noise, and phone use — and dynamically adapts your study/break timing using a rule-based adaptive engine and a Gemini-powered personal coach.

---

## Demo

Run `venv/bin/python tracker.py --work 5 --break 2` for a quick demo. A webcam window shows live focus density, posture status, ambient noise, and an adaptive timer. When focus drops, posture slips, or your phone appears, a personalized coaching message fires on-screen and as a macOS notification. Press **Q** or **Esc** to stop.

---

## Features

### Real-Time Sensing

| Sensor | What It Tracks |
|---|---|
| **Gaze** (MediaPipe FaceMesh, 478 landmarks) | Iris x-position → on-screen vs. looking away |
| **Blink rate** (Eye Aspect Ratio) | Fatigue indicator — normal is 15–20 blinks/min |
| **Posture** (MediaPipe Pose) | Shoulder Y-delta vs. per-session calibrated baseline |
| **Phone detection** (MediaPipe Hands) | Hand visible ≥ 3 continuous seconds during work block |
| **Active app** (macOS AppKit, bg thread) | Productive vs. distracting app classification |
| **Ambient noise** (sounddevice, bg thread) | RMS → dB SPL, classified as Quiet / Moderate / Loud |

### Adaptive Timer (4 Decision Rules)

| Trigger | Condition | Result |
|---|---|---|
| **Early break** | focus < 35% AND elapsed > 50% of block | Immediate break, LLM coaching message |
| **Flow extension** | focus ≥ 80% AND time left ≤ 30s | +5 min added (stackable), LLM coaching |
| **Posture nudge** | slouching > 70% of last 30s | LLM coaching (2-min cooldown) |
| **Phone detected** | hand visible ≥ 3s during work | LLM coaching message |

Press **E** at any time during a work block to manually extend +5 minutes. All timer changes are logged in `timer_history` with timestamp and reason.

### Break Mode

Break screen uses a distinct green HUD — no focus score shown, rotating relaxation tips (20-ft eye rule, breathing, hydration), and gentle posture reminders. Transition between blocks includes an 8-second overlay, an audible tone (`Glass.aiff` → break, `Ping.aiff` → work), and macOS notification.

### Gemini AI Coach

Every intervention triggers an async call to `gemini-2.5-flash-lite`. The model receives your real-time focus score, blink rate, noise level, and app context, and returns 2–3 bullet coaching messages. Calls run in daemon threads — zero blocking of the 30fps video loop. Messages appear as:
- Camera feed overlay (bottom strip)
- macOS native notification
- Floating always-on-top window (`overlay.py`)

### Web Dashboard

`venv/bin/python web_dashboard.py` → open `http://localhost:5050` in any browser.

- **Focus trend** line chart (per-session, chronological)
- **Hourly productivity** bar chart (your personal peak hours)
- **App usage** doughnut chart
- **Session comparison** grouped bars (focus% vs posture%)
- **Adaptive Timer Log** — every timer change with timestamp, reason, and focus score
- **AI personalized advice** — on-demand Gemini coaching based on all historical data

---

## Setup

### Prerequisites

- Python 3.11+
- macOS (for active-window detection via AppKit and audio tones)
- Webcam and microphone
- A Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### Install

```bash
git clone https://github.com/safaahussain1/adaptive-pomodoro-buddy
cd adaptive-pomodoro-buddy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure API Key

```bash
echo 'GEMINI_API_KEY=your-key-here' > .env
```

The `.env` file is gitignored — your key never leaves your machine.

### Run

```bash
# Main tracker (25-min work / 5-min break)
venv/bin/python tracker.py

# Short test session (5-min work / 2-min break)
venv/bin/python tracker.py --work 5 --break 2

# Web dashboard (any browser)
venv/bin/python web_dashboard.py   # → http://localhost:5050

# Floating coaching overlay (separate terminal)
venv/bin/python overlay.py

# Terminal analytics dashboard
venv/bin/python dashboard.py --advice
```

---

## Project Structure

```
adaptive-pomodoro-buddy/
├── tracker.py             # Main loop — CV pipeline, HUD, adaptive rules, demo entry point
├── session_manager.py     # Focus scoring, intervention rules, timer_history logging
├── llm_coach.py           # Gemini API integration (google-genai), async coaching messages
├── noise_detector.py      # sounddevice background thread, RMS → dB measurement
├── analytics.py           # Post-session reports, JSON export, session aggregation
├── web_dashboard.py       # Flask server + API endpoints for the web dashboard
├── dashboard.py           # Terminal analytics dashboard with AI advice
├── overlay.py             # Always-on-top tkinter coaching window
├── templates/
│   └── dashboard.html     # Chart.js web dashboard (dark theme)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Configuration

| Parameter | Default | Location | Description |
|---|---|---|---|
| `--work` | 25 | CLI arg | Work block length in minutes |
| `--break` | 5 | CLI arg | Break length in minutes |
| `EAR_THRESHOLD` | 0.21 | tracker.py | Eye closure threshold for blink detection |
| `SLOUCH_DELTA` | 0.06 | session_manager.py | How far below calibrated baseline = slouching |
| `PRODUCTIVE_APPS` | see code | session_manager.py | Apps that count toward focus score |
| `POSTURE_NUDGE_COOLDOWN` | 120s | session_manager.py | Minimum time between posture nudges |

---

## Evaluation & Limitations

- **Focus score** is a weighted composite: gaze on screen + productive app = 100%, gaze on screen + unknown app = 60%, gaze away = 0%. Approximates engagement, not a direct cognitive measure.
- **Posture baseline** is calibrated at session start — sit up straight for 5 seconds. Shoulder Y-delta threshold avoids false positives from camera angle variation.
- **Phone detection** uses a 3-second accumulator to reduce false positives from brief hand movements. False-positive rate reduced from ~40% (instant gaze heuristic) to <5%.
- **Gaze range** is intentionally wide (iris x: 0.28–0.72) to accommodate natural screen-reading movement without flagging normal eye behavior.
- **Gemini latency** is 0.5–2s. Coaching messages appear once the response returns; no blocking of the video loop.
- **Noise calibration** is relative, not absolute dB SPL. Use values comparatively across sessions, not as a reference measurement.

---

## AI Usage Disclosure

This project uses AI tools throughout:

- **Claude Code (Anthropic)** was used for development assistance, module scaffolding, bug fixing, and documentation throughout this project.
- **Gemini 2.5 Flash Lite** (`models/gemini-2.5-flash-lite`) is called at runtime for personalized coaching messages and dashboard advice.
- **MediaPipe** (Google) provides pre-trained models for face mesh, pose estimation, and hand detection.
- **Chart.js** powers the web dashboard visualizations.

All architectural decisions, feature design, sensor integration choices, and adaptive logic were designed by the author.

---

## License

MIT
