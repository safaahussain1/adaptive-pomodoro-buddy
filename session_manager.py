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
