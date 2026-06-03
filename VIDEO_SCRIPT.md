# CS 153 Project Video Script
**"Adaptive Cognitive-State Pomodoro Study Buddy"**
Target length: ≤ 3 minutes | Format: voiceover + screen recordings

---

## Before You Record — Setup Checklist

1. Run test mode so you can see all features in < 3 minutes:
   ```
   venv/bin/python tracker.py --work 2 --break 1
   ```
2. Open the web dashboard in a browser tab:
   ```
   venv/bin/python web_dashboard.py   →   http://localhost:5050
   ```
3. Open `overlay.py` in a third terminal:
   ```
   venv/bin/python overlay.py
   ```
4. Have Claude or VS Code open in the background so the "App" reads as something real.

### How to trigger every demo moment on cue

| Feature to show | How to force it |
|---|---|
| Calibration phase | It always runs 5s at startup — just wait |
| Focus score rising | Look directly at the camera with Claude open |
| Posture nudge | Slump shoulders down hard for 30+ seconds |
| Phone detection | Hold your hand up in frame for 3 seconds |
| Early break (focus↓) | Use `--work 2`, look away from screen repeatedly for ~1 min |
| Flow extension (focus↑) | Use `--work 2`, stare at camera with Claude open in last 30s |
| Transition overlay + sound | Wait for the 2-minute timer to expire naturally |
| Break UI (green screen) | Automatically appears after work→break transition |
| macOS notification | Fires automatically — visible in any screen recording |
| Dashboard timer log | Run a session to completion, refresh dashboard |
| Dashboard advice bullets | Click "Refresh Advice" button |

---

## Full Script

---

### SCENE 1 — [SLIDE 1: Title] — 0:00–0:12
**Q1: Why did you build this?**

> "The Pomodoro technique has been around for 35 years. Work 25 minutes, take a 5-minute break. It's a great idea — but it has one fatal flaw. It has no idea who you are."

*Show slide 1 with the 5 sensor cards on the right.*

---

### SCENE 2 — [SLIDE 2: The Problem] — 0:12–0:35
**Q1 continued — bottlenecks identified**

> "It doesn't know if your focus completely collapsed 10 minutes in. It doesn't know your environment is too loud to concentrate. It doesn't know you're on your phone. And it will never know that you personally focus best at 5 PM after a cup of coffee. I found myself sitting at my desk for hours, going through the motions of studying, with nothing to show for it — and no tool could tell me why."

*Hover over each problem card as you mention it.*

---

### SCENE 3 — [SLIDE 4: Architecture] — 0:35–0:58
**Q2: Product architecture and deployment**

> "The architecture is fully local — no video ever leaves your machine. Everything runs in a single Python process on your laptop. At the core is a 30-frames-per-second OpenCV loop on the main thread. Three background threads run in parallel: a microphone thread measuring ambient noise every 200ms, an AppKit thread polling the active window every 2 seconds, and whenever an intervention fires, a daemon thread makes an async call to the Gemini API so the video loop is never blocked."

*Show Slide 4 — the three-column architecture diagram. Point to INPUTS → CORE ENGINE → OUTPUTS.*

> "Session data is written to local JSON files after each session. The web dashboard is a Flask server that reads those files — so you can leave it running in a browser tab all day and it auto-refreshes. There's no cloud, no account, no data leaving your computer. The only external call is to Gemini when a coaching message is triggered."

*Still on Slide 4 or briefly show the session JSON structure in a terminal.*

---

### SCENE 4 — [SCREEN RECORDING: tracker.py running] — 0:58–1:18
**Q2 continued — live sensing pipeline**

> "So here's what it looks like in practice. I run one command — `python tracker.py` — and a webcam window opens with a 5-second posture calibration that sets my personal baseline. Then it starts tracking. That face mesh overlay is 478 landmarks running in real time to extract gaze direction and blink rate. The skeleton is shoulder alignment — if my shoulders drop more than 6% below my calibrated baseline, it flags slouching."

*Show the camera window: face mesh overlay, posture skeleton, focus score ticking up. Point out each element on screen.*

---

### SCENE 5 — [DEMO: trigger posture nudge — slouch 30s] — 1:18–1:32
**Q2 continued — intervention system**
**Q2 continued — intervention system**

> "Every 3 seconds, the system evaluates your state against a set of adaptive rules. If I've been slouching for too long — watch what happens."

*Slouch down. After ~30 seconds, the camera overlay and macOS notification both appear.*

> "Gemini generates a personalized 2-bullet coaching message with your exact context — focus score, blink rate, noise level — all factored in. And it fires as a macOS notification so you see it even if you're in another tab."

*Point out the notification banner and the text overlay on the camera feed.*

---

