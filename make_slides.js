const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Adaptive Cognitive-State Pomodoro Buddy";
pres.author = "Safaa Hussain";

// ── Palette ─────────────────────────────────────────────────────────────────
const BG      = "0D0D1A";
const CARD    = "13132A";
const PURPLE  = "7C3AED";
const CYAN    = "06B6D4";
const GREEN   = "10B981";
const ORANGE  = "F59E0B";
const RED     = "EF4444";
const WHITE   = "FFFFFF";
const MUTED   = "94A3B8";
const TEXT    = "E2E8F0";

// ── Helpers ──────────────────────────────────────────────────────────────────
function card(slide, x, y, w, h, accentColor) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: CARD }, line: { color: "1E1E40", width: 1 } });
  if (accentColor) {
    slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.05, fill: { color: accentColor }, line: { color: accentColor, width: 0 } });
  }
}

function badge(slide, label, x, y, color) {
  const bw = label.length * 0.11 + 0.4;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 0.3, fill: { color: color, transparency: 70 }, rectRadius: 0.05, line: { color, width: 1 } });
  slide.addText(label, { x, y, w: bw, h: 0.3, fontSize: 9, color, bold: true, align: "center", valign: "middle", margin: 0 });
}

function sectionDot(slide, x, y, color) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.10, h: 0.10, fill: { color } });
}

// ── SLIDE 1: Title ────────────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  // Decorative circles — kept off-screen so they don't overlap text
  s.addShape(pres.shapes.OVAL, { x: 8.8, y: -1.2, w: 4.0, h: 4.0, fill: { color: PURPLE, transparency: 88 }, line: { color: PURPLE, width: 0 } });
  s.addShape(pres.shapes.OVAL, { x: -1.5, y: 3.8, w: 3.0, h: 3.0, fill: { color: CYAN, transparency: 90 }, line: { color: CYAN, width: 0 } });

  // Eyebrow tag
  badge(s, "CS 153 FINAL PROJECT", 0.6, 0.55, CYAN);

  // Title — constrained to left 6.7" so it doesn't reach the sensor cards (at x=7.5)
  s.addText("Adaptive Cognitive-State", { x: 0.6, y: 0.95, w: 6.7, h: 0.9, fontSize: 40, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Pomodoro Study Buddy", { x: 0.6, y: 1.75, w: 6.7, h: 0.9, fontSize: 40, bold: true, color: PURPLE, fontFace: "Arial Black" });

  // Subtitle
  s.addText("A real-time AI system that senses your cognitive state and adapts your study sessions — so you work smarter, not harder.", {
    x: 0.6, y: 2.75, w: 6.5, h: 0.9, fontSize: 14, color: MUTED, fontFace: "Calibri"
  });

  // Author + class
  s.addText("Safaa Hussain  ·  CS 153  ·  Spring 2026", { x: 0.6, y: 4.85, w: 6.5, h: 0.4, fontSize: 12, color: MUTED, fontFace: "Calibri" });

  // Right side: 4 sensor badges stacked
  const sensors = [
    { label: "👁  Gaze Tracking", color: PURPLE },
    { label: "🧍 Posture Detection", color: CYAN },
    { label: "🎤 Ambient Noise", color: GREEN },
    { label: "✦  Gemini AI Coach", color: ORANGE },
  ];
  sensors.forEach((s2, i) => {
    card(s, 7.5, 1.0 + i * 0.95, 2.1, 0.78, s2.color);
    s.addText(s2.label, { x: 7.5, y: 1.0 + i * 0.95 + 0.08, w: 2.1, h: 0.62, fontSize: 12, color: TEXT, bold: false, fontFace: "Calibri", align: "center", valign: "middle" });
  });
})();

