import time
import json

# Apps that count as productive work. "Python" is our own process — always excluded.
PRODUCTIVE_APPS = {
    "Code", "Visual Studio Code", "Electron", "Electron Framework",
    "Terminal", "iTerm2", "Xcode", "Safari", "Google Chrome", "Firefox",
    "Arc", "Cursor", "PyCharm", "IntelliJ IDEA", "WebStorm", "Slack",
    "Notion", "Obsidian", "Notes", "TextEdit", "Sublime Text",
}

# Never treat these as the "active" app — they are our own window or system UI.
OWN_PROCESS_NAMES = {"Python", "python", "python3", "Adaptive Pomodoro Buddy"}


class PomodoroSessionManager:
    def __init__(self, work_duration_mins=25, break_duration_mins=5):
        self.work_duration_seconds = work_duration_mins * 60
        self.break_duration_seconds = break_duration_mins * 60
        self.base_work_duration_seconds = work_duration_mins * 60  # for display
        self.is_working = True
        self.session_start_time = time.time()
        self.block_start_time = time.time()
        self.history_logs = []
        self._last_real_app = "Unknown"          # last app that wasn't our own window

        # Posture calibration — set by tracker after startup calibration
        self.posture_baseline_y = None           # good-posture shoulder_y reference
        self.SLOUCH_DELTA = 0.06                 # how much below baseline triggers slouching

        # Per-intervention cooldowns (seconds)
        self._last_posture_nudge_time = 0.0
        self._last_focus_intervention_time = 0.0
        self.POSTURE_NUDGE_COOLDOWN = 120        # 2 minutes between posture nudges
        self.FOCUS_INTERVENTION_COOLDOWN = 60    # 1 minute between focus interventions

        # Adaptive timer history — proof that durations change based on focus
        self.timer_history = []   # (timestamp, description_str)

    # ------------------------------------------------------------------
    def get_active_window_macos(self):
        try:
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            name = active_app.localizedName()
            if name not in OWN_PROCESS_NAMES:
                self._last_real_app = name
            return self._last_real_app
        except Exception:
            return self._last_real_app

    # ------------------------------------------------------------------
    def log_frame_state(self, gaze_status, posture_status, blink_count,
                        noise_db=40.0, shoulder_y=None, active_app=None):
        timestamp = time.time()
        # Use the pre-fetched app name (fetched in background thread in tracker.py)
        # to avoid calling AppKit on the same thread as OpenCV's Cocoa window.
        if active_app is None:
            active_app = self._last_real_app

        gaze_numeric = 1 if gaze_status == "Focused on Screen" else 0
        posture_numeric = 1 if posture_status == "Good Posture" else 0
        window_is_productive = 1 if active_app in PRODUCTIVE_APPS else 0

        self.history_logs.append({
            "timestamp": timestamp,
            "elapsed_seconds": int(timestamp - self.block_start_time),
            "is_working_block": self.is_working,
            "gaze_score": gaze_numeric,
            "posture_score": posture_numeric,
            "blinks_in_last_sec": blink_count,
            "active_app": active_app,
            "window_is_productive": window_is_productive,
            "noise_db": noise_db,
            "shoulder_y": shoulder_y,
        })

    # ------------------------------------------------------------------
    def get_remaining_time(self):
        elapsed = time.time() - self.block_start_time
        limit = self.work_duration_seconds if self.is_working else self.break_duration_seconds
        return int(max(0, limit - elapsed))

    def get_elapsed_in_block(self):
        return time.time() - self.block_start_time

    # ------------------------------------------------------------------
    def compute_focus_score(self, window_seconds=60):
        if not self.history_logs:
            return 100.0
        now = time.time()
        recent = [p for p in self.history_logs if now - p["timestamp"] <= window_seconds]
        if not recent:
            return 100.0
        focused = sum(1 for p in recent if p["gaze_score"] == 1 and p["window_is_productive"] == 1)
        return round(focused / len(recent) * 100, 1)

    # ------------------------------------------------------------------
    def evaluate_interventions(self):
        now = time.time()
        recent = [p for p in self.history_logs if now - p["timestamp"] <= 30]

        if len(recent) < 10:
            return None

        # 1. Posture check (uses calibrated baseline if available)
        slouching_frames = sum(1 for p in recent if p["posture_score"] == 0)
        if slouching_frames / len(recent) > 0.70:
            if now - self._last_posture_nudge_time >= self.POSTURE_NUDGE_COOLDOWN:
                self._last_posture_nudge_time = now
                return "POSTURE_NUDGE"

        if not self.is_working:
            return None

        if now - self._last_focus_intervention_time < self.FOCUS_INTERVENTION_COOLDOWN:
            return None

        rolling_focus = self.compute_focus_score(window_seconds=60)
        elapsed = self.get_elapsed_in_block()
        time_left = self.get_remaining_time()

        # 2. Early break — focus < 35% after halfway through block
        if elapsed > self.work_duration_seconds / 2 and rolling_focus < 35.0:
            self._last_focus_intervention_time = now
            old_elapsed = int(elapsed // 60)
            self.is_working = False
            self.block_start_time = now
            entry = (f"Early break at {old_elapsed}m "
                     f"(focus={rolling_focus:.0f}%, was {self.work_duration_seconds // 60}m block)")
            self.timer_history.append((now, entry))
            return "EARLY_BREAK"

        # 3. Flow extension — high focus when timer is almost done
        if time_left <= 30 and rolling_focus >= 80.0:
            self._last_focus_intervention_time = now
            old_dur = self.work_duration_seconds // 60
            self.work_duration_seconds += 300
            new_dur = self.work_duration_seconds // 60
            entry = f"Flow extension {old_dur}m→{new_dur}m (focus={rolling_focus:.0f}%)"
            self.timer_history.append((now, entry))
            return "FLOW_EXTENSION"

        return None
