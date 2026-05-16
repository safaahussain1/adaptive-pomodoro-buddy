import time
import json
import os

class PomodoroSessionManager:
    def __init__(self, work_duration_mins=25, break_duration_mins=5):
        # Configuration
        self.work_duration_seconds = work_duration_mins * 60
        self.break_duration_seconds = break_duration_mins * 60
        
        # State tracking vars
        self.is_working = True  # True = Work block, False = Break block
        self.session_start_time = time.time()
        self.block_start_time = time.time()
        
        # Time-series analytics memory
        # This stores tuples or dicts: (timestamp, gaze_score, posture_score)
        self.history_logs = []
        
    def log_frame_state(self, gaze_status, posture_status):
        """Appends current frame insights to our time-series tracking matrix."""
        timestamp = time.time()
        
        # Convert text statuses into clean binary/numeric metrics for analysis
        gaze_numeric = 1 if gaze_status == "Focused on Screen" else 0
        posture_numeric = 1 if posture_status == "Good Posture" else 0
        
        data_point = {
            "timestamp": timestamp,
            "elapsed_seconds": int(timestamp - self.block_start_time),
            "is_working_block": self.is_working,
            "gaze_score": gaze_numeric,
            "posture_score": posture_numeric
        }
        
        self.history_logs.append(data_point)
        
    def get_remaining_time(self):
        """Calculates seconds left in current work or break block."""
        elapsed = time.time() - self.block_start_time
        limit = self.work_duration_seconds if self.is_working else self.break_duration_seconds
        remaining = max(0, limit - elapsed)
        return int(remaining)

    def compute_focus_score(self, window_seconds=60):
        """
        Looks back at the last X seconds of data points to evaluate 
        the user's real-time productivity density.
        """
        if not self.history_logs:
            return 100.0
            
        now = time.time()
        recent_points = [p for p in self.history_logs if now - p["timestamp"] <= window_seconds]
        
        if not recent_points:
            return 100.0
            
        # Calculate percentage of frames where the user was looking at the screen
        focused_frames = sum(1 for p in recent_points if p["gaze_score"] == 1)
        focus_percentage = (focused_frames / len(recent_points)) * 100
        return round(focus_percentage, 1)

    def save_session_data(self, filename="session_history.json"):
        """Dumps collected metrics out to disk for future training or LLM parsing."""
        with open(filename, "w") as f:
            json.dump(self.history_logs, f, indent=4)
        print(f"\n[Session Saved] Metric log written to {filename}")

    def evaluate_interventions(self):
        """
        Evaluates recent time-series data points to determine if an adaptive 
        intervention (extend, break early, or posture nudge) is required.
        """
        now = time.time()
        # Look back at the last 30 seconds for quick triggers
        recent_points = [p for p in self.history_logs if now - p["timestamp"] <= 30]
        
        if len(recent_points) < 10:  # Not enough data points gathered yet
            return None

        # 1. Posture Check
        slouching_frames = sum(1 for p in recent_points if p["posture_score"] == 0)
        slouch_ratio = slouching_frames / len(recent_points)
        if slouch_ratio > 0.70:  # Slouching for more than 70% of the last 30 seconds
            return "POSTURE_NUDGE"

        # 2. Adaptive Pomodoro Adjustments (Only evaluated during work blocks)
        if self.is_working:
            time_left = self.get_remaining_time()
            rolling_focus = self.compute_focus_score(window_seconds=60)

            # Scenario A: Cognitive Fatigue / Deep Distraction -> Early Break
            # If you are more than halfway through your session but your focus drops below 30%
            elapsed = time.time() - self.block_start_time
            if elapsed > (self.work_duration_seconds / 2) and rolling_focus < 30.0:
                # Dynamically shorten the block by cutting the remaining time to 0
                self.is_working = False
                self.block_start_time = time.time() # Reset block anchor
                return "EARLY_BREAK"

            # Scenario B: Deep Flow State -> Extend Session
            # If the timer is about to run out (less than 10s left) and focus is pristine (>85%)
            if time_left <= 10 and rolling_focus >= 85.0:
                extension_mins = 5
                self.work_duration_seconds += (extension_mins * 60)
                return "FLOW_EXTENSION"

        return None
