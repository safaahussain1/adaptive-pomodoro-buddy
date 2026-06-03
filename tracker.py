import os
import sys

os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

# Permanently redirect C-level stderr (fd 2) to /dev/null for the whole
# process lifetime. mediapipe initializes lazily inside FaceMesh()/Pose()
# so there is no safe point to restore — keeping it suppressed is correct.
# Our print() calls use stdout (fd 1) and are unaffected.
os.dup2(os.open(os.devnull, os.O_WRONLY), 2)

import cv2
import mediapipe as mp
import time
import math
import threading
import subprocess
import sys
from dotenv import load_dotenv
load_dotenv()

from session_manager import PomodoroSessionManager, OWN_PROCESS_NAMES
from noise_detector import AmbientNoiseDetector
from analytics import print_session_report, save_session_report
from llm_coach import get_coaching_message

mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

LEFT_EYE_TOP_BOTTOM = [374, 386]
LEFT_EYE_LEFT_RIGHT = [362, 263]

# ── Calibration ────────────────────────────────────────────────────────────────
CALIBRATION_SECONDS = 5   # sit up straight for this long at startup


def calculate_ear(landmarks, top_bottom_idx, left_right_idx):
    p_top = landmarks[top_bottom_idx[1]]
    p_bottom = landmarks[top_bottom_idx[0]]
    p_left = landmarks[left_right_idx[0]]
    p_right = landmarks[left_right_idx[1]]
    vert = math.sqrt((p_top.x - p_bottom.x) ** 2 + (p_top.y - p_bottom.y) ** 2)
    horiz = math.sqrt((p_left.x - p_right.x) ** 2 + (p_left.y - p_right.y) ** 2)
    return vert / horiz if horiz != 0 else 0.0


TRIGGER_TITLES = {
    "POSTURE_NUDGE":   "Posture Check",
    "EARLY_BREAK":     "Early Break Triggered",
    "FLOW_EXTENSION":  "Flow Extension +5 min",
    "SESSION_END":     "Session Complete",
    "PHONE_DETECTED":  "Put the Phone Down",
}

