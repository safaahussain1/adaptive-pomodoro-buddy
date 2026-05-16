import cv2
import mediapipe as mp
import time
from session_manager import PomodoroSessionManager

mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def simulate_llm_buddy_voice(event_type):
    """
    Placeholder for LLM Integration. Generates context-aware, 
    personalized notification strings based on system states.
    """
    prompts = {
        "POSTURE_NUDGE": "[Buddy]: I noticed your shoulders dropping. Roll them back and straighten up up so you don't ruin your neck posture!",
        "EARLY_BREAK": "[Buddy]: Hey, your focus density took a sharp dip. Forcing myself to read when tired doesn't work—let's shift into a break right now.",
        "FLOW_EXTENSION": "[Buddy]: Exceptional focus! You are in absolute flow right now, so I've adaptively extended this timer by 5 minutes. Ride the wave!"
    }
    return prompts.get(event_type, "")

def run_study_buddy():
    cap = cv2.VideoCapture(0) 
    
    # Using an ultra-short 1-minute work block for quick prototype testing
    session = PomodoroSessionManager(work_duration_mins=1, break_duration_mins=1)
    
    last_log_time = time.time()
    last_intervention_time = time.time()

    with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh, \
         mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        
        print("Study Buddy Active. System running adaptive decision matrix...")
        
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

            # 1. Gaze Tracking Execution
            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        image=frame, landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
                    )
                    left_iris = face_landmarks.landmark[468]
                    if left_iris.x < 0.4 or left_iris.x > 0.6:
                        gaze_status = "Distracted (Looking Away)"
                    else:
                        gaze_status = "Focused on Screen"

            # 2. Posture Tracking Execution
            if pose_results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                left_shoulder = pose_results.pose_landmarks.landmark[11]
                right_shoulder = pose_results.pose_landmarks.landmark[12]
                avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                if avg_shoulder_y > 0.65: 
                    posture_status = "Slouching Detected"

            # 3. Time-Series Metric Logging (Once per second)
            current_time = time.time()
            if current_time - last_log_time >= 1.0:
                session.log_frame_state(gaze_status, posture_status)
                last_log_time = current_time

            # 4. Continuous Operational Evaluation (Check every 3 seconds to avoid alert spamming)
            if current_time - last_intervention_time >= 3.0:
                decision = session.evaluate_interventions()
                if decision:
                    buddy_msg = simulate_llm_buddy_voice(decision)
                    print(f"\n⚡ INTERVENTION TRIGGERED ⚡\n{buddy_msg}\n")
                    last_intervention_time = current_time

            # 5. UI Dashboard Aggregation
            time_left = session.get_remaining_time()
            recent_focus = session.compute_focus_score(window_seconds=15)
            
            # --- ADD THIS AUTOMATIC TRANSITION BLOCK HERE ---
            if time_left <= 0:
                # Toggle the block type
                session.is_working = not session.is_working
                # Reset the clock anchor to the current time so it starts counting down again
                session.block_start_time = time.time()
                
                # Print a notification to the terminal
                next_phase = "WORK" if session.is_working else "BREAK"
                print(f"\n🔔 TIMER COMPLETED! Transitioning to {next_phase} block. 🔔\n")
                
                # Fetch updated time left so the display doesn't flash 00:00 for a frame
                time_left = session.get_remaining_time()
            # ------------------------------------------------
            
            mins, secs = divmod(time_left, 60)
            timer_display = f"Timer ({'WORK' if session.is_working else 'BREAK'}): {mins:02d}:{secs:02d}"

            cv2.putText(frame, timer_display, (30, 40), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(frame, f"Focus Density: {recent_focus}%", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Posture: {posture_status}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow('Adaptive Pomodoro Buddy - Vision Feed', frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    session.save_session_data()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_study_buddy()