### SCENE 5 — [DEMO: hold hand up 3 seconds] — 1:32–1:38
**Q2 continued — phone detection**

> "And if a hand stays visible in frame for more than 3 seconds during a work block, it flags phone use."

*Hold hand up. Show "PHONE DETECTED" appearing on HUD and as a notification.*

---

### SCENE 6 — [DEMO: wait for transition overlay + sound] — 1:38–1:55
**Q2 continued — adaptive timer + break UI**

> "The timer itself adapts. When focus drops below 35% past the halfway point, an early break is triggered before the clock runs out. When I'm in deep flow, it extends automatically. And at every transition, there's an 8-second overlay with an audible tone — I can press E to cancel the break and stay in the zone."

*Let the 2-minute timer expire. Show the full-screen "BREAK TIME!" overlay and chime. Then show the distinct green break UI with a relaxation tip.*

---

### SCENE 7 — [SCREEN RECORDING: web dashboard] — 1:55–2:22
**Q2 continued — data layer, deployment, and AI personalization**

> "Everything is local-first. No cloud, no account. Session data writes to JSON files on your machine after each session. The web dashboard is a Flask server that reads those files — you run it once and open it in any browser tab. It shows your focus trend over time, which hour of day you personally peak, your app breakdown, and the adaptive timer log — every early break and flow extension timestamped with the triggering focus score. That's the auditable proof that the timer is dynamically adjusting."

*Scroll through the dashboard: focus trend chart → hourly productivity bar chart → adaptive timer log with real entries.*

> "On demand, Gemini reads your entire session history and generates personalized coaching advice — not generic tips, but data-driven observations about your specific patterns."

*Click Refresh Advice. Show 4 bullet points loading and appearing.*

---

### SCENE 8 — [SLIDE 9: Use Cases] — 2:22–2:38
**Q3: Potential use cases and impact**

> "This extends well beyond students. Remote workers can get data-backed evidence that their home environment is hurting focus. Researchers can use it as a non-invasive cognitive load sensor. Long-term blink rate and posture trends could surface early fatigue or burnout indicators before they become serious. My vision is a lightweight background agent that builds a true map of your cognitive patterns over weeks — not just one session."

*Show slide 9 with the 4 use case cards.*

---

### SCENE 9 — [SLIDE 10: Future Work] — 2:38–2:52
**Q4: What more would you add?**

> "At the top of my list: replacing the rule-based logic with a reinforcement learning policy that learns your optimal session lengths from your own history. And a baseline A/B mode — fixed 25/5 sessions alongside adaptive ones, on the same user, measuring which actually produces higher sustained focus. The sensor infrastructure is built. The data is already being collected."

*Walk through the numbered list on slide 10.*

---

### SCENE 10 — [SLIDE 11: Closing] — 2:52–3:00

> "One person, one laptop, five sensors, a free API key, and a real problem worth solving."

---

## Recording Tips

- **Screen record at 1080p or higher** — the dashboard and camera window need to be legible
- **Do scenes 4–7 in one continuous recording** — starting the tracker once and going through all demo moments in sequence looks most natural; switch to the browser for Scene 7
- **The macOS notification** appears automatically in the top-right corner — it will be captured in your screen recording without any extra effort
- **If Gemini is rate-limited**, the fallback messages ("Put the phone down — you're in a work block. Refocus!") are clean and fine to use in the video
- **For the dashboard recording**, scroll slowly — the Chart.js charts animate on load which looks great on camera
- **Slides are in:** `CS153_Pomodoro_Buddy_Slides.pptx` in the project folder — open with PowerPoint or Keynote

---

## Slide → Script Mapping (quick reference)

| Slide | Content | Scene # | Q |
|---|---|---|---|
| 1 | Title + 5 sensors | 1 | Q1 |
| 2 | The Problem | 2 | Q1 |
| 3 | Solution: SENSE→SCORE→ADAPT→COACH | — | (reference only) |
| **4** | **Technical Architecture** | **3** | **Q2 — architecture** |
| 5 | Adaptive timer: 4 decision rules | — | (reference only) |
| 6 | AI coaching examples | — | (reference only) |
| 7 | Web dashboard features | — | (reference only) |
| 8 | Evaluation & evidence | — | (reference only) |
| 9 | Use cases & impact | 8 | Q3 |
| 10 | Future work | 9 | Q4 |
| 11 | Closing | 10 | — |

> **Note on timing:** this script is approximately 3:05 — trim Scene 3 voiceover slightly if needed, or cut to the dashboard recording right after the architecture diagram without elaborating on the JSON structure.

> Slides 3–8 are for reference and deeper explanation — you don't need to show all of them in the 3-minute video. The live demo covers what they describe better than showing the slides would.