def notify_macos(title: str, message: str):
    """Send a native macOS notification (non-blocking)."""
    safe_msg = message.replace('"', "'").replace("\\", "")
    safe_title = title.replace('"', "'")
    script = f'display notification "{safe_msg}" with title "Pomodoro Buddy" subtitle "{safe_title}"'
    subprocess.Popen(["osascript", "-e", script],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def fetch_llm_message_async(trigger, context, result_container):
    msg = get_coaching_message(trigger, context)
    result_container["message"] = msg
    result_container["trigger"] = trigger
    result_container["timestamp"] = time.time()
    title = TRIGGER_TITLES.get(trigger, trigger)
    print(f"\n[Coach — {title}]\n  {msg}\n")
    notify_macos(title, msg)
    # Write for overlay window
    try:
        import json as _json
        with open(".overlay_msg", "w") as _f:
            _json.dump({"message": msg, "trigger": trigger, "title": title,
                        "ts": time.time()}, _f)
    except Exception:
        pass


def draw_hud(frame, session, recent_focus, posture_status, display_app,
             noise_label, cached_noise_db, llm_overlay, calibrating,
             calibration_deadline, phone_detected):
    h, w = frame.shape[:2]

    # Semi-transparent header bar
    header = frame.copy()
    cv2.rectangle(header, (0, 0), (w, 165), (0, 0, 0), -1)
    cv2.addWeighted(header, 0.55, frame, 0.45, 0, frame)

    time_left = session.get_remaining_time()
    mins, secs = divmod(time_left, 60)
    block_label = "WORK" if session.is_working else "BREAK"
    timer_color = (0, 255, 255) if session.is_working else (255, 180, 0)

    # Show +Xmin extension if base was changed
    extra = (session.work_duration_seconds - session.base_work_duration_seconds) // 60
    extension_str = f" (+{extra}m extended)" if extra > 0 else ""

    if calibrating:
        secs_left = max(0, int(calibration_deadline - time.time()))
        cv2.putText(frame, f"CALIBRATING — sit up straight ({secs_left}s)...",
                    (20, 42), cv2.FONT_HERSHEY_DUPLEX, 0.85, (0, 220, 255), 2)
    else:
        cv2.putText(frame, f"[{block_label}] {mins:02d}:{secs:02d}{extension_str}",
                    (20, 42), cv2.FONT_HERSHEY_DUPLEX, 1.0, timer_color, 2)

    focus_color = (0, 255, 0) if recent_focus >= 60 else (0, 165, 255) if recent_focus >= 30 else (0, 0, 255)
    cv2.putText(frame, f"Focus: {recent_focus:.0f}%",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, focus_color, 2)

    posture_color = (0, 255, 0) if posture_status == "Good Posture" else (0, 0, 255)
    cv2.putText(frame, f"App: {display_app}  |  Posture: {posture_status}",
                (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.60, posture_color, 2)

    noise_color = (200, 200, 200) if cached_noise_db < 55 else (0, 165, 255)
    phone_str = "  |  PHONE DETECTED" if phone_detected else ""
    cv2.putText(frame, f"Noise: {noise_label} ({cached_noise_db:.0f} dB){phone_str}",
                (20, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                (0, 0, 255) if phone_detected else noise_color, 1)

    # Recent timer events (bottom-right)
    now = time.time()
    visible_events = [e for ts, e in session.timer_events if now - ts < 30]
    for i, ev in enumerate(visible_events[-3:]):
        cv2.putText(frame, ev, (w - 350, h - 20 - i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 100), 1)

    # LLM coaching overlay at bottom
    msg_age = now - llm_overlay.get("timestamp", 0)
    if llm_overlay.get("message") and msg_age < 12.0:
        msg = llm_overlay["message"]
        words = msg.split()
        line1, line2 = [], []
        for word in words:
            if len(" ".join(line1 + [word])) < 70:
                line1.append(word)
            else:
                line2.append(word)
        cv2.rectangle(frame, (0, h - 90), (w, h), (20, 20, 20), -1)
        cv2.putText(frame, " ".join(line1), (15, h - 58),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        if line2:
            cv2.putText(frame, " ".join(line2), (15, h - 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def teardown(session, noise_detector, cap):
    noise_detector.stop()
    cv2.destroyAllWindows()   # must come before cap.release() on macOS
    cap.release()
    print_session_report(session.history_logs)
    if session.history_logs:
        saved_path = save_session_report(session.history_logs)
        print(f"[Session Saved] → {saved_path}")
        summary_context = {
            "focus_score": session.compute_focus_score(window_seconds=9999),
            "elapsed_mins": (session.history_logs[-1]["timestamp"] - session.session_start_time) / 60,
            "noise_level_db": sum(p.get("noise_db", 40) for p in session.history_logs) / len(session.history_logs),
            "top_app": max(
                set(p["active_app"] for p in session.history_logs),
                key=lambda a: sum(1 for p in session.history_logs if p["active_app"] == a),
            ),
            "blink_rate_per_min": sum(p["blinks_in_last_sec"] for p in session.history_logs) * 60 / len(session.history_logs),
        }
        print("\n[Coach] Generating end-of-session feedback...")
        msg = get_coaching_message("SESSION_END", summary_context)
        print(f"\n>> {msg}\n")
    # os._exit skips the C++ destructors that cause the macOS double-free crash
    os._exit(0)


def run_study_buddy(work_mins=25, break_mins=5):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        sys.exit(1)

    session = PomodoroSessionManager(work_duration_mins=work_mins, break_duration_mins=break_mins)
    noise_detector = AmbientNoiseDetector()
    noise_detector.start()

    last_log_time = time.time()
    last_intervention_time = time.time()

    blink_counter = 0
    is_blinking = False
    EAR_THRESHOLD = 0.21

    cached_noise_db = 40.0
    llm_overlay = {"message": "", "trigger": "", "timestamp": 0.0}

    # ── Posture calibration state ──────────────────────────────────────
    calibrating = True
    calibration_deadline = time.time() + CALIBRATION_SECONDS
    calibration_shoulder_readings = []

    # ── Phone detection via hand landmarks ─────────────────────────────
    phone_detected = False
    phone_detected_until = 0.0

    # ── AppKit polling in a background thread ──────────────────────────
    # Calling NSWorkspace on the same thread as OpenCV's Cocoa window
    # causes the window to freeze. We poll in a daemon thread instead.
    _app_cache = {"name": "Unknown"}
    def _poll_active_app():
        while True:
            try:
                from AppKit import NSWorkspace
                name = NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()
                if name not in OWN_PROCESS_NAMES:
                    _app_cache["name"] = name
                    session._last_real_app = name
            except Exception:
                pass
            time.sleep(2.0)
    threading.Thread(target=_poll_active_app, daemon=True).start()

    print("=" * 60)
    print("  Adaptive Pomodoro Buddy")
    print(f"  Work: {work_mins} min  |  Break: {break_mins} min")
    print("  Sit up straight — calibrating posture baseline for 5s...")
    print("  Press [Q] or [Esc] to quit.")
    print("=" * 60)

    # Create overlay file immediately so overlay.py shows "session active"
    import json as _json
    try:
        with open(".overlay_msg", "w") as _f:
            _json.dump({
                "message": "Session started — sit up straight for calibration!",
                "trigger": "START", "title": "Pomodoro Buddy",
                "ts": time.time(), "stats": f"WORK {work_mins:02d}:00  |  Focus —%  |  Calibrating"
            }, _f)
    except Exception:
        pass

    try:
        with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh, \
             mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose, \
             mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6,
                            min_tracking_confidence=0.5) as hands:

            while True:
                success, frame = cap.read()
                if not success:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                face_results = face_mesh.process(rgb_frame)
                pose_results = pose.process(rgb_frame)
                hand_results = hands.process(rgb_frame)

                gaze_status = "Unknown"
                posture_status = "Good Posture"
                current_shoulder_y = None

                # ── Face / gaze / blink ───────────────────────────────
                if face_results.multi_face_landmarks:
                    for face_landmarks in face_results.multi_face_landmarks:
                        mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=face_landmarks,
                            connections=mp_face_mesh.FACEMESH_CONTOURS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing.DrawingSpec(
                                color=(0, 255, 0), thickness=1, circle_radius=1
                            ),
                        )
                        ear = calculate_ear(
                            face_landmarks.landmark, LEFT_EYE_TOP_BOTTOM, LEFT_EYE_LEFT_RIGHT
                        )
                        if ear < EAR_THRESHOLD:
                            if not is_blinking:
                                is_blinking = True
                                blink_counter += 1
                        else:
                            is_blinking = False

                        left_iris = face_landmarks.landmark[468]
                        gaze_status = (
                            "Focused on Screen"
                            if 0.35 <= left_iris.x <= 0.65
                            else "Distracted (Looking Away)"
                        )

                # ── Pose / posture ────────────────────────────────────
                if pose_results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                    )
                    ls = pose_results.pose_landmarks.landmark[11]
                    rs = pose_results.pose_landmarks.landmark[12]
                    current_shoulder_y = (ls.y + rs.y) / 2

                    if calibrating:
                        calibration_shoulder_readings.append(current_shoulder_y)
                    elif session.posture_baseline_y is not None:
                        # Slouching = shoulders significantly lower than calibrated baseline
                        if current_shoulder_y > session.posture_baseline_y + session.SLOUCH_DELTA:
                            posture_status = "Slouching Detected"

                # ── Calibration completion ────────────────────────────
                if calibrating and time.time() >= calibration_deadline:
                    calibrating = False
                    if calibration_shoulder_readings:
                        session.posture_baseline_y = sum(calibration_shoulder_readings) / len(calibration_shoulder_readings)
                        print(f"[Calibration] Posture baseline set: shoulder_y = {session.posture_baseline_y:.3f}")
                    else:
                        print("[Calibration] No pose detected — posture check disabled.")

                # ── Phone detection (hand + gaze mismatch) ───────────
                hands_visible = hand_results.multi_hand_landmarks is not None
                if hands_visible:
                    for hand_lm in hand_results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
                # Phone heuristic: hand visible while gaze is away from screen during work
                if hands_visible and gaze_status == "Distracted (Looking Away)" and session.is_working:
                    phone_detected = True
                    phone_detected_until = time.time() + 5.0  # hold the flag for 5s
                if time.time() > phone_detected_until:
                    phone_detected = False

                current_time = time.time()

                # ── 1-second logging tick ────────────────────────────
                if current_time - last_log_time >= 1.0:
                    cached_noise_db = noise_detector.get_db()
                    session.log_frame_state(
                        gaze_status, posture_status, blink_counter,
                        noise_db=cached_noise_db, shoulder_y=current_shoulder_y,
                        active_app=_app_cache["name"],
                    )
                    blink_counter = 0
                    last_log_time = current_time

                    if phone_detected:
                        print(f"[PHONE DETECTED] hands visible + gaze away during work block")

                # ── Intervention check (every 3s, after calibration) ─
                if not calibrating and current_time - last_intervention_time >= 3.0:
                    last_intervention_time = current_time
                    decision = session.evaluate_interventions()
                    if decision:
                        context = {
                            "focus_score": session.compute_focus_score(window_seconds=60),
                            "elapsed_mins": (current_time - session.session_start_time) / 60,
                            "noise_level_db": cached_noise_db,
                            "top_app": session._last_real_app,
                            "blink_rate_per_min": (
                                sum(p["blinks_in_last_sec"] for p in session.history_logs[-60:])
                                * 60 / max(len(session.history_logs[-60:]), 1)
                            ),
                        }
                        threading.Thread(
                            target=fetch_llm_message_async,
                            args=(decision, context, llm_overlay),
                            daemon=True,
                        ).start()

                    # Phone nudge — separate from focus interventions
                    if phone_detected:
                        if not llm_overlay.get("message") or (current_time - llm_overlay.get("timestamp", 0)) > 12:
                            context = {
                                "focus_score": session.compute_focus_score(window_seconds=30),
                                "elapsed_mins": (current_time - session.session_start_time) / 60,
                                "noise_level_db": cached_noise_db,
                                "top_app": session._last_real_app,
                                "blink_rate_per_min": 15,
                            }
                            threading.Thread(
                                target=fetch_llm_message_async,
                                args=("PHONE_DETECTED", context, llm_overlay),
                                daemon=True,
                            ).start()

                # ── Timer auto-transition ─────────────────────────────
                time_left = session.get_remaining_time()
                if time_left <= 0 and not calibrating:
                    old_state = "WORK" if session.is_working else "BREAK"
                    session.is_working = not session.is_working
                    session.block_start_time = time.time()
                    new_state = "WORK" if session.is_working else "BREAK"
                    msg = f"{old_state} ended → {new_state} starting"
                    session.timer_events.append((time.time(), msg))
                    print(f"\n[TIMER] {msg}")

                # ── Draw HUD ──────────────────────────────────────────
                recent_focus = session.compute_focus_score(window_seconds=15)
                noise_label = noise_detector.get_noise_label()
                display_app = session._last_real_app

                draw_hud(
                    frame, session, recent_focus, posture_status, display_app,
                    noise_label, cached_noise_db, llm_overlay,
                    calibrating, calibration_deadline, phone_detected,
                )

                cv2.imshow("Adaptive Pomodoro Buddy", frame)

                # Keep overlay stats line fresh
                if current_time - last_log_time < 0.1:  # just after a log tick
                    try:
                        import json as _json
                        _mins, _secs = divmod(session.get_remaining_time(), 60)
                        _stats = (f"{'WORK' if session.is_working else 'BREAK'} "
                                  f"{_mins:02d}:{_secs:02d}  |  Focus {recent_focus:.0f}%  |  "
                                  f"{noise_label}")
                        _overlay_path = ".overlay_msg"
                        if os.path.exists(_overlay_path):
                            with open(_overlay_path) as _f:
                                _data = _json.load(_f)
                            _data["stats"] = _stats
                            with open(_overlay_path, "w") as _f:
                                _json.dump(_data, _f)
                    except Exception:
                        pass

                key = cv2.waitKey(5) & 0xFF
                if key == ord("q") or key == 27:
                    break

    except KeyboardInterrupt:
        pass
    finally:
        teardown(session, noise_detector, cap)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Adaptive Pomodoro Buddy")
    parser.add_argument("--work", type=int, default=25, help="Work block length in minutes (default 25)")
    parser.add_argument("--break", type=int, default=5, dest="brk", help="Break length in minutes (default 5)")
    args = parser.parse_args()
    run_study_buddy(work_mins=args.work, break_mins=args.brk)
