const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Adaptive Cognitive-State Pomodoro Buddy";
pres.author = "Safaa Hussain";

const BG     = "0D0D1A";
const CARD   = "13132A";
const PURPLE = "7C3AED";
const CYAN   = "06B6D4";
const GREEN  = "10B981";
const ORANGE = "F59E0B";
const RED    = "EF4444";
const WHITE  = "FFFFFF";
const MUTED  = "94A3B8";
const TEXT   = "E2E8F0";

function card(s, x, y, w, h, accent) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: CARD }, line: { color: "1E1E40", width: 1 } });
  if (accent) s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.05, fill: { color: accent }, line: { color: accent, width: 0 } });
}
function badge(s, label, x, y, color) {
  const bw = label.length * 0.10 + 0.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 0.28, fill: { color: color, transparency: 72 }, rectRadius: 0.04, line: { color, width: 1 } });
  s.addText(label, { x, y, w: bw, h: 0.28, fontSize: 8.5, color, bold: true, align: "center", valign: "middle", margin: 0 });
}

// ── SLIDE 1: Title ───────────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  // Eyebrow
  badge(s, "CS 153 FINAL PROJECT", 0.55, 0.48, CYAN);

  // Title in one combined text box — prevents line-2 from crashing into line-1
  s.addText([
    { text: "Adaptive Cognitive-State\n", options: { color: WHITE,  fontSize: 30, bold: true, breakLine: false } },
    { text: "Pomodoro Study Buddy",        options: { color: PURPLE, fontSize: 30, bold: true } },
  ], { x: 0.55, y: 0.88, w: 5.85, h: 1.52, fontFace: "Arial Black", valign: "top" });

  s.addText("A real-time AI system that senses your cognitive state\nand dynamically adapts your Pomodoro study sessions.", {
    x: 0.55, y: 2.50, w: 5.8, h: 0.82, fontSize: 13, color: MUTED, fontFace: "Calibri"
  });
  s.addText("Safaa Hussain  ·  CS 153  ·  Spring 2026", { x: 0.55, y: 4.95, w: 5.8, h: 0.38, fontSize: 11, color: MUTED, fontFace: "Calibri" });

  // Divider
  s.addShape(pres.shapes.RECTANGLE, { x: 6.55, y: 0.4, w: 0.025, h: 4.8, fill: { color: "1E1E40" }, line: { color: "1E1E40", width: 0 } });

  // Right: sensor cards — start at x=6.70, safely to the right of all title text
  const sensors = [
    { label: "👁  Gaze Tracking",    color: PURPLE },
    { label: "🧍 Posture Detection", color: CYAN },
    { label: "🎤 Ambient Noise",     color: GREEN },
    { label: "📱 Phone Detection",   color: ORANGE },
    { label: "✦  Gemini AI Coach",  color: RED },
  ];
  sensors.forEach((sen, i) => {
    card(s, 6.70, 0.42 + i * 1.02, 3.0, 0.88, sen.color);
    s.addText(sen.label, { x: 6.70, y: 0.42 + i * 1.02 + 0.10, w: 3.0, h: 0.68, fontSize: 12.5, color: TEXT, fontFace: "Calibri", align: "center", valign: "middle" });
  });
})();

