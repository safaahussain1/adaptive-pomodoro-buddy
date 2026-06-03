# Adaptive Cognitive-State Pomodoro Buddy

A real-time, AI-powered productivity tool that continuously senses your cognitive state — gaze, posture, blink rate, and ambient noise — and dynamically adapts your study/break intervals using a rule-based adaptive engine and a Claude-powered personal coach.

---

## Demo

> Run `python tracker.py` — a webcam window appears showing your live focus density, posture status, ambient noise level, and an adaptive Pomodoro timer. When focus drops or posture slips, Claude generates a personalized coaching message directly on screen.

---

## Features

| Sensor / Module | What it tracks |
|---|---|
| **Gaze tracking** (MediaPipe FaceMesh) | Whether your eyes are on-screen or looking away |
| **Posture detection** (MediaPipe Pose) | Shoulder alignment to detect slouching |
| **Blink rate** (EAR algorithm) | Eye Aspect Ratio for fatigue indication |
| **Active app** (macOS AppKit) | Whether the foreground app is productive |
| **Ambient noise** (microphone + sounddevice) | Background dB level that correlates with distraction |

### Adaptive timer logic

- **Early break**: if focus < 35% past the halfway point of a work block, an early break is triggered
- **Flow extension**: if focus ≥ 85% when the timer is about to end, the work session is extended 5 minutes
- **Posture nudge**: if slouching > 70% of the last 30 seconds, an alert fires

### LLM coaching (Claude Haiku)

Every intervention triggers an async call to Claude Haiku (`claude-haiku-4-5-20251001`). Claude receives your current focus score, app usage, blink rate, and noise level, and writes a warm, specific 2–3 sentence coaching message displayed as an overlay on the video feed. An end-of-session summary message is also generated.

### Session analytics

At the end of each session, a detailed report is printed to the terminal and saved as `session_<timestamp>.json`:
- Overall and work-only focus percentages
- Good posture rate
- Average ambient noise
- App usage breakdown

---

## Setup

### Prerequisites

- Python 3.11+
- macOS (for active-window detection via AppKit; Linux/Windows users can remove that feature)
- A webcam and microphone
- An Anthropic API key

### Install

```bash
git clone https://github.com/safaahussain1/adaptive-pomodoro-buddy
cd adaptive-pomodoro-buddy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Run

```bash
python tracker.py
```

Press **Q** to stop the session and view the analytics report.

---

## Project Structure

```
adaptive-pomodoro-buddy/
├── tracker.py            # Main entry point — webcam loop, display, wires everything together
├── session_manager.py    # Pomodoro timer, per-frame data logging, intervention rules
├── llm_coach.py          # Claude API integration for personalized coaching messages
├── noise_detector.py     # Background microphone thread measuring ambient dB
├── analytics.py          # Post-session summary and JSON report generation
├── requirements.txt
└── README.md
```

---

## Architecture

```
Webcam (30 fps)
    │
    ▼
MediaPipe FaceMesh ──► gaze_status, EAR (blink)
MediaPipe Pose     ──► posture_status
                             │
Microphone ──► noise_detector.py (background thread)
macOS AppKit ──► active window (1 Hz polling)
                             │
                             ▼
                    session_manager.py
                    ┌────────────────────────────────────┐
                    │  log_frame_state()  → history_logs │
                    │  compute_focus_score()              │
                    │  evaluate_interventions()           │
                    │    • POSTURE_NUDGE                  │
                    │    • EARLY_BREAK                    │
                    │    • FLOW_EXTENSION                 │
                    └──────────────┬─────────────────────┘
                                   │ trigger + context
                                   ▼
                            llm_coach.py
                            Claude Haiku API call (async thread)
                                   │
                                   ▼
                          coaching message overlay
                          displayed on video feed
                                   │
                          (on Q press)
                                   ▼
                            analytics.py
                            terminal report + session_<ts>.json
```

---

## Configuration

You can adjust these constants in `tracker.py` and `session_manager.py`:

| Parameter | Default | Description |
|---|---|---|
| `work_duration_mins` | 25 | Standard work block length |
| `break_duration_mins` | 5 | Standard break length |
| `EAR_THRESHOLD` | 0.21 | Eye closure threshold for blink detection |
| `LLM_DISPLAY_SECONDS` | 10 | How long coaching messages stay on screen |
| `productive_apps` | see code | Apps counted as productive for focus score |

---

## Evaluation & Limitations

- **Focus score** is a composite of gaze direction + productive app usage, sampled at 1 Hz. It approximates cognitive engagement rather than measuring it directly.
- **Blink rate** interpretation: typical range is 15–20 blinks/min; sustained low rates may indicate screen fatigue; very high rates may indicate sleepiness.
- **Noise calibration**: the dB estimate from `sounddevice` is relative, not absolute. Treat thresholds as relative indicators, not acoustic measurements.
- **Posture**: shoulder Y-position threshold (0.65 in normalized coordinates) was empirically tuned — may need adjustment depending on camera angle and seating height.
- **LLM latency**: Claude Haiku responses take ~0.5–2 s. The coaching message appears on screen once the response returns, with no blocking of the video loop.

---

## AI Usage Disclosure

This project makes extensive use of AI tools:

- **Claude Code (Anthropic)** was used to scaffold modules, implement the noise detector, analytics reporter, and LLM coach integration, and to write this README.
- **Claude Haiku** (`claude-haiku-4-5-20251001`) is called at runtime for personalized coaching messages.
- **MediaPipe** (Google) provides pre-trained models for face mesh and pose estimation.

All substantial architectural decisions, feature selection, sensor integration, and adaptive logic design were made by the author.

---

## License

MIT
