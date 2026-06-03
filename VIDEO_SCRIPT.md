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

### SCENE 3 — [SCREEN RECORDING: tracker.py running] — 0:35–1:00
**Q2: How exactly does it work? — Sensing pipeline**

> "So I built a tool that actually looks at you while you study. It uses Google MediaPipe to track your gaze direction and blink rate through your webcam — detecting both focus and fatigue. It reads your shoulder alignment to detect slouching. Your microphone measures ambient noise levels every second. And your active application is monitored in the background."

*Show the camera window: face mesh overlay visible, posture skeleton, focus score ticking up as you look at camera with a productive app open.*

---

### SCENE 4 — [DEMO: trigger posture nudge — slouch 30s] — 1:00–1:15
**Q2 continued — intervention system**

> "Every 3 seconds, the system evaluates your state against a set of adaptive rules. If I've been slouching for too long — watch what happens."

*Slouch down. After ~30 seconds, the camera overlay and macOS notification both appear.*

> "Gemini generates a personalized 2-bullet coaching message with your exact context — focus score, blink rate, noise level — all factored in. And it fires as a macOS notification so you see it even if you're in another tab."

*Point out the notification banner and the text overlay on the camera feed.*

---

### SCENE 5 — [DEMO: hold hand up 3 seconds] — 1:15–1:22
**Q2 continued — phone detection**

> "If a hand stays visible in the frame for more than 3 seconds during a work block, it flags potential phone use."

*Hold hand up. Show "PHONE DETECTED" appearing.*

---

### SCENE 6 — [DEMO: wait for transition overlay + sound] — 1:22–1:40
**Q2 continued — adaptive timer + break UI**

> "Here's the heart of the system — the timer itself adapts. When focus drops below 35% past the halfway point of a block, it triggers an early break before the timer expires. When I'm in deep flow, it extends the session automatically. And when a block ends, there's an 8-second transition with an audible tone — and I can press E to stay in the zone if I'm not ready to stop."

*Let the 2-minute work timer expire. Show the full-screen "BREAK TIME!" overlay with countdown and chime sound. Then show the green break UI with relaxation tip.*

---

### SCENE 7 — [SCREEN RECORDING: switch to web dashboard] — 1:40–2:10
**Q2 continued — architecture & long-term analytics**

> "All of this data feeds into a persistent web dashboard I built with Flask and Chart.js. You can see your focus trend across sessions, which hour of day you personally perform best, your app usage breakdown — and most importantly, the adaptive timer log. Every early break and flow extension is recorded here with a timestamp and the exact focus score that triggered it. This is the proof that the system isn't just running a fixed timer."

*Scroll through the dashboard: focus trend chart → hourly productivity → adaptive timer log showing entries like "Early break at 3m (focus=30%)".*

---

### SCENE 8 — [DEMO: click Refresh Advice] — 2:10–2:22
**Q2 continued — AI personalization**

> "And on demand, Gemini analyzes all your historical session data and generates personalized advice — specific to your patterns. Not generic tips."

*Click the button. Show 4 bullets appearing one by one.*

---

### SCENE 9 — [SLIDE 9: Use Cases] — 2:22–2:38
**Q3: Potential use cases and impact**

> "This tool is useful beyond just students. Remote workers can get data-backed evidence that home office noise is hurting their output. Researchers can use it as a non-invasive cognitive load sensor. Long-term, blink rate and posture trends could surface early burnout indicators before they become serious. My vision is a lightweight background agent that builds a true map of your cognitive patterns over weeks — not just individual sessions."

*Show slide 9 with the 4 use case cards.*

---

### SCENE 10 — [SLIDE 10: Future Work] — 2:38–2:52
**Q4: What more would you add?**

> "There's a lot more I'd build with more time. At the top of my list: replacing the rule-based logic with a reinforcement learning policy that learns your optimal session lengths from your own data. And a baseline A/B comparison mode — running fixed 25/5 sessions alongside adaptive ones and measuring which actually produces higher focus. The foundation is here. The data is being collected."

*Walk through numbered items on slide 10.*

---

### SCENE 11 — [SLIDE 11: Closing] — 2:52–3:00

> "One person, one laptop, five sensors, a Gemini API key, and a real problem worth solving."

---

## Recording Tips

- **Screen record at 1080p or higher** — the dashboard and camera window need to be legible
- **Do scenes 4–8 in one continuous recording** — starting the tracker once and going through all demo moments in sequence looks most natural
- **The macOS notification** appears automatically in the top-right corner — it will be captured in your screen recording without any extra effort
- **If Gemini is rate-limited**, the fallback messages ("Put the phone down — you're in a work block. Refocus!") are clean and fine to use in the video
- **For the dashboard recording**, scroll slowly — the Chart.js charts animate on load which looks great on camera
- **Slides are in:** `CS153_Pomodoro_Buddy_Slides.pptx` in the project folder — open with PowerPoint or Keynote

---

## Slide → Script Mapping (quick reference)

| Slide | Content | Scene # | Q |
|---|---|---|---|
| 1 | Title + 5 sensors | 1 | Q1 |
| 2 | The problem | 2 | Q1 |
| 3 | Solution: SENSE→SCORE→ADAPT→COACH | — | (reference only) |
| 4 | Technical architecture | — | (reference only) |
| 5 | Adaptive timer: 4 decision rules | — | (show during scene 6 if time) |
| 6 | AI coaching examples | — | (reference only) |
| 7 | Web dashboard features | — | (reference only) |
| 8 | Evaluation & evidence | — | (reference only) |
| 9 | Use cases & impact | 9 | Q3 |
| 10 | Future work | 10 | Q4 |
| 11 | Closing | 11 | — |

> Slides 3–8 are for reference and deeper explanation — you don't need to show all of them in the 3-minute video. The live demo covers what they describe better than showing the slides would.
