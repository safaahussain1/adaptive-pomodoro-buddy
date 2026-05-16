import time
import json
import os
import subprocess

class PomodoroSessionManager:
    def __init__(self, work_duration_mins=25, break_duration_mins=5):
        self.work_duration_seconds = work_duration_mins * 60
        self.break_duration_seconds = break_duration_mins * 60
        self.is_working = True  
        self.session_start_time = time.time()
        self.block_start_time = time.time()
        self.history_logs = []
        
    def get_active_window_macos(self):
        """Uses native AppKit memory inspection to instantly identify the front app."""
        try:
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return active_app.localizedName()
        except Exception:
            return "Unknown"

    def log_frame_state(self, gaze_status, posture_status, blink_count):
        """Appends comprehensive vision and OS context to our analytics matrix."""
        timestamp = time.time()
        active_app = self.get_active_window_macos()
        
        gaze_numeric = 1 if gaze_status == "Focused on Screen" else 0
        posture_numeric = 1 if posture_status == "Good Posture" else 0
        
        # Categorize the current window application type
        # Add any productivity apps you use (like Slack, Cursor, etc.) to this list
        productive_apps = ["Code", "Visual Studio Code", "Terminal", "iTerm2", "Xcode", "Safari", "Google Chrome"]
        # Add "Electron" variants to ensure VS Code is registered as productive
        productive_apps = [
            "Code", "Visual Studio Code", "Electron", "Electron Framework", 
            "Terminal", "iTerm2", "Xcode", "Safari", "Google Chrome"
        ]
        window_is_productive = 1 if active_app in productive_apps else 0

        data_point = {
            "timestamp": timestamp,
            "elapsed_seconds": int(timestamp - self.block_start_time),
            "is_working_block": self.is_working,
            "gaze_score": gaze_numeric,
            "posture_score": posture_numeric,
            "blinks_in_last_sec": blink_count,
            "active_app": active_app,
            "window_is_productive": window_is_productive
        }
        
        self.history_logs.append(data_point)
        
    def get_remaining_time(self):
        elapsed = time.time() - self.block_start_time
        limit = self.work_duration_seconds if self.is_working else self.break_duration_seconds
        remaining = max(0, limit - elapsed)
        return int(remaining)

    def compute_focus_score(self, window_seconds=60):
        if not self.history_logs:
            return 100.0
        now = time.time()
        recent_points = [p for p in self.history_logs if now - p["timestamp"] <= window_seconds]
        if not recent_points:
            return 100.0
            
        # COMPOSITE SCORE: Combined gaze focus AND app alignment!
        # Even if looking at screen, score drops if browsing an unproductive app
        focused_frames = sum(1 for p in recent_points if p["gaze_score"] == 1 and p["window_is_productive"] == 1)
        focus_percentage = (focused_frames / len(recent_points)) * 100
        return round(focus_percentage, 1)

    def evaluate_interventions(self):
        now = time.time()
        recent_points = [p for p in self.history_logs if now - p["timestamp"] <= 30]
        
        if len(recent_points) < 10:
            return None

        # 1. Posture Check
        slouching_frames = sum(1 for p in recent_points if p["posture_score"] == 0)
        if (slouching_frames / len(recent_points)) > 0.70:
            return "POSTURE_NUDGE"

        if self.is_working:
            time_left = self.get_remaining_time()
            rolling_focus = self.compute_focus_score(window_seconds=60)

            # 2. Distraction/Fatigue Trigger -> Early Break
            elapsed = time.time() - self.block_start_time
            if elapsed > (self.work_duration_seconds / 2) and rolling_focus < 35.0:
                self.is_working = False
                self.block_start_time = time.time()
                return "EARLY_BREAK"

            # 3. Flow Extension Trigger
            if time_left <= 10 and rolling_focus >= 85.0:
                self.work_duration_seconds += 300
                return "FLOW_EXTENSION"

        return None

    def save_session_data(self, filename="session_history.json"):
        with open(filename, "w") as f:
            json.dump(self.history_logs, f, indent=4)
        print(f"\n[Session Saved] Metric log written to {filename}")