// ── SLIDE 2: The Problem ─────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("The Problem", { x: 0.5, y: 0.28, w: 9, h: 0.58, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Traditional Pomodoro timers are rigid, impersonal, and blind to how you actually feel.", {
    x: 0.5, y: 0.88, w: 9, h: 0.42, fontSize: 13, color: MUTED, fontFace: "Calibri"
  });
  const problems = [
    { icon: "⏱", title: "One-Size Timer",    body: "25/5 split for everyone, every day. No awareness of your actual energy or flow state.", color: RED },
    { icon: "🙈", title: "Zero Sensing",      body: "Ignores your posture, gaze, phone usage, and environment entirely.", color: ORANGE },
    { icon: "🤖", title: "No Learning",       body: "Doesn't remember that you focus best at 5 PM or that loud noise tanks your attention.", color: PURPLE },
    { icon: "📉", title: "No Intervention",   body: "Won't shorten a session when you've been distracted for 10 minutes — or extend one when you're in flow.", color: CYAN },
  ];
  problems.forEach((p, i) => {
    const x = 0.5 + (i % 2) * 4.75; const y = 1.55 + Math.floor(i / 2) * 1.82;
    card(s, x, y, 4.35, 1.62, p.color);
    s.addText(p.icon + "  " + p.title, { x: x + 0.18, y: y + 0.18, w: 3.95, h: 0.40, fontSize: 14, bold: true, color: p.color, fontFace: "Calibri" });
    s.addText(p.body, { x: x + 0.18, y: y + 0.60, w: 3.95, h: 0.88, fontSize: 11.5, color: MUTED, fontFace: "Calibri", valign: "top" });
  });
  s.addText("Motivation: I lost hours to fake studying — sitting at my desk but mentally checked out. No tool noticed.", {
    x: 0.5, y: 5.17, w: 9, h: 0.30, fontSize: 10.5, color: "4B5563", italic: true, fontFace: "Calibri", align: "center"
  });
})();

// ── SLIDE 3: Solution Overview ───────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("The Solution", { x: 0.5, y: 0.28, w: 9, h: 0.55, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("A closed-loop system that continuously senses, scores, and responds to your cognitive state.", {
    x: 0.5, y: 0.86, w: 9, h: 0.42, fontSize: 13, color: MUTED, fontFace: "Calibri"
  });
  const steps = [
    { num: "01", label: "SENSE",  desc: "Camera + mic sampled at 30 fps. MediaPipe extracts gaze direction, blink EAR, shoulder alignment, and hand presence. sounddevice measures ambient dB.", color: CYAN },
    { num: "02", label: "SCORE",  desc: "Per-second weighted focus score: gaze on screen × productive app active = 100%. Gaze on screen but unknown app = 60%. Gaze away = 0%.", color: PURPLE },
    { num: "03", label: "ADAPT",  desc: "Rule engine fires every 3 seconds. Triggers early breaks, flow extensions, posture nudges, and phone alerts based on real-time thresholds.", color: GREEN },
    { num: "04", label: "COACH",  desc: "Gemini 2.5 Flash generates 2-bullet personalized coaching messages in async daemon threads. Fires as camera overlay + macOS notification.", color: ORANGE },
  ];
  steps.forEach((step, i) => {
    const x = 0.5 + i * 2.32;
    card(s, x, 1.50, 2.18, 3.72, step.color);
    s.addText(step.num, { x: x + 0.15, y: 1.65, w: 1.90, h: 0.48, fontSize: 26, bold: true, color: step.color, fontFace: "Arial Black", margin: 0 });
    s.addText(step.label, { x: x + 0.15, y: 2.10, w: 1.90, h: 0.32, fontSize: 12, bold: true, color: WHITE, fontFace: "Arial Black", charSpacing: 3, margin: 0 });
    s.addText(step.desc,  { x: x + 0.15, y: 2.46, w: 1.92, h: 2.58, fontSize: 10.5, color: MUTED, fontFace: "Calibri", valign: "top" });
    if (i < 3) s.addText("→", { x: x + 2.16, y: 3.18, w: 0.20, h: 0.28, fontSize: 13, color: "2D2D5A", bold: true, align: "center" });
  });
})();