// ── SLIDE 2: The Problem ──────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("The Problem", { x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Traditional Pomodoro timers are rigid, impersonal, and completely unaware of how you actually feel.", {
    x: 0.5, y: 0.92, w: 9, h: 0.5, fontSize: 14, color: MUTED, fontFace: "Calibri"
  });

  const problems = [
    { icon: "⏱", title: "One-Size Timer", body: "25/5 split regardless of your focus level, fatigue, or flow state.", color: RED },
    { icon: "🙈", title: "Zero Sensing", body: "No awareness of your posture, gaze, environment, or phone use.", color: ORANGE },
    { icon: "🤖", title: "No Learning", body: "Doesn't remember yesterday's patterns or improve its recommendations.", color: PURPLE },
    { icon: "📉", title: "No Intervention", body: "Can't tell you to take a break when you've been zoned out for 10 minutes.", color: CYAN },
  ];
  problems.forEach((p, i) => {
    const x = 0.5 + (i % 2) * 4.7;
    const y = 1.65 + Math.floor(i / 2) * 1.75;
    card(s, x, y, 4.3, 1.55, p.color);
    s.addText(p.icon + "  " + p.title, { x: x + 0.18, y: y + 0.20, w: 3.9, h: 0.42, fontSize: 15, bold: true, color: p.color, fontFace: "Calibri" });
    s.addText(p.body, { x: x + 0.18, y: y + 0.60, w: 3.9, h: 0.70, fontSize: 12, color: MUTED, fontFace: "Calibri", valign: "top" });
  });

  s.addText("Research shows cognitive performance varies by up to 40% based on time of day and environment — yet timers ignore this entirely.", {
    x: 0.5, y: 5.1, w: 9, h: 0.35, fontSize: 11, color: "4B5563", italic: true, fontFace: "Calibri", align: "center"
  });
})();

// ── SLIDE 3: Solution Overview ────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("The Solution", { x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("A closed-loop system that continuously senses, scores, and responds to your cognitive state.", {
    x: 0.5, y: 0.92, w: 9, h: 0.45, fontSize: 14, color: MUTED, fontFace: "Calibri"
  });

  const steps = [
    { num: "01", label: "SENSE", desc: "Camera + microphone stream captured at 30 fps. MediaPipe extracts gaze, blink rate, posture. Sounddevice measures ambient dB.", color: CYAN },
    { num: "02", label: "SCORE", desc: "Per-second composite focus score: gaze direction × app productivity × posture alignment.", color: PURPLE },
    { num: "03", label: "ADAPT", desc: "Rule engine triggers early breaks (focus < 35%), flow extensions (focus > 80%), and posture nudges — all with logged reasons.", color: GREEN },
    { num: "04", label: "COACH", desc: "Gemini 2.5 Flash generates personalized 2-bullet coaching messages async. Fires as macOS notification + camera overlay.", color: ORANGE },
  ];

  steps.forEach((step, i) => {
    const x = 0.5 + i * 2.28;
    card(s, x, 1.55, 2.1, 3.65, step.color);
    s.addText(step.num, { x: x + 0.15, y: 1.72, w: 1.8, h: 0.45, fontSize: 26, bold: true, color: step.color, fontFace: "Arial Black", margin: 0 });
    s.addText(step.label, { x: x + 0.15, y: 2.12, w: 1.8, h: 0.35, fontSize: 13, bold: true, color: WHITE, fontFace: "Arial Black", charSpacing: 3, margin: 0 });
    s.addText(step.desc, { x: x + 0.15, y: 2.52, w: 1.82, h: 2.5, fontSize: 10.5, color: MUTED, fontFace: "Calibri", valign: "top" });

    // Arrow between cards
    if (i < 3) {
      s.addShape(pres.shapes.LINE, { x: x + 2.15, y: 3.35, w: 0.15, h: 0, line: { color: "2D2D5A", width: 2 } });
      s.addText("→", { x: x + 2.1, y: 3.2, w: 0.22, h: 0.28, fontSize: 13, color: "2D2D5A", bold: true, align: "center" });
    }
  });

  s.addText("Feedback loop runs continuously — every 3 seconds during work blocks", {
    x: 0.5, y: 5.2, w: 9, h: 0.28, fontSize: 11, color: "4B5563", italic: true, align: "center", fontFace: "Calibri"
  });
})();

