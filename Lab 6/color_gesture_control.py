# --- GESTURE COLOR CONTROL SCRIPT ---
# Uses OpenCV and MediaPipe to detect hand position and change the display color.
# Designed to run on a Raspberry Pi with a Logitech C270 Webcam (or similar).

import cv2
import mediapipe as mp
import time
import numpy as np

# --- Configuration ---
# C270 performs best at these resolutions for performance on the Pi
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Define the colors in BGR format (OpenCV default)
COLOR_LEFT = (255, 0, 0)      # Blue (BGR: Blue is 255)
COLOR_RIGHT = (0, 255, 0)     # Green (BGR: Green is 255)
COLOR_DEFAULT = (50, 50, 50)  # Dark Gray

# --- Initialize MediaPipe Hand Detector ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# --- Initialize Webcam with Camera Index Fallback ---
# Tries index 0 first, then 1 if 0 fails (common for USB webcams on Pi)
cap = cv2.VideoCapture(0) 
if not cap.isOpened():
    print("Warning: Index 0 failed. Trying index 1...")
    cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("FATAL ERROR: Cannot open webcam at index 0 or 1. Check connection and permissions.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
print(f"Webcam initialized at index {cap.get(cv2.CAP_PROP_OPENED)}.")


def draw_info(frame, color_name, active_color):
    """Draws the instructional text and a colored background."""
    # Create a solid color rectangle for the background effect
    overlay = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), active_color, dtype=np.uint8)
    # Blend the frame and the solid color (50% blend)
    frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

    # Add text on top
    text = f"Hand Detected: {color_name}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "Move hand left/right to change color.", (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 
255, 255), 1, cv2.LINE_AA)

    # Draw center line for visual guide
    cv2.line(frame, (FRAME_WIDTH // 2, 0), (FRAME_WIDTH // 2, FRAME_HEIGHT), (255, 255, 255), 1)
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

        # Process the frame with MediaPipe Hands
        results = hands.process(rgb_frame)

        current_color = COLOR_DEFAULT
        color_name = "None"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # We use the WRIST landmark (index 0) to determine position
                wrist_landmark = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                # wrist_landmark.x is normalized to [0.0, 1.0]
                normalized_x = wrist_landmark.x

                # Determine if the hand is on the left or right side of the screen
                # The camera is flipped, so 0.0 is the right side of your camera's view
                if normalized_x < 0.5:
                    # Hand is on the left side of the screen (your right hand)
                    current_color = COLOR_LEFT
                    color_name = "BLUE (Left Screen)"
                else:
                    # Hand is on the right side of the screen (your left hand)
                    current_color = COLOR_RIGHT
                    color_name = "GREEN (Right Screen)"

                # Draw the hand landmarks
                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp.solutions.drawing_utils.HAND_CONNECTIONS,
                    mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp.solutions.drawing_styles.get_default_hand_connections_style())

        # Draw the visual feedback
        display_frame = draw_info(frame, color_name, current_color)

        # Show the resulting image in a window (will display on VNC desktop/PiTFT)
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