// ── SLIDE 4: Architecture ────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Technical Architecture", { x: 0.5, y: 0.28, w: 9, h: 0.55, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });

  s.addText("INPUTS", { x: 0.5, y: 1.02, w: 2.8, h: 0.32, fontSize: 10, color: CYAN, bold: true, charSpacing: 3, fontFace: "Arial Black" });
  [
    { label: "MediaPipe FaceMesh", sub: "478 landmarks → iris x, blink EAR ratio", color: CYAN },
    { label: "MediaPipe Pose",     sub: "Shoulder Y vs calibrated baseline", color: CYAN },
    { label: "MediaPipe Hands",    sub: "3s sustained = phone detected", color: CYAN },
    { label: "sounddevice mic",    sub: "RMS→dB, background thread", color: GREEN },
    { label: "AppKit NSWorkspace", sub: "Active app polled every 2s", color: ORANGE },
  ].forEach((inp, i) => {
    card(s, 0.5, 1.40 + i * 0.72, 2.85, 0.62, inp.color);
    s.addText(inp.label, { x: 0.64, y: 1.47 + i * 0.72, w: 2.55, h: 0.27, fontSize: 10.5, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(inp.sub,   { x: 0.64, y: 1.73 + i * 0.72, w: 2.55, h: 0.22, fontSize: 9,    color: MUTED, fontFace: "Calibri", margin: 0 });
  });

  s.addText("CORE ENGINE", { x: 3.62, y: 1.02, w: 3.0, h: 0.32, fontSize: 10, color: PURPLE, bold: true, charSpacing: 3, fontFace: "Arial Black" });
  [
    { label: "session_manager.py",  desc: "Focus score, intervention rules, timer_history log", color: PURPLE },
    { label: "tracker.py",          desc: "30fps CV main loop, calibration, HUD rendering", color: PURPLE },
    { label: "llm_coach.py",        desc: "Gemini 2.5 Flash via google-genai, async threads", color: PURPLE },
    { label: "noise_detector.py",   desc: "sounddevice InputStream, mutex-protected cache", color: GREEN },
  ].forEach((e, i) => {
    card(s, 3.62, 1.40 + i * 0.96, 3.0, 0.84, e.color);
    s.addText(e.label, { x: 3.76, y: 1.47 + i * 0.96, w: 2.70, h: 0.27, fontSize: 10.5, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(e.desc,  { x: 3.76, y: 1.74 + i * 0.96, w: 2.70, h: 0.38, fontSize: 9,    color: MUTED, fontFace: "Calibri", margin: 0 });
  });

  s.addText("OUTPUTS", { x: 6.88, y: 1.02, w: 2.8, h: 0.32, fontSize: 10, color: GREEN, bold: true, charSpacing: 3, fontFace: "Arial Black" });
  [
    { label: "Camera HUD",         sub: "Live focus%, posture, timer, coaching", color: GREEN },
    { label: "macOS Notifications",sub: "Non-intrusive alerts for every event", color: GREEN },
    { label: "Floating Overlay",   sub: "Always-on-top tkinter coaching window", color: ORANGE },
    { label: "Web Dashboard",      sub: "Flask + Chart.js at localhost:5050", color: ORANGE },
    { label: "session_*.json",     sub: "Timestamped logs + timer_history", color: CYAN },
  ].forEach((o, i) => {
    card(s, 6.88, 1.40 + i * 0.72, 2.75, 0.62, o.color);
    s.addText(o.label, { x: 7.02, y: 1.47 + i * 0.72, w: 2.45, h: 0.27, fontSize: 10.5, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(o.sub,   { x: 7.02, y: 1.73 + i * 0.72, w: 2.45, h: 0.22, fontSize: 9,    color: MUTED, fontFace: "Calibri", margin: 0 });
  });
})();

// ── SLIDE 5: Adaptive Timer Decision Logic (HOW IT WORKS) ───────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Adaptive Timer: Decision Engine", { x: 0.5, y: 0.25, w: 9, h: 0.55, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Three rules evaluate your state every 3 seconds during work blocks. All changes are logged with reason + focus score.", {
    x: 0.5, y: 0.83, w: 9, h: 0.38, fontSize: 12.5, color: MUTED, fontFace: "Calibri"
  });

  const rules = [
    {
      icon: "⚡", label: "EARLY BREAK", color: RED,
      trigger: "focus < 35%  AND  elapsed > 50% of block",
      result:  "Immediate break triggered. LLM coaching message explaining why.",
      example: '"Early break at 14m (focus=28%, was 25m block)"',
    },
    {
      icon: "🔥", label: "FLOW EXTENSION", color: GREEN,
      trigger: "focus ≥ 80%  AND  time remaining ≤ 30s",
      result:  "+5 minutes added to work block. Can stack multiple times.",
      example: '"Flow extension 25m→30m (focus=83%)"',
    },
    {
      icon: "🧍", label: "POSTURE NUDGE", color: ORANGE,
      trigger: "slouching > 70% of last 30s  (2-min cooldown)",
      result:  "LLM coaching message. Calibrated to your personal baseline.",
      example: '"Posture nudge — 72% slouch rate last 30 sec"',
    },
    {
      icon: "📱", label: "PHONE DETECTED", color: PURPLE,
      trigger: "hand visible ≥ 3 continuous seconds during work",
      result:  "LLM coaching message. 5-second hold to avoid false positives.",
      example: '"Hand detected 4s, gaze away — phone likely in use"',
    },
  ];

  rules.forEach((r, i) => {
    const x = 0.5 + (i % 2) * 4.75;
    const y = 1.38 + Math.floor(i / 2) * 1.88;
    card(s, x, y, 4.35, 1.72, r.color);
    s.addText(r.icon + "  " + r.label, { x: x + 0.18, y: y + 0.12, w: 3.95, h: 0.35, fontSize: 13, bold: true, color: r.color, fontFace: "Arial Black", margin: 0 });
    s.addText("Trigger: " + r.trigger, { x: x + 0.18, y: y + 0.50, w: 3.95, h: 0.28, fontSize: 10.5, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText("Result: "  + r.result,  { x: x + 0.18, y: y + 0.80, w: 3.95, h: 0.35, fontSize: 10.5, color: MUTED, fontFace: "Calibri", margin: 0 });
    s.addText(r.example,               { x: x + 0.18, y: y + 1.22, w: 3.95, h: 0.30, fontSize: 9.5, color: r.color, fontFace: "Calibri", italic: true, margin: 0 });
  });

  s.addText("Manual: Press [E] at any time during a work block or transition to add +5 min and stay in flow.", {
    x: 0.5, y: 5.20, w: 9, h: 0.28, fontSize: 10.5, color: CYAN, fontFace: "Calibri", align: "center"
  });
})();

// ── SLIDE 6: AI Coaching ─────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Gemini-Powered Personal Coach", { x: 0.5, y: 0.25, w: 9, h: 0.55, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Every rule trigger fires an async Gemini 2.5 Flash call with your exact sensor context. Responses arrive in < 2 seconds.", {
    x: 0.5, y: 0.83, w: 9, h: 0.38, fontSize: 12.5, color: MUTED, fontFace: "Calibri"
  });
  const triggers = [
    { event: "POSTURE_NUDGE",  context: "focus=65%, slouch=72% of last 30s, blink=8/min", msg: "• You've been hunching — sit tall and reset your shoulders.\n• Low blink rate suggests eye strain; look away for 20 seconds.", color: ORANGE },
    { event: "EARLY_BREAK",   context: "focus=28%, elapsed=14min, noise=61dB",             msg: "• Focus dropped sharply — your brain needs a real reset now.\n• Step away from the screen; even 5 minutes will help.", color: RED },
    { event: "PHONE_DETECTED",context: "hand visible 4s, gaze away, during work block",    msg: "• Phone spotted — put it face-down and refocus.\n• You were building momentum; don't lose it now.", color: PURPLE },
    { event: "SESSION_END",   context: "focus=72%, 25min session, top_app=Claude",          msg: "• Great session — 72% focus is above your personal average.\n• Your peak hour is 5 PM; protect that time tomorrow.", color: GREEN },
  ];
  triggers.forEach((t, i) => {
    const x = (i % 2) * 4.82 + 0.5; const y = 1.40 + Math.floor(i / 2) * 1.95;
    card(s, x, y, 4.55, 1.82, t.color);
    badge(s, t.event, x + 0.15, y + 0.10, t.color);
    s.addText("Context: " + t.context, { x: x + 0.15, y: y + 0.46, w: 4.28, h: 0.26, fontSize: 9, color: MUTED, fontFace: "Calibri", italic: true });
    s.addText(t.msg, { x: x + 0.15, y: y + 0.76, w: 4.28, h: 0.90, fontSize: 10.5, color: TEXT, fontFace: "Calibri" });
  });
  s.addText("All calls run in daemon threads — zero blocking of the 30fps OpenCV video loop", {
    x: 0.5, y: 5.24, w: 9, h: 0.25, fontSize: 10, color: "4B5563", italic: true, align: "center", fontFace: "Calibri"
  });
})();