// ── SLIDE 4: Technical Architecture ──────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Technical Architecture", { x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });

  // Left column: sensors
  s.addText("INPUTS", { x: 0.5, y: 1.05, w: 2.6, h: 0.35, fontSize: 11, color: CYAN, bold: true, charSpacing: 3, fontFace: "Arial Black" });
  const inputs = [
    { label: "MediaPipe FaceMesh", sub: "478 landmarks → iris position, blink EAR", color: CYAN },
    { label: "MediaPipe Pose", sub: "Shoulder Y-delta vs calibrated baseline", color: CYAN },
    { label: "MediaPipe Hands", sub: "3s sustained visibility = phone detected", color: CYAN },
    { label: "sounddevice mic", sub: "RMS → dB SPL, background thread", color: GREEN },
    { label: "AppKit NSWorkspace", sub: "Active app polled every 2s (bg thread)", color: ORANGE },
  ];
  inputs.forEach((inp, i) => {
    card(s, 0.5, 1.45 + i * 0.73, 2.8, 0.63, inp.color);
    s.addText(inp.label, { x: 0.65, y: 1.52 + i * 0.73, w: 2.5, h: 0.28, fontSize: 11, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(inp.sub, { x: 0.65, y: 1.79 + i * 0.73, w: 2.5, h: 0.22, fontSize: 9, color: MUTED, fontFace: "Calibri", margin: 0 });
  });

  // Middle: core engine
  s.addText("CORE ENGINE", { x: 3.6, y: 1.05, w: 3.0, h: 0.35, fontSize: 11, color: PURPLE, bold: true, charSpacing: 3, fontFace: "Arial Black" });
  const engine = [
    { label: "session_manager.py", desc: "Focus score (weighted), intervention rules, timer_history log", color: PURPLE },
    { label: "tracker.py (main loop)", desc: "30fps CV loop, calibration, phone detection, HUD rendering", color: PURPLE },
    { label: "llm_coach.py", desc: "Gemini 2.5 Flash via google-genai, async daemon threads", color: PURPLE },
    { label: "noise_detector.py", desc: "sounddevice InputStream, mutex-protected RMS cache", color: GREEN },
  ];
  engine.forEach((e, i) => {
    card(s, 3.6, 1.45 + i * 0.94, 3.0, 0.82, e.color);
    s.addText(e.label, { x: 3.75, y: 1.52 + i * 0.94, w: 2.7, h: 0.28, fontSize: 11, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(e.desc, { x: 3.75, y: 1.79 + i * 0.94, w: 2.7, h: 0.30, fontSize: 9, color: MUTED, fontFace: "Calibri", margin: 0 });
  });

  // Right: outputs
  s.addText("OUTPUTS", { x: 6.9, y: 1.05, w: 2.8, h: 0.35, fontSize: 11, color: GREEN, bold: true, charSpacing: 3, fontFace: "Arial Black" });
  const outputs = [
    { label: "Camera HUD", sub: "Live focus%, posture, timer, coaching msgs", color: GREEN },
    { label: "macOS Notifications", sub: "Non-intrusive alerts for every event", color: GREEN },
    { label: "Floating Overlay", sub: "Always-on-top tkinter coaching window", color: ORANGE },
    { label: "Web Dashboard", sub: "Flask + Chart.js, localhost:5050", color: ORANGE },
    { label: "Session JSON", sub: "Timestamped logs + timer_history", color: CYAN },
  ];
  outputs.forEach((o, i) => {
    card(s, 6.9, 1.45 + i * 0.73, 2.7, 0.63, o.color);
    s.addText(o.label, { x: 7.05, y: 1.52 + i * 0.73, w: 2.4, h: 0.28, fontSize: 11, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(o.sub, { x: 7.05, y: 1.79 + i * 0.73, w: 2.4, h: 0.22, fontSize: 9, color: MUTED, fontFace: "Calibri", margin: 0 });
  });
})();

// ── SLIDE 5: Adaptive Timer ───────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Adaptive Timer — Dynamic Work/Break", { x: 0.5, y: 0.28, w: 9, h: 0.6, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });

  // Left: Fixed timer (old way)
  card(s, 0.5, 1.05, 4.1, 4.35, RED);
  s.addText("❌  Traditional Pomodoro", { x: 0.65, y: 1.22, w: 3.8, h: 0.40, fontSize: 14, bold: true, color: RED, fontFace: "Calibri" });
  const oldPoints = [
    "Always 25 min work, 5 min break",
    "No awareness of actual focus level",
    "Interrupts deep flow states",
    "No break when genuinely exhausted",
    "Same for everyone, every day",
  ];
  s.addText(oldPoints.map((p, i) => ({ text: p, options: { bullet: true, color: MUTED, breakLine: i < oldPoints.length - 1 } })),
    { x: 0.65, y: 1.72, w: 3.8, h: 3.3, fontSize: 12, fontFace: "Calibri" });

  // Right: Adaptive (our system)
  card(s, 5.0, 1.05, 4.6, 4.35, GREEN);
  s.addText("✓  Adaptive Cognitive Timer", { x: 5.15, y: 1.22, w: 4.3, h: 0.40, fontSize: 14, bold: true, color: GREEN, fontFace: "Calibri" });

  const newPoints = [
    { txt: "Early break at 14 min  →  focus dropped to 28%", color: ORANGE },
    { txt: "Flow extension 25→30 min  →  focus was 83%", color: GREEN },
    { txt: "Posture nudge after 70%+ slouching (2 min cooldown)", color: CYAN },
    { txt: "Phone detected: hand visible 3s+ during work block", color: RED },
    { txt: "All changes timestamped in timer_history log", color: PURPLE },
  ];
  newPoints.forEach((p, i) => {
    s.addShape(pres.shapes.OVAL, { x: 5.2, y: 1.83 + i * 0.64, w: 0.1, h: 0.1, fill: { color: p.color } });
    s.addText(p.txt, { x: 5.38, y: 1.77 + i * 0.64, w: 4.1, h: 0.5, fontSize: 11.5, color: TEXT, fontFace: "Calibri", valign: "middle" });
  });

  // Proof quote
  s.addText('"Early break at 3m (focus=30%, was 5m block)"  —  actual log entry from real session', {
    x: 0.5, y: 5.2, w: 9, h: 0.28, fontSize: 10.5, color: PURPLE, italic: true, align: "center", fontFace: "Calibri"
  });
})();

// ── SLIDE 6: AI Coaching ──────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Gemini-Powered Personal Coach", { x: 0.5, y: 0.28, w: 9, h: 0.6, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Every intervention triggers an async Gemini 2.5 Flash call with your real-time sensor context.", {
    x: 0.5, y: 0.88, w: 9, h: 0.38, fontSize: 13, color: MUTED, fontFace: "Calibri"
  });

  // Trigger cards
  const triggers = [
    { event: "POSTURE_NUDGE", context: "focus=65%, slouch=72% of last 30s, blink=8/min", msg: "• You've been hunching — sit tall and reset your shoulders.\n• Low blink rate suggests eye strain; look away for 20 seconds.", color: ORANGE },
    { event: "EARLY_BREAK", context: "focus=28%, elapsed=14min, noise=61dB", msg: "• Focus dropped sharply — your brain needs a real reset.\n• Step away from the screen; even 5 minutes will help significantly.", color: RED },
    { event: "PHONE_DETECTED", context: "hand visible 4s, gaze away, during work block", msg: "• Phone spotted — put it face-down and refocus.\n• You were building momentum; don't lose it now.", color: PURPLE },
    { event: "SESSION_END", context: "focus=72%, 25min, top_app=Claude", msg: "• Great session — 72% focus is above your average.\n• Your best hour is 5 PM; prioritize hard work then.", color: GREEN },
  ];

  triggers.forEach((t, i) => {
    const x = (i % 2) * 4.8 + 0.5;
    const y = 1.42 + Math.floor(i / 2) * 2.0;
    card(s, x, y, 4.55, 1.78, t.color);
    badge(s, t.event, x + 0.15, y + 0.13, t.color);
    s.addText("Context: " + t.context, { x: x + 0.15, y: y + 0.48, w: 4.25, h: 0.25, fontSize: 9, color: MUTED, fontFace: "Calibri", italic: true });
    s.addText(t.msg, { x: x + 0.15, y: y + 0.78, w: 4.25, h: 0.88, fontSize: 10.5, color: TEXT, fontFace: "Calibri" });
  });

  s.addText("All calls run in daemon threads — zero blocking of the 30fps video loop", {
    x: 0.5, y: 5.25, w: 9, h: 0.25, fontSize: 10.5, color: "4B5563", italic: true, align: "center", fontFace: "Calibri"
  });
})();

