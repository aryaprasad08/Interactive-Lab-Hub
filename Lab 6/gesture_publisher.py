# --- RAINBOW GESTURE PUBLISHER SCRIPT (Multi-Device Sync) ---
# Detects thumb direction (left or right) and maps the horizontal position 
# of the thumb tip to the HUE of the color, broadcasting it via SyncDisplay.

import cv2
import mediapipe as mp
import time
import numpy as np
import sys
import os
import colorsys # Python's built-in HSV to RGB conversion

# --- CRITICAL FIX: Ensure current directory is in path for SyncDisplay ---
# This prevents the 'name SyncDisplay is not defined' error under sudo
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
# --- Hardware Imports ---
from sync_display import SyncDisplay 


# --- Configuration ---
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Default RGB for rest state (Dark Gray)
COLOR_DEFAULT_RGB = (50, 50, 50)       

# --- Initialize MediaPipe Hand Detector ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.7, 
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
    sys.exit(1)
    
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
print(f"Webcam initialized successfully at index {camera_index}.")

# --- Functions for Dynamic Color Generation ---

def hsv_to_rgb(h, s=1.0, v=1.0):
    """Converts Hue (0.0-1.0), Saturation, and Value to RGB (0-255)."""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)

def get_rainbow_color(normalized_x):
    """
    Maps normalized X position (0.0 to 1.0) to a continuous Rainbow Hue.
    
    0.0 -> Red/Magenta
    0.5 -> Green
    1.0 -> Blue/Cyan
    """
    # Map the position (0.0 to 1.0) directly to the Hue (0.0 to 1.0).
    # We invert 1-normalized_x to make the left side of the screen 
    # match the start of the spectrum (Red).
    hue = 1.0 - normalized_x
    return hsv_to_rgb(hue)

# --- Initialize SyncDisplay in 'both' mode ---
try:
    sync = SyncDisplay(mode='both')
except Exception as e:
    print(f"FATAL ERROR: Could not initialize SyncDisplay. Check MQTT config/internet. Error: {e}")
    cap.release()
    sys.exit(1)


def draw_debug_info(frame, color_name, active_color_rgb):
    """Draws the instructional text and a colored overlay for the VNC desktop."""
    # Convert RGB color back to BGR for OpenCV display
    active_color_bgr = (active_color_rgb[2], active_color_rgb[1], active_color_rgb[0])
    
    # Create a subtle color overlay for debug view
    overlay = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), active_color_bgr, dtype=np.uint8)
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0) # 70% frame, 30% overlay

    # Add text on top
    text = f"HUE CONTROL: {color_name}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "Position controls HUE (Left=Red, Right=Blue). Press 'q' to quit.", 
                (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    return frame

# --- Main Execution Loop ---
try:
    sync.clear()
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            time.sleep(0.05)
            continue

        frame = cv2.flip(frame, 1) # Flip for mirror view
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        color_name = "Inactive / Neutral"
        active_color_rgb = COLOR_DEFAULT_RGB

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
            thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
            
            # --- Gesture Activation Logic ---
            # If thumb tip is further right than the wrist OR further left than the wrist, 
            # the pointing gesture is active.
            if thumb_tip_x != wrist_x: 
                
                # Use the wrist position (which represents the overall hand position)
                # Note: wrist_x is normalized from 0.0 (right side of screen) to 1.0 (left side)
                normalized_x = wrist_x 
                
                # Determine the continuous rainbow color based on the hand's horizontal position
                active_color_rgb = get_rainbow_color(normalized_x)
                color_name = f"Active ({normalized_x:.2f})"

            # Draw the hand landmarks on the VNC frame
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style())

        
        # 1. Send Command to All Displays (Publish)
        sync.display_color(*active_color_rgb) 
        
        # 2. Draw Debug Info on VNC Desktop
        display_frame = draw_debug_info(frame, color_name, active_color_rgb)
        cv2.imshow('Gesture Publisher (VNC Debug)', display_frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
    # Cleanup resources
    if 'sync' in locals() and sync is not None:
        sync.clear()
        sync.stop()
        
    cap.release()
    cv2.destroyAllWindows()
    print("Webcam released. Program finished.")