// ── SLIDE 7: Web Dashboard ───────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Web Analytics Dashboard", { x: 0.5, y: 0.25, w: 9, h: 0.55, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Flask + Chart.js at localhost:5050. Run in any browser. Auto-refreshes every 60 seconds.", {
    x: 0.5, y: 0.83, w: 9, h: 0.38, fontSize: 12.5, color: MUTED, fontFace: "Calibri"
  });
  [
    { icon: "📈", title: "Focus Trend Line",       desc: "Per-session focus % over time. See if you're getting better.", color: PURPLE },
    { icon: "🕐", title: "Hourly Productivity",    desc: "Avg focus by time of day — reveals your personal peak hours.", color: CYAN },
    { icon: "🍩", title: "App Usage Breakdown",    desc: "Which apps dominate your sessions. Productive vs. distracting.", color: GREEN },
    { icon: "📊", title: "Session Comparison",     desc: "Focus% vs posture% per session. Spot patterns across days.", color: ORANGE },
    { icon: "⚡", title: "Adaptive Timer Log",     desc: "Every timer change timestamped with reason + focus score — proof of adaptation.", color: RED },
    { icon: "✦",  title: "AI Personalized Advice", desc: "On-demand Gemini coaching based on all historical data. 4 data-driven bullets.", color: PURPLE },
  ].forEach((f, i) => {
    const x = 0.5 + (i % 3) * 3.17; const y = 1.42 + Math.floor(i / 3) * 1.88;
    card(s, x, y, 3.02, 1.72, f.color);
    s.addText(f.icon + "  " + f.title, { x: x + 0.15, y: y + 0.14, w: 2.72, h: 0.40, fontSize: 12.5, bold: true, color: f.color, fontFace: "Calibri" });
    s.addText(f.desc,                  { x: x + 0.15, y: y + 0.58, w: 2.72, h: 1.00, fontSize: 10.5, color: MUTED, fontFace: "Calibri", valign: "top" });
  });
})();