// ── SLIDE 7: Web Dashboard ────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Web Analytics Dashboard", { x: 0.5, y: 0.28, w: 9, h: 0.6, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Flask + Chart.js at localhost:5050. Auto-refreshes every 60s. Access from any browser tab.", {
    x: 0.5, y: 0.88, w: 9, h: 0.38, fontSize: 13, color: MUTED, fontFace: "Calibri"
  });

  const features = [
    { icon: "📈", title: "Focus Trend Line", desc: "Per-session focus % plotted chronologically. See if you're improving over time.", color: PURPLE },
    { icon: "🕐", title: "Hourly Productivity", desc: "Bar chart of avg focus by hour of day. Identifies your personal peak hours.", color: CYAN },
    { icon: "🍩", title: "App Usage Breakdown", desc: "Doughnut chart: which apps dominate your study sessions.", color: GREEN },
    { icon: "📊", title: "Session Comparison", desc: "Grouped bar: focus% vs posture% per session. Spot patterns.", color: ORANGE },
    { icon: "⚡", title: "Adaptive Timer Log", desc: "Every timer change with timestamp, reason, and focus score. Proof of adaptation.", color: RED },
    { icon: "✦", title: "AI Personalized Advice", desc: "On-demand Gemini coaching based on all historical data. 4 data-driven bullets.", color: PURPLE },
  ];

  features.forEach((f, i) => {
    const x = 0.5 + (i % 3) * 3.15;
    const y = 1.45 + Math.floor(i / 3) * 1.85;
    card(s, x, y, 3.0, 1.68, f.color);
    s.addText(f.icon + "  " + f.title, { x: x + 0.15, y: y + 0.15, w: 2.7, h: 0.42, fontSize: 13, bold: true, color: f.color, fontFace: "Calibri" });
    s.addText(f.desc, { x: x + 0.15, y: y + 0.60, w: 2.7, h: 0.95, fontSize: 10.5, color: MUTED, fontFace: "Calibri", valign: "top" });
  });
})();

