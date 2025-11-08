# --- GESTURE PUBLISHER SCRIPT (Multi-Device Sync) ---
# Detects thumb direction (left or right) and publishes the corresponding 
# color command via MQTT using the SyncDisplay class.

import cv2
import mediapipe as mp
import time
import numpy as np
import sys
import os # <--- Moved OS import up

# --- FIX: Add current directory to the Python path FIRST ---
# This ensures sync_display.py can be found, even when run with 'sudo'
sys.path.append(os.getcwd())
# ---------------------------------------------------

# Import the Synchronization class (Now it should work!)
from sync_display import SyncDisplay 


# --- Configuration ---
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Define the colors in BGR format (OpenCV default)
COLOR_RIGHT_THUMB = (255, 0, 0)       # Green (Thumb points Right)
COLOR_LEFT_THUMB = (0, 255, 0)        # Blue (Thumb points Left)
COLOR_DEFAULT = (50, 50, 50)          # Dark Gray (rest state / hand not pointing)

# --- Initialize MediaPipe Hand Detector ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.7, # Increased confidence for more stable detection
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

# --- State Variables ---
active_color = COLOR_DEFAULT


def draw_info(frame, color_name, current_color):
    """Draws the instructional text and a colored background."""
    # Create a solid color rectangle for the background effect
    overlay = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), current_color, dtype=np.uint8)
    # Blend the frame and the solid color (50% blend)
    frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

    # Add text on top
    text = f"THUMB: {color_name}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "Point thumb left or right. Press 'q' to quit.", (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
(255, 255, 255), 1, cv2.LINE_AA)
    
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

        color_name = "Neutral / Not Pointing"
        active_color = COLOR_DEFAULT

        if results.multi_hand_landmarks:
            # We track the first detected hand
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Get normalized X coordinates for the Wrist (0) and Thumb Tip (4)
            wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
            thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
            
            # --- Thumb Direction Logic (Frame is Flipped) ---
            
            # If thumb tip is further right on the screen (smaller X value) than the wrist, 
            # the thumb is pointing to the physical RIGHT.
            if thumb_tip_x < wrist_x:
                active_color = COLOR_RIGHT_THUMB
                color_name = "LEFT (Blue)"
            
            # If thumb tip is further left on the screen (larger X value) than the wrist, 
            # the thumb is pointing to the physical LEFT.
            elif thumb_tip_x > wrist_x:
                active_color = COLOR_LEFT_THUMB
                color_name = "RIGHT (Green)"


            # Draw the hand landmarks
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style())

        
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
