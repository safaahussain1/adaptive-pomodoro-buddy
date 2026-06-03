import os
import sys

os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")
os.dup2(os.open(os.devnull, os.O_WRONLY), 2)

import cv2
import mediapipe as mp
import time
import math
import threading
import subprocess
import json as _json
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
CALIBRATION_SECONDS = 5
TRANSITION_DISPLAY_SECONDS = 8   # how long the transition overlay stays up

BREAK_TIPS = [
    "Look at something 20 feet away for 20 seconds.",
    "Stand up, stretch your neck and shoulders.",
    "Take 5 slow, deep breaths.",
    "Drink some water.",
    "Rest your eyes — look away from all screens.",
    "Roll your shoulders back and sit tall.",
    "Take a short walk if you can.",
]

TRIGGER_TITLES = {
    "POSTURE_NUDGE":  "Posture Check",
    "EARLY_BREAK":    "Early Break",
    "FLOW_EXTENSION": "Flow +5 min",
    "SESSION_END":    "Session Complete",
    "PHONE_DETECTED": "Phone Detected",
    "WORK_START":     "Work Block Starting",
    "BREAK_START":    "Break Time!",
    "EXTEND":         "Work Extended",
}


def calculate_ear(landmarks, top_bottom_idx, left_right_idx):
    p_top = landmarks[top_bottom_idx[1]]
    p_bottom = landmarks[top_bottom_idx[0]]
    p_left = landmarks[left_right_idx[0]]
    p_right = landmarks[left_right_idx[1]]
    vert = math.sqrt((p_top.x - p_bottom.x)**2 + (p_top.y - p_bottom.y)**2)
    horiz = math.sqrt((p_left.x - p_right.x)**2 + (p_left.y - p_right.y)**2)
    return vert / horiz if horiz != 0 else 0.0


