import cv2
import mediapipe as mp
import time
# IMPORT YOUR NEW SESSION MANAGER
from session_manager import PomodoroSessionManager

mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def run_study_buddy():
    # Change camera index to 1 or 2 if index 0 gave you a black screen earlier!
    cap = cv2.VideoCapture(0) 
    
    # Instantiate your new engine
    # Setting an ultra-short 1-minute test block so you can see it transition quickly
    session = PomodoroSessionManager(work_duration_mins=1, break_duration_mins=1)
    
    last_log_time = time.time()

    with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh, \
         mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        
        print("Study Buddy Engine Engaged! Tracking metrics...")
        
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

            # 1. Gaze Tracking
            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    # --- ADD THIS LINE TO BRING BACK FACE LINES ---
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
                    )
                    
                    left_iris = face_landmarks.landmark[468]
                    if left_iris.x < 0.4 or left_iris.x > 0.6:
                        gaze_status = "Distracted (Looking Away)"
                    else:
                        gaze_status = "Focused on Screen"

            # 2. Posture Tracking
            if pose_results.pose_landmarks:
                # --- ADD THIS LINE TO BRING BACK SHOULDER/POSE LINES ---
                mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                left_shoulder = pose_results.pose_landmarks.landmark[11]
                right_shoulder = pose_results.pose_landmarks.landmark[12]
                avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                if avg_shoulder_y > 0.65: 
                    posture_status = "Slouching Detected"

            # 3. Log data precisely once every second to avoid bloating memory
            current_time = time.time()
            if current_time - last_log_time >= 1.0:
                session.log_frame_state(gaze_status, posture_status)
                last_log_time = current_time

            # 4. Fetch dynamic state analytics from our manager module
            time_left = session.get_remaining_time()
            recent_focus = session.compute_focus_score(window_seconds=10) # 10-second rolling view
            
            # Format display string for the countdown timer (MM:SS)
            mins, secs = divmod(time_left, 60)
            timer_string = f"Timer: {mins:02d}:{secs:02d}"

            # 5. UI Overlay Render
            cv2.putText(frame, timer_string, (30, 40), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)
            cv2.putText(frame, f"10s Focus Density: {recent_focus}%", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Current Posture: {posture_status}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow('Adaptive Pomodoro Buddy - Vision Feed', frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    # Save data down to JSON when user terminates the script
    session.save_session_data()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_study_buddy()