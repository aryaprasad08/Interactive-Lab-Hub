# --- GESTURE COLOR CONTROL SCRIPT (DIRECTION INFERENCE) ---
# Tracks hand position across frames to infer left or right sweeping motion.

import cv2
import mediapipe as mp
import time
import numpy as np

# --- Configuration ---
# C270 performs best at these resolutions for performance on the Pi
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Define the colors in BGR format (OpenCV default)
COLOR_RIGHT_SWEEP = (0, 255, 0)       # Green (for sweeping right)
COLOR_LEFT_SWEEP = (255, 0, 0)        # Blue (for sweeping left)
COLOR_DEFAULT = (50, 50, 50)          # Dark Gray (rest state)

# Motion detection settings
SWEEP_THRESHOLD = 0.05    # Minimum normalized X change (0.0 to 1.0) to register a sweep
FRAME_HOLD_DURATION = 30  # Number of frames to hold the color after a sweep

# --- Initialize MediaPipe Hand Detector ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# --- Initialize Webcam with Camera Index Fallback ---
camera_index = 0
cap = cv2.VideoCapture(camera_index) 
if not cap.isOpened():
    camera_index = 1
    print("Warning: Index 0 failed. Trying index 1...")
    cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("FATAL ERROR: Cannot open webcam at index 0 or 1. Check connection and permissions.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
print(f"Webcam initialized successfully at index {camera_index}.")

# --- State Variables for Direction Tracking ---
prev_x = None               # Previous normalized X position of the wrist
active_color = COLOR_DEFAULT
color_hold_frames = 0       # Counter to keep the gesture color visible


def draw_info(frame, color_name, current_color):
    """Draws the instructional text and a colored background."""
    # Create a solid color rectangle for the background effect
    overlay = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), current_color, dtype=np.uint8)
    # Blend the frame and the solid color (50% blend)
    frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

    # Add text on top
    text = f"GESTURE: {color_name}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "Sweep left or right to change color. Press 'q' to quit.", (10, FRAME_HEIGHT - 10), 
cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    return frame

try:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            time.sleep(0.05)
            continue

        # Flip the frame horizontally for a more intuitive "mirror" view
        frame = cv2.flip(frame, 1)

        # To improve performance, convert the frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        # Reset state defaults for the frame
        gesture_detected = False
        color_name = "Waiting for Sweep"

        if results.multi_hand_landmarks:
            # We track the first detected hand's WRIST landmark (index 0)
            hand_landmarks = results.multi_hand_landmarks[0]
            current_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x

            if prev_x is not None:
                # Calculate the difference in X position
                # Note: Because the frame is FLIPPED (mirror view), 
                # sweeping to your physical right results in X DECREASING (negative delta).
                delta_x = current_x - prev_x

                if delta_x < -SWEEP_THRESHOLD:
                    # Detected a sweep to the physical RIGHT (X is decreasing)
                    active_color = COLOR_RIGHT_SWEEP
                    color_name = "SWEEP RIGHT!"
                    color_hold_frames = FRAME_HOLD_DURATION
                    gesture_detected = True
                
                elif delta_x > SWEEP_THRESHOLD:
                    # Detected a sweep to the physical LEFT (X is increasing)
                    active_color = COLOR_LEFT_SWEEP
                    color_name = "SWEEP LEFT!"
                    color_hold_frames = FRAME_HOLD_DURATION
                    gesture_detected = True

            # Update previous position for the next frame
            prev_x = current_x

            # Draw the hand landmarks regardless of gesture detection
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style())

        else:
            # Hand not detected, reset previous position
            prev_x = None
        
        
        # --- Handle Color Hold Logic ---
        if color_hold_frames > 0:
            color_hold_frames -= 1
            if color_hold_frames == 0:
                # Reset to default color and name when hold duration expires
                active_color = COLOR_DEFAULT
                color_name = "Ready"
        
        # Update text if we are just waiting or holding
        if color_name == "Waiting for Sweep" and color_hold_frames > 0:
             color_name = f"HOLDING ({color_hold_frames})"


        # Draw the visual feedback
        display_frame = draw_info(frame, color_name, active_color)

        # Show the resulting image in a window 
        cv2.imshow('Gesture Control', display_frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