def notify_macos(title: str, message: str):
    safe_msg = message.replace('"', "'").replace("\\", "")
    safe_title = title.replace('"', "'")
    script = f'display notification "{safe_msg}" with title "Pomodoro Buddy" subtitle "{safe_title}"'
    subprocess.Popen(["osascript", "-e", script],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def write_overlay(message, trigger, title, stats=""):
    try:
        with open(".overlay_msg", "w") as f:
            _json.dump({"message": message, "trigger": trigger,
                        "title": title, "ts": time.time(), "stats": stats}, f)
    except Exception:
        pass


def fetch_llm_async(trigger, context, result_container):
    msg = get_coaching_message(trigger, context)
    result_container["message"] = msg
    result_container["trigger"] = trigger
    result_container["timestamp"] = time.time()
    title = TRIGGER_TITLES.get(trigger, trigger)
    print(f"\n[Coach — {title}]\n  {msg}\n")
    notify_macos(title, msg)
    write_overlay(msg, trigger, title)


def draw_work_hud(frame, session, recent_focus, posture_status,
                  display_app, noise_label, cached_noise_db,
                  phone_detected, llm_overlay, calibrating,
                  calibration_deadline, time_left):
    h, w = frame.shape[:2]
    header = frame.copy()
    cv2.rectangle(header, (0, 0), (w, 165), (0, 0, 0), -1)
    cv2.addWeighted(header, 0.55, frame, 0.45, 0, frame)

    mins, secs = divmod(time_left, 60)
    extra = (session.work_duration_seconds - session.base_work_duration_seconds) // 60
    ext_str = f"  (+{extra}m)" if extra > 0 else ""

    # Warn last 30s of work block
    warn_str = "  [E]=extend" if time_left <= 30 and not calibrating else ""

    if calibrating:
        secs_left = max(0, int(calibration_deadline - time.time()))
        cv2.putText(frame, f"CALIBRATING — sit up straight ({secs_left}s)...",
                    (20, 42), cv2.FONT_HERSHEY_DUPLEX, 0.85, (0, 220, 255), 2)
    else:
        timer_color = (0, 200, 255) if time_left > 30 else (0, 80, 255)
        cv2.putText(frame, f"[WORK] {mins:02d}:{secs:02d}{ext_str}{warn_str}",
                    (20, 42), cv2.FONT_HERSHEY_DUPLEX, 1.0, timer_color, 2)

    fc = (0, 255, 0) if recent_focus >= 60 else (0, 165, 255) if recent_focus >= 30 else (0, 0, 255)
    cv2.putText(frame, f"Focus: {recent_focus:.0f}%",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, fc, 2)

    pc = (0, 255, 0) if posture_status == "Good Posture" else (0, 0, 255)
    cv2.putText(frame, f"App: {display_app}  |  Posture: {posture_status}",
                (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.60, pc, 2)

    nc = (200, 200, 200) if cached_noise_db < 55 else (0, 165, 255)
    phone_str = "  |  PHONE DETECTED" if phone_detected else ""
    cv2.putText(frame, f"Noise: {noise_label} ({cached_noise_db:.0f} dB){phone_str}",
                (20, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                (0, 0, 255) if phone_detected else nc, 1)

    _draw_timer_events(frame, session, h, w)
    _draw_coaching_overlay(frame, llm_overlay, h, w)


def draw_break_hud(frame, session, posture_status, noise_label,
                   cached_noise_db, llm_overlay, time_left, tip):
    h, w = frame.shape[:2]
    header = frame.copy()
    cv2.rectangle(header, (0, 0), (w, 165), (0, 30, 10), -1)
    cv2.addWeighted(header, 0.60, frame, 0.40, 0, frame)

    mins, secs = divmod(time_left, 60)
    cv2.putText(frame, f"BREAK  {mins:02d}:{secs:02d}",
                (20, 42), cv2.FONT_HERSHEY_DUPLEX, 1.1, (80, 255, 120), 2)
    cv2.putText(frame, f"Rest your eyes  |  Posture: {posture_status}",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                (80, 255, 120) if posture_status == "Good Posture" else (0, 165, 255), 2)
    cv2.putText(frame, f"Noise: {noise_label} ({cached_noise_db:.0f} dB)",
                (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (160, 220, 160), 1)
    # Break tip
    cv2.putText(frame, f"Tip: {tip}", (20, 148),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 255, 200), 1)

    _draw_timer_events(frame, session, h, w)
    _draw_coaching_overlay(frame, llm_overlay, h, w)


def draw_transition_overlay(frame, going_to_work: bool, seconds_left: int):
    """Full-frame overlay shown during block transitions."""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    color = (0, 20, 60) if going_to_work else (0, 40, 10)
    cv2.rectangle(overlay, (0, 0), (w, h), color, -1)
    cv2.addWeighted(overlay, 0.70, frame, 0.30, 0, frame)

    label = "BACK TO WORK" if going_to_work else "BREAK TIME!"
    text_color = (0, 200, 255) if going_to_work else (80, 255, 120)
    cv2.putText(frame, label, (w // 2 - 200, h // 2 - 30),
                cv2.FONT_HERSHEY_DUPLEX, 1.6, text_color, 3)
    cv2.putText(frame, f"Starting in {seconds_left}s...", (w // 2 - 120, h // 2 + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (220, 220, 220), 2)
    if going_to_work:
        cv2.putText(frame, "Press [E] to add 5 more min first",
                    (w // 2 - 175, h // 2 + 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 100), 1)


def _draw_timer_events(frame, session, h, w):
    now = time.time()
    visible = [(ts, e) for ts, e in session.timer_history if now - ts < 45]
    for i, (_, ev) in enumerate(visible[-3:]):
        cv2.putText(frame, ev, (w - 360, h - 20 - i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 100), 1)


def _draw_coaching_overlay(frame, llm_overlay, h, w):
    now = time.time()
    msg_age = now - llm_overlay.get("timestamp", 0)
    if not llm_overlay.get("message") or msg_age >= 12.0:
        return
    msg = llm_overlay["message"]
    lines = msg.split("\n") if "\n" in msg else _wrap(msg, 68)
    cv2.rectangle(frame, (0, h - 20 - 26 * len(lines)), (w, h), (20, 20, 20), -1)
    for i, line in enumerate(lines):
        cv2.putText(frame, line, (15, h - 12 - 26 * (len(lines) - 1 - i)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1)


def _wrap(text, width):
    words, lines, cur = text.split(), [], []
    for w in words:
        if len(" ".join(cur + [w])) <= width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def teardown(session, noise_detector, cap):
    noise_detector.stop()
    cv2.destroyAllWindows()
    cap.release()

    # Only report work-block data for quality metrics
    work_logs = [p for p in session.history_logs if p.get("is_working_block")]
    print_session_report(session.history_logs)

    if session.history_logs:
        saved_path = save_session_report(session.history_logs,
                                         timer_history=session.timer_history)
        print(f"[Session Saved] → {saved_path}")

    if session.timer_history:
        print("\n[Adaptive Timer Log]")
        for ts, ev in session.timer_history:
            print(f"  {time.strftime('%I:%M:%S %p', time.localtime(ts))}  {ev}")

    if work_logs:
        ctx = {
            "focus_score": sum(p["gaze_score"] == 1 and p["window_is_productive"] == 1
                               for p in work_logs) / len(work_logs) * 100,
            "elapsed_mins": (session.history_logs[-1]["timestamp"] - session.session_start_time) / 60,
            "noise_level_db": sum(p.get("noise_db", 40) for p in session.history_logs) / len(session.history_logs),
            "top_app": max(set(p["active_app"] for p in work_logs),
                           key=lambda a: sum(1 for p in work_logs if p["active_app"] == a)),
            "blink_rate_per_min": sum(p["blinks_in_last_sec"] for p in work_logs) * 60 / len(work_logs),
            "timer_changes": len(session.timer_history),
        }
        print("\n[Coach] Generating end-of-session feedback...")
        msg = get_coaching_message("SESSION_END", ctx)
        print(f"\n>> {msg}\n")

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

    calibrating = True
    calibration_deadline = time.time() + CALIBRATION_SECONDS
    calibration_shoulder_readings = []

    phone_detected = False
    phone_detected_until = 0.0
    hand_visible_since = None   # timestamp when hand first appeared during work

    # Transition state
    in_transition = False
    transition_start = 0.0
    transition_going_to_work = False  # True = transitioning TO work

    # Break tip (rotates each break)
    import random
    break_tip = random.choice(BREAK_TIPS)

    # AppKit in background thread to avoid freezing OpenCV window
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
    print("  Sit up straight for 5s to calibrate posture baseline.")
    print("  Keys: [Q]/[Esc]=quit  [E]=extend work 5 min")
    print("=" * 60)

    write_overlay("Session started — sit up straight for calibration!",
                  "START", "Pomodoro Buddy",
                  f"WORK {work_mins:02d}:00  |  Calibrating")

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
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                face_res = face_mesh.process(rgb)
                pose_res = pose.process(rgb)
                hand_res = hands.process(rgb)

                gaze_status = "Unknown"
                posture_status = "Good Posture"
                current_shoulder_y = None

                # Face / gaze / blink
                if face_res.multi_face_landmarks:
                    for fl in face_res.multi_face_landmarks:
                        mp_drawing.draw_landmarks(
                            frame, fl, mp_face_mesh.FACEMESH_CONTOURS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing.DrawingSpec(
                                color=(0, 255, 0), thickness=1, circle_radius=1))
                        ear = calculate_ear(fl.landmark, LEFT_EYE_TOP_BOTTOM, LEFT_EYE_LEFT_RIGHT)
                        if ear < EAR_THRESHOLD:
                            if not is_blinking:
                                is_blinking = True
                                blink_counter += 1
                        else:
                            is_blinking = False
                        iris = fl.landmark[468]
                        # Wider range (0.28–0.72): accounts for natural screen-reading
                        # movement and slight head turns while still catching when
                        # someone looks fully away (phone, window, etc.)
                        gaze_status = ("Focused on Screen"
                                       if 0.28 <= iris.x <= 0.72
                                       else "Distracted (Looking Away)")

                # Pose / posture
                if pose_res.pose_landmarks:
                    mp_drawing.draw_landmarks(frame, pose_res.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                    ls = pose_res.pose_landmarks.landmark[11]
                    rs = pose_res.pose_landmarks.landmark[12]
                    current_shoulder_y = (ls.y + rs.y) / 2
                    if calibrating:
                        calibration_shoulder_readings.append(current_shoulder_y)
                    elif session.posture_baseline_y is not None:
                        if current_shoulder_y > session.posture_baseline_y + session.SLOUCH_DELTA:
                            posture_status = "Slouching Detected"

                # Calibration complete
                if calibrating and time.time() >= calibration_deadline:
                    calibrating = False
                    if calibration_shoulder_readings:
                        session.posture_baseline_y = (sum(calibration_shoulder_readings)
                                                       / len(calibration_shoulder_readings))
                        print(f"[Calibration] Posture baseline: shoulder_y = {session.posture_baseline_y:.3f}")
                    else:
                        print("[Calibration] No pose detected — posture check disabled.")

                # Phone detection — hand visible for 3+ continuous seconds during work
                hands_in_frame = hand_res.multi_hand_landmarks is not None
                if hands_in_frame:
                    for hl in hand_res.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)

                if session.is_working and hands_in_frame:
                    if hand_visible_since is None:
                        hand_visible_since = time.time()
                    elif time.time() - hand_visible_since >= 3.0:
                        phone_detected = True
                        phone_detected_until = time.time() + 6.0
                else:
                    hand_visible_since = None

                if time.time() > phone_detected_until:
                    phone_detected = False

                current_time = time.time()

                # 1-second logging tick
                if current_time - last_log_time >= 1.0:
                    cached_noise_db = noise_detector.get_db()
                    session.log_frame_state(
                        gaze_status, posture_status, blink_counter,
                        noise_db=cached_noise_db, shoulder_y=current_shoulder_y,
                        active_app=_app_cache["name"],
                    )
                    blink_counter = 0
                    last_log_time = current_time

                # Intervention check (only during work, not in transition)
                if (not calibrating and not in_transition
                        and current_time - last_intervention_time >= 3.0):
                    last_intervention_time = current_time
                    decision = session.evaluate_interventions()
                    if decision:
                        ctx = {
                            "focus_score": session.compute_focus_score(window_seconds=60),
                            "elapsed_mins": (current_time - session.session_start_time) / 60,
                            "noise_level_db": cached_noise_db,
                            "top_app": _app_cache["name"],
                            "blink_rate_per_min": (
                                sum(p["blinks_in_last_sec"] for p in session.history_logs[-60:])
                                * 60 / max(len(session.history_logs[-60:]), 1)
                            ),
                        }
                        threading.Thread(target=fetch_llm_async,
                                         args=(decision, ctx, llm_overlay),
                                         daemon=True).start()

                    # Phone nudge
                    if phone_detected and not llm_overlay.get("message"):
                        ctx = {"focus_score": session.compute_focus_score(30),
                               "elapsed_mins": (current_time - session.session_start_time) / 60,
                               "noise_level_db": cached_noise_db,
                               "top_app": _app_cache["name"], "blink_rate_per_min": 15}
                        threading.Thread(target=fetch_llm_async,
                                         args=("PHONE_DETECTED", ctx, llm_overlay),
                                         daemon=True).start()

                # Timer — start transition warning 30s before end (work only)
                time_left = session.get_remaining_time()
                if (time_left <= 30 and session.is_working
                        and not in_transition and not calibrating
                        and time_left > 0):
                    # Warn but don't flip yet — let E key extend
                    pass

                if time_left <= 0 and not calibrating and not in_transition:
                    in_transition = True
                    transition_start = current_time
                    transition_going_to_work = not session.is_working  # going TO the opposite
                    label = "Break Time!" if not session.is_working else "Back to Work!"
                    print(f"\n[TIMER] {'WORK' if session.is_working else 'BREAK'} ended → {label}")
                    notify_macos(label, "Press [E] in the camera window to extend work.")
                    # Play a gentle tone on break→work only (more important to signal)
                    if session.is_working:  # currently work, transitioning to break — soft chime
                        subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:  # currently break, transitioning to work — stronger alert
                        subprocess.Popen(["afplay", "/System/Library/Sounds/Ping.aiff"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if not session.is_working:
                        break_tip = random.choice(BREAK_TIPS)
                    session.timer_history.append((current_time,
                        f"{'WORK→BREAK' if session.is_working else 'BREAK→WORK'} at {time.strftime('%I:%M %p')}"))

                # Actually flip the block after transition overlay
                if in_transition:
                    elapsed_transition = current_time - transition_start
                    secs_left = max(0, TRANSITION_DISPLAY_SECONDS - int(elapsed_transition))
                    draw_transition_overlay(frame, transition_going_to_work, secs_left)
                    if elapsed_transition >= TRANSITION_DISPLAY_SECONDS:
                        in_transition = False
                        session.is_working = not session.is_working
                        session.block_start_time = time.time()
                else:
                    time_left = session.get_remaining_time()
                    noise_label = noise_detector.get_noise_label()
                    display_app = _app_cache["name"]
                    recent_focus = session.compute_focus_score(window_seconds=15)

                    if session.is_working:
                        draw_work_hud(frame, session, recent_focus, posture_status,
                                      display_app, noise_label, cached_noise_db,
                                      phone_detected, llm_overlay, calibrating,
                                      calibration_deadline, time_left)
                    else:
                        draw_break_hud(frame, session, posture_status, noise_label,
                                       cached_noise_db, llm_overlay, time_left, break_tip)

                    # Update overlay stats strip
                    if current_time - last_log_time < 0.1:
                        block = "WORK" if session.is_working else "BREAK"
                        mins_l, secs_l = divmod(time_left, 60)
                        stats = f"{block} {mins_l:02d}:{secs_l:02d}  |  Focus {recent_focus:.0f}%  |  {noise_label}"
                        try:
                            if os.path.exists(".overlay_msg"):
                                with open(".overlay_msg") as f:
                                    d = _json.load(f)
                                d["stats"] = stats
                                with open(".overlay_msg", "w") as f:
                                    _json.dump(d, f)
                        except Exception:
                            pass

                cv2.imshow("Adaptive Pomodoro Buddy", frame)
                key = cv2.waitKey(5) & 0xFF

                if key == ord("q") or key == 27:
                    break

                # E key: extend work by 5 min (any time during work or transition)
                if key == ord("e") or key == ord("E"):
                    if session.is_working or (in_transition and not transition_going_to_work):
                        session.work_duration_seconds += 300
                        msg = f"Extended +5 min (total {session.work_duration_seconds // 60}m)"
                        session.timer_history.append((current_time, msg))
                        print(f"\n[EXTEND] {msg}")
                        notify_macos("Work Extended", "+5 minutes added")
                        if in_transition:
                            # Cancel the transition — stay in work
                            in_transition = False
                            session.is_working = True
                            session.block_start_time = time.time()
                        llm_overlay["message"] = "You chose to keep going — great commitment! Stay focused."
                        llm_overlay["timestamp"] = current_time

    except KeyboardInterrupt:
        pass
    finally:
        teardown(session, noise_detector, cap)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Adaptive Pomodoro Buddy")
    parser.add_argument("--work", type=int, default=25)
    parser.add_argument("--break", type=int, default=5, dest="brk")
    args = parser.parse_args()
    run_study_buddy(work_mins=args.work, break_mins=args.brk)
