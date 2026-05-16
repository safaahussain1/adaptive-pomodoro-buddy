import cv2
import mediapipe as mp
import time
import math
from session_manager import PomodoroSessionManager

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

def run_study_buddy():
    cap = cv2.VideoCapture(0) 
    session = PomodoroSessionManager(work_duration_mins=1, break_duration_mins=1)
    
    last_log_time = time.time()
    last_intervention_time = time.time()
    
    blink_counter = 0
    is_blinking = False
    EAR_THRESHOLD = 0.21  
    
    # Create a persistent variable so we don't have to query macOS 30 times a second
    cached_current_app = "Visual Studio Code"

    with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh, \
         mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        
        print("Sensing Matrix Online: Optimized background polling engaged.")
        
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
                        image=frame, landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
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

            # --- OPTIMIZATION IS HERE ---
            current_time = time.time()
            if current_time - last_log_time >= 1.0:
                # Update the system window check exactly ONCE per second
                cached_current_app = session.get_active_window_macos()
                
                # If macOS returns Electron, visually map it to a user-friendly name on screen
                if cached_current_app in ["Electron", "Electron Framework"]:
                    display_app_name = "VS Code"
                else:
                    display_app_name = cached_current_app

                session.log_frame_state(gaze_status, posture_status, blink_counter)
                blink_counter = 0
                last_log_time = current_time
            # ----------------------------

            if current_time - last_intervention_time >= 3.0:
                decision = session.evaluate_interventions()
                if decision:
                    print(f"\n⚡ INTERVENTION DETECTED: {decision} ⚡\n")
                    last_intervention_time = current_time

            time_left = session.get_remaining_time()
            recent_focus = session.compute_focus_score(window_seconds=15)
            
            if time_left <= 0:
                session.is_working = not session.is_working
                session.block_start_time = time.time()
                print(f"\n🔔 TIMER COMPLETED! Swapping state. 🔔\n")
                time_left = session.get_remaining_time()
            
            mins, secs = divmod(time_left, 60)
            timer_display = f"Timer ({'WORK' if session.is_working else 'BREAK'}): {mins:02d}:{secs:02d}"

            # Clean display name fallback check
            display_app_name = "VS Code" if cached_current_app in ["Electron", "Electron Framework"] else cached_current_app

            cv2.putText(frame, timer_display, (30, 40), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(frame, f"Focus Density: {recent_focus}%", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Current App: {display_app_name}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 128, 0), 2)

            cv2.imshow('Adaptive Pomodoro Buddy - Vision Feed', frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    session.save_session_data()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_study_buddy()