// ── SLIDE 8: Evaluation & Evidence ──────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Evaluation & Evidence", { x: 0.5, y: 0.25, w: 9, h: 0.55, fontSize: 30, bold: true, color: WHITE, fontFace: "Arial Black" });

  [
    { value: "48%",   label: "Peak focus",         sub: "vs 0% in session 1",      color: GREEN },
    { value: "97%",   label: "Best posture rate",  sub: "up from 19% baseline",    color: CYAN },
    { value: "< 5%",  label: "Phone false-pos.",   sub: "3s hold vs 40% with old", color: ORANGE },
    { value: "25→30", label: "Flow extension (m)", sub: "adaptive timer proof",    color: PURPLE },
  ].forEach((st, i) => {
    const x = 0.5 + i * 2.32;
    card(s, x, 1.02, 2.18, 1.72, st.color);
    s.addText(st.value, { x: x + 0.1, y: 1.10, w: 1.98, h: 0.65, fontSize: 28, bold: true, color: st.color, fontFace: "Arial Black", align: "center" });
    s.addText(st.label, { x: x + 0.1, y: 1.84, w: 1.98, h: 0.30, fontSize: 9.5, bold: true, color: TEXT, fontFace: "Calibri", align: "center" });
    s.addText(st.sub,   { x: x + 0.1, y: 2.20, w: 1.98, h: 0.28, fontSize: 9,   color: MUTED, fontFace: "Calibri", align: "center" });
  });

  s.addText("How We Validated", { x: 0.5, y: 2.92, w: 9, h: 0.40, fontSize: 15, bold: true, color: WHITE, fontFace: "Arial Black" });
  [
    { icon: "🔬", title: "Session-over-session trends",   desc: "Dashboard shows focus improving as the tool calibrates to the user over multiple sessions." },
    { icon: "⚡", title: "Timer adaptation log",          desc: "Every early break and flow extension is timestamped with the triggering focus score — auditable proof." },
    { icon: "📋", title: "Failure analysis + iteration",  desc: "Phone detection: false-positive rate cut from ~40% (instant gaze heuristic) to <5% (3s accumulator)." },
    { icon: "🎯", title: "Calibrated posture baseline",   desc: "Per-session calibration eliminates false slouch positives from the fixed threshold approach." },
  ].forEach((e, i) => {
    const x = 0.5 + (i % 2) * 4.78; const y = 3.40 + Math.floor(i / 2) * 0.88;
    s.addText(e.icon + "  " + e.title, { x, y,        w: 4.38, h: 0.30, fontSize: 11.5, bold: true, color: CYAN, fontFace: "Calibri" });
    s.addText(e.desc,                  { x: x + 0.25, y: y + 0.30, w: 4.20, h: 0.48, fontSize: 10,   color: MUTED, fontFace: "Calibri" });
  });
})();

