import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Face Mesh and Pose solutions
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def run_study_buddy():
    # Change from 0 to 1 (or 2)
    cap = cv2.VideoCapture(1)
    
    # Initialize the tracking models
    with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh, \
         mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        
        print("Study Buddy Active! Press 'q' in the video window to quit.")
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip the image horizontally for a selfie-view display, convert BGR to RGB
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame with MediaPipe
            face_results = face_mesh.process(rgb_frame)
            pose_results = pose.process(rgb_frame)

            # Simple heuristic flags for your state machine
            gaze_status = "Unknown"
            posture_status = "Good Posture"

            # 1. Analyze Face / Gaze
            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    # Draw subtle face mesh landmarks on the frame
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
                    )
                    
                    # Core Landmark Anchors (Iris tracking)
                    # Landmark 468 is the center of the right iris, 473 is left iris
                    left_iris = face_landmarks.landmark[468]
                    right_iris = face_landmarks.landmark[473]
                    
                    # Basic Gaze Check: Are they looking wildly off-screen?
                    if left_iris.x < 0.4 or left_iris.x > 0.6:
                        gaze_status = "Distracted (Looking Away)"
                    else:
                        gaze_status = "Focused on Screen"

            # 2. Analyze Posture (Shoulder alignment)
            if pose_results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Get coordinates for shoulders (Landmarks 11 and 12)
                left_shoulder = pose_results.pose_landmarks.landmark[11]
                right_shoulder = pose_results.pose_landmarks.landmark[12]
                
                # Slouching heuristic: If shoulders drop too low in the frame view
                # (Note: y-axis goes from 0 at the top to 1 at the bottom)
                avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                if avg_shoulder_y > 0.65:  # Adjust this threshold based on your seating arrangement
                    posture_status = "Slouching Detected"

            # 3. UI Overlay: Display state metrics on screen
            cv2.putText(frame, f"Gaze: {gaze_status}", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Posture: {posture_status}", (30, 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            # Show the live video feed
            cv2.imshow('Adaptive Pomodoro Buddy - Vision Feed', frame)

            # Break the loop safely when 'q' is pressed
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_study_buddy()