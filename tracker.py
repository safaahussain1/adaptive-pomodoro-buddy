import cv2
import mediapipe as mp
import time
import math
import threading
from session_manager import PomodoroSessionManager
from noise_detector import AmbientNoiseDetector
from analytics import print_session_report, save_session_report
from llm_coach import get_coaching_message

mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

LEFT_EYE_TOP_BOTTOM = [374, 386]
LEFT_EYE_LEFT_RIGHT = [362, 263]


def calculate_ear(landmarks, top_bottom_idx, left_right_idx):
    p_top = landmarks[top_bottom_idx[1]]
    p_bottom = landmarks[top_bottom_idx[0]]
    p_left = landmarks[left_right_idx[0]]
    p_right = landmarks[left_right_idx[1]]
    vertical_dist = math.sqrt((p_top.x - p_bottom.x)**2 + (p_top.y - p_bottom.y)**2)
    horizontal_dist = math.sqrt((p_left.x - p_right.x)**2 + (p_left.y - p_right.y)**2)
    return vertical_dist / horizontal_dist if horizontal_dist != 0 else 0.0


def fetch_llm_message_async(trigger, context, result_container):
    """Run LLM call in a background thread to avoid blocking the video loop."""
    msg = get_coaching_message(trigger, context)
    result_container["message"] = msg
    result_container["trigger"] = trigger
    result_container["timestamp"] = time.time()


def run_study_buddy():
    cap = cv2.VideoCapture(0)
    session = PomodoroSessionManager(work_duration_mins=25, break_duration_mins=5)
    noise_detector = AmbientNoiseDetector()
    noise_detector.start()

    last_log_time = time.time()
    last_intervention_time = time.time()

    blink_counter = 0
    is_blinking = False
    EAR_THRESHOLD = 0.21

    cached_current_app = "Visual Studio Code"
    cached_noise_db = 40.0

    # LLM coaching message overlay state
    llm_overlay = {"message": "", "trigger": "", "timestamp": 0.0}
    LLM_DISPLAY_SECONDS = 10.0  # how long the coaching message is shown on screen

    print("=" * 60)
    print("  Adaptive Pomodoro Buddy — Sensing Matrix Online")
    print("  Press [Q] to quit and save the session report.")
    print("=" * 60)

    with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh, \
         mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            face_results = face_mesh.process(rgb_frame)
            pose_results = pose.process(rgb_frame)

            gaze_status = "Unknown"
            posture_status = "Good Posture"

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
                    ear = calculate_ear(face_landmarks.landmark, LEFT_EYE_TOP_BOTTOM, LEFT_EYE_LEFT_RIGHT)
                    if ear < EAR_THRESHOLD:
                        if not is_blinking:
                            is_blinking = True
                            blink_counter += 1
                    else:
                        is_blinking = False

                    left_iris = face_landmarks.landmark[468]
                    if left_iris.x < 0.4 or left_iris.x > 0.6:
                        gaze_status = "Distracted (Looking Away)"
                    else:
                        gaze_status = "Focused on Screen"

            if pose_results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                left_shoulder = pose_results.pose_landmarks.landmark[11]
                right_shoulder = pose_results.pose_landmarks.landmark[12]
                avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                if avg_shoulder_y > 0.65:
                    posture_status = "Slouching Detected"

            current_time = time.time()

            # --- 1-second polling tick ---
            if current_time - last_log_time >= 1.0:
                cached_current_app = session.get_active_window_macos()
                cached_noise_db = noise_detector.get_db()
                session.log_frame_state(gaze_status, posture_status, blink_counter, noise_db=cached_noise_db)
                blink_counter = 0
                last_log_time = current_time

            # --- Intervention check every 3 s ---
            if current_time - last_intervention_time >= 3.0:
                decision = session.evaluate_interventions()
                if decision:
                    last_intervention_time = current_time
                    # Build context for LLM
                    context = {
                        "focus_score": session.compute_focus_score(window_seconds=60),
                        "elapsed_mins": (current_time - session.session_start_time) / 60,
                        "noise_level_db": cached_noise_db,
                        "top_app": cached_current_app,
                        "blink_rate_per_min": (
                            sum(p["blinks_in_last_sec"] for p in session.history_logs[-60:]) * 60 / max(len(session.history_logs[-60:]), 1)
                        ),
                    }
                    t = threading.Thread(
                        target=fetch_llm_message_async,
                        args=(decision, context, llm_overlay),
                        daemon=True,
                    )
                    t.start()
                    print(f"\n[{decision}] Fetching coaching message...")

            # --- Timer auto-transition ---
            time_left = session.get_remaining_time()
            if time_left <= 0:
                old_state = "WORK" if session.is_working else "BREAK"
                session.is_working = not session.is_working
                session.block_start_time = time.time()
                new_state = "WORK" if session.is_working else "BREAK"
                print(f"\n[TIMER] {old_state} block ended → starting {new_state} block.")
                time_left = session.get_remaining_time()

            # ==================== DISPLAY ====================
            h, w = frame.shape[:2]
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

            mins, secs = divmod(time_left, 60)
            block_label = "WORK" if session.is_working else "BREAK"
            timer_color = (0, 255, 255) if session.is_working else (255, 180, 0)
            recent_focus = session.compute_focus_score(window_seconds=15)
            noise_label = noise_detector.get_noise_label()

            display_app = "VS Code" if cached_current_app in ["Electron", "Electron Framework"] else cached_current_app

            cv2.putText(frame, f"[{block_label}] {mins:02d}:{secs:02d}", (20, 40),
                        cv2.FONT_HERSHEY_DUPLEX, 1.1, timer_color, 2)
            cv2.putText(frame, f"Focus: {recent_focus:.0f}%", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            cv2.putText(frame, f"App: {display_app}", (20, 115),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 128, 0), 2)
            cv2.putText(frame, f"Noise: {noise_label} ({cached_noise_db:.0f}dB)  Posture: {posture_status}",
                        (20, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

            # LLM coaching message overlay (bottom strip)
            msg_age = current_time - llm_overlay.get("timestamp", 0)
            if llm_overlay.get("message") and msg_age < LLM_DISPLAY_SECONDS:
                msg = llm_overlay["message"]
                # Word-wrap into two lines if long
                words = msg.split()
                line1, line2 = [], []
                for w_word in words:
                    if len(" ".join(line1 + [w_word])) < 72:
                        line1.append(w_word)
                    else:
                        line2.append(w_word)
                cv2.rectangle(frame, (0, h - 90), (w, h), (20, 20, 20), -1)
                cv2.putText(frame, " ".join(line1), (15, h - 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                if line2:
                    cv2.putText(frame, " ".join(line2), (15, h - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow("Adaptive Pomodoro Buddy", frame)

            if cv2.waitKey(5) & 0xFF == ord("q"):
                break

    # Teardown
    noise_detector.stop()
    cap.release()
    cv2.destroyAllWindows()

    # Post-session analytics
    print_session_report(session.history_logs)
    saved_path = save_session_report(session.history_logs)
    print(f"[Session Saved] Full session log → {saved_path}")

    # LLM end-of-session message
    if session.history_logs:
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
        print(f"\n🎯 {msg}\n")


if __name__ == "__main__":
    run_study_buddy()