// ── SLIDE 9: Use Cases & Impact ──────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Use Cases & Impact", { x: 0.5, y: 0.25, w: 9, h: 0.55, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("Who benefits, and how could this scale?", {
    x: 0.5, y: 0.83, w: 9, h: 0.38, fontSize: 13, color: MUTED, fontFace: "Calibri"
  });

  const cases = [
    { icon: "🎓", title: "Students",         desc: "Replace passive studying with sessions that actually adapt. Know exactly when you're wasting time sitting at your desk.", color: CYAN },
    { icon: "💻", title: "Remote Workers",   desc: "Detect when home office noise or phone interruptions are hurting your productivity. Get data-backed evidence.", color: PURPLE },
    { icon: "🏥", title: "Mental Health",    desc: "Long-term blink rate and posture trends may surface early fatigue or burnout indicators before they become serious.", color: GREEN },
    { icon: "🔬", title: "Research",         desc: "A non-invasive sensor platform for studying cognitive load, attention, and environmental effects on focus.", color: ORANGE },
  ];
  cases.forEach((c, i) => {
    const x = 0.5 + (i % 2) * 4.75; const y = 1.38 + Math.floor(i / 2) * 1.95;
    card(s, x, y, 4.35, 1.78, c.color);
    s.addText(c.icon + "  " + c.title, { x: x + 0.18, y: y + 0.16, w: 3.95, h: 0.40, fontSize: 14, bold: true, color: c.color, fontFace: "Calibri" });
    s.addText(c.desc,                  { x: x + 0.18, y: y + 0.58, w: 3.95, h: 1.00, fontSize: 11.5, color: MUTED, fontFace: "Calibri", valign: "top" });
  });

  s.addText("Vision: a lightweight background agent that runs all day and builds a true map of your cognitive patterns over weeks.", {
    x: 0.5, y: 5.18, w: 9, h: 0.30, fontSize: 10.5, color: PURPLE, italic: true, fontFace: "Calibri", align: "center"
  });
})();