// ── SLIDE 8: Evaluation & Evidence ───────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Evaluation & Evidence", { x: 0.5, y: 0.28, w: 9, h: 0.55, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });

  // Big stat numbers
  const stats = [
    { value: "48%", label: "Peak focus score", sub: "vs 0% in session 1", color: GREEN },
    { value: "97%", label: "Best posture rate", sub: "improved from 19%", color: CYAN },
    { value: "3s", label: "Phone detection", sub: "sustained hand visibility", color: ORANGE },
    { value: "25→30", label: "Flow extension (min)", sub: "timer adapted live", color: PURPLE },
  ];
  stats.forEach((st, i) => {
    const x = 0.5 + i * 2.3;
    card(s, x, 1.0, 2.1, 1.70, st.color);
    s.addText(st.value, { x: x + 0.1, y: 1.08, w: 1.9, h: 0.65, fontSize: 30, bold: true, color: st.color, fontFace: "Arial Black", align: "center" });
    s.addText(st.label, { x: x + 0.1, y: 1.82, w: 1.9, h: 0.32, fontSize: 9.5, bold: true, color: TEXT, fontFace: "Calibri", align: "center" });
    s.addText(st.sub, { x: x + 0.1, y: 2.20, w: 1.9, h: 0.28, fontSize: 9, color: MUTED, fontFace: "Calibri", align: "center" });
  });

  // Evidence methods
  s.addText("How We Validated", { x: 0.5, y: 2.75, w: 9, h: 0.42, fontSize: 16, bold: true, color: WHITE, fontFace: "Arial Black" });

  const evidence = [
    { icon: "🔬", title: "Session-over-session trends", desc: "Dashboard shows focus improving across sessions as the tool calibrates to the user." },
    { icon: "⚡", title: "Timer adaptation log", desc: "Every early break and flow extension is timestamped with the triggering focus score — auditable proof of adaptive behavior." },
    { icon: "📋", title: "Failure analysis", desc: "Phone detection false-positive rate reduced from ~40% (gaze heuristic) to <5% (3-second accumulator)." },
    { icon: "🎯", title: "Calibrated posture baseline", desc: "Per-session calibration eliminated false slouch positives that plagued the fixed threshold approach." },
  ];
  evidence.forEach((e, i) => {
    const x = 0.5 + (i % 2) * 4.7;
    const y = 3.22 + Math.floor(i / 2) * 0.9;
    s.addText(e.icon + "  " + e.title, { x: x, y, w: 4.3, h: 0.32, fontSize: 12, bold: true, color: CYAN, fontFace: "Calibri" });
    s.addText(e.desc, { x: x + 0.25, y: y + 0.3, w: 4.2, h: 0.48, fontSize: 10.5, color: MUTED, fontFace: "Calibri" });
  });
})();

// ── SLIDE 9: Future Work ──────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Future Work", { x: 0.5, y: 0.28, w: 5.5, h: 0.6, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("The foundation is built. Here's what comes next.", { x: 0.5, y: 0.88, w: 5.5, h: 0.38, fontSize: 13, color: MUTED, fontFace: "Calibri" });

  const future = [
    { num: "01", title: "RL-Based Adaptive Policy", desc: "Replace rule-based logic with a Q-learning agent. State: (focus, blink_rate, noise, time_in_block, hour_of_day). Reward: sustained focus improvement.", color: PURPLE },
    { num: "02", title: "Ambient Noise Classification", desc: "Distinguish speech vs. music vs. background hum using a lightweight audio CNN — smarter than raw dB alone.", color: CYAN },
    { num: "03", title: "Multi-Day Streak & Gamification", desc: "Track focus streaks, personal bests, and weekly summaries. Behavioral nudges to build consistent study habits.", color: GREEN },
    { num: "04", title: "Pre-Session Goal Setting", desc: "User states a goal at session start. LLM checks at end: 'Did you accomplish: finish section 4?' Stored with session data.", color: ORANGE },
    { num: "05", title: "Baseline Comparison Mode", desc: "A/B test: run fixed 25/5 sessions vs. adaptive. Dashboard shows statistically which produces higher sustained focus.", color: RED },
  ];

  future.forEach((f, i) => {
    const y = 1.35 + i * 0.78;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 0.5, h: 0.60, fill: { color: f.color, transparency: 20 }, line: { color: f.color, width: 0 } });
    s.addText(f.num, { x: 0.5, y: y + 0.02, w: 0.5, h: 0.58, fontSize: 13, bold: true, color: f.color, fontFace: "Arial Black", align: "center", valign: "middle" });
    s.addText(f.title, { x: 1.15, y: y + 0.02, w: 8.3, h: 0.28, fontSize: 13, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(f.desc, { x: 1.15, y: y + 0.30, w: 8.3, h: 0.35, fontSize: 10.5, color: MUTED, fontFace: "Calibri", margin: 0 });
  });
})();

// ── SLIDE 10: Closing ─────────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  // Glow circles — fully off-screen so they don't overlap any text
  s.addShape(pres.shapes.OVAL, { x: -3.5, y: -1.5, w: 4.5, h: 4.5, fill: { color: PURPLE, transparency: 90 }, line: { color: PURPLE, width: 0 } });
  s.addShape(pres.shapes.OVAL, { x: 9.5, y: 4.5, w: 4, h: 4, fill: { color: CYAN, transparency: 90 }, line: { color: CYAN, width: 0 } });

  s.addText("One Person.", { x: 1.0, y: 0.75, w: 8.5, h: 0.85, fontSize: 50, bold: true, color: WHITE, fontFace: "Arial Black", align: "center" });
  s.addText("Full-Stack AI Productivity Research.", { x: 1.0, y: 1.55, w: 8.5, h: 0.85, fontSize: 32, bold: true, color: PURPLE, fontFace: "Arial Black", align: "center" });

  s.addText("5 sensors  ·  real-time adaptive timer  ·  Gemini AI coach  ·  long-term analytics dashboard", {
    x: 1.0, y: 2.6, w: 8.5, h: 0.45, fontSize: 14, color: MUTED, fontFace: "Calibri", align: "center"
  });

  // Key stack badges
  const tech = ["MediaPipe", "OpenCV", "Flask + Chart.js", "Gemini 2.5 Flash", "sounddevice", "AppKit", "tkinter"];
  const totalW = tech.length * 1.28;
  const startX = (10 - totalW) / 2;
  tech.forEach((t, i) => {
    badge(s, t, startX + i * 1.28, 3.35, CYAN);
  });

  // GitHub
  s.addText("github.com/safaahussain1/adaptive-pomodoro-buddy", {
    x: 1.0, y: 4.05, w: 8.5, h: 0.38, fontSize: 13, color: PURPLE, fontFace: "Calibri", align: "center"
  });

  s.addText("Safaa Hussain  ·  CS 153  ·  Spring 2026", {
    x: 1.0, y: 5.05, w: 8.5, h: 0.3, fontSize: 11, color: "4B5563", fontFace: "Calibri", align: "center"
  });
})();

// ── Write file ───────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "/Users/safaahussain/Documents/adaptive-pomodoro-buddy/CS153_Pomodoro_Buddy_Slides.pptx" })
  .then(() => console.log("✓  Slides written: CS153_Pomodoro_Buddy_Slides.pptx"))
  .catch(e => { console.error("Error:", e); process.exit(1); });