// ── SLIDE 10: Future Work ────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Future Work", { x: 0.5, y: 0.25, w: 9, h: 0.55, fontSize: 32, bold: true, color: WHITE, fontFace: "Arial Black" });
  s.addText("The foundation is built. Here is what comes next.", {
    x: 0.5, y: 0.83, w: 9, h: 0.38, fontSize: 13, color: MUTED, fontFace: "Calibri"
  });
  [
    { num: "01", title: "RL-Based Adaptive Policy",       desc: "Replace rule-based logic with Q-learning. State: (focus, blink, noise, hour). Reward: sustained focus improvement across intervals.", color: PURPLE },
    { num: "02", title: "Ambient Noise Classification",   desc: "Distinguish speech vs. music vs. background hum with a lightweight audio CNN — smarter than raw dB alone.", color: CYAN },
    { num: "03", title: "Baseline A/B Comparison",        desc: "Fixed 25/5 mode vs. adaptive mode, same user, same conditions. Dashboard shows which produces higher focus statistically.", color: GREEN },
    { num: "04", title: "Pre-Session Goal + Post-Review", desc: "\"What do you want to finish?\" stored at start. LLM checks completion at end. Builds accountability loop.", color: ORANGE },
    { num: "05", title: "Streak & Gamification Layer",    desc: "Focus streaks, personal records, weekly digests. Behavioral nudges to make consistent studying a habit.", color: RED },
  ].forEach((f, i) => {
    const y = 1.35 + i * 0.76;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 0.5, h: 0.58, fill: { color: f.color, transparency: 20 }, line: { color: f.color, width: 0 } });
    s.addText(f.num,   { x: 0.5, y: y + 0.02, w: 0.5, h: 0.55, fontSize: 12, bold: true, color: f.color, fontFace: "Arial Black", align: "center", valign: "middle" });
    s.addText(f.title, { x: 1.15, y: y + 0.02, w: 8.35, h: 0.27, fontSize: 12.5, bold: true, color: TEXT, fontFace: "Calibri", margin: 0 });
    s.addText(f.desc,  { x: 1.15, y: y + 0.30, w: 8.35, h: 0.36, fontSize: 10,   color: MUTED, fontFace: "Calibri", margin: 0 });
  });
})();

// ── SLIDE 11: Closing ────────────────────────────────────────────────────────
(function() {
  const s = pres.addSlide();
  s.background = { color: BG };

  // Simple clean dark layout — no decorative circles
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 2.45, w: 10, h: 0.03, fill: { color: PURPLE }, line: { color: PURPLE, width: 0 } });

  s.addText("One Person.", { x: 0.5, y: 0.55, w: 9, h: 0.88, fontSize: 54, bold: true, color: WHITE, fontFace: "Arial Black", align: "center" });
  s.addText("Full-Stack AI Productivity Research.", { x: 0.5, y: 1.38, w: 9, h: 0.78, fontSize: 30, bold: true, color: PURPLE, fontFace: "Arial Black", align: "center" });

  s.addText("5 sensors  ·  real-time adaptive timer  ·  Gemini AI coach  ·  long-term analytics dashboard", {
    x: 0.5, y: 2.65, w: 9, h: 0.42, fontSize: 13.5, color: MUTED, fontFace: "Calibri", align: "center"
  });

  // Tech stack row — evenly spaced text, no badge shapes that might overflow
  const techs = "MediaPipe  ·  OpenCV  ·  Flask + Chart.js  ·  Gemini 2.5 Flash  ·  sounddevice  ·  AppKit";
  s.addText(techs, { x: 0.5, y: 3.25, w: 9, h: 0.38, fontSize: 11, color: "4B5563", fontFace: "Calibri", align: "center" });

  s.addText("github.com/safaahussain1/adaptive-pomodoro-buddy", {
    x: 0.5, y: 3.82, w: 9, h: 0.38, fontSize: 13, color: PURPLE, fontFace: "Calibri", align: "center"
  });

  s.addText("Safaa Hussain  ·  CS 153  ·  Spring 2026", {
    x: 0.5, y: 4.55, w: 9, h: 0.35, fontSize: 11, color: "4B5563", fontFace: "Calibri", align: "center"
  });
})();

// ── Write ────────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "CS153_Pomodoro_Buddy_Slides.pptx" })
  .then(() => console.log("✓  Written: CS153_Pomodoro_Buddy_Slides.pptx  (11 slides)"))
  .catch(e => { console.error(e); process.exit(1); });
