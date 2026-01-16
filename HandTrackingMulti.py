import cv2
import mediapipe as mp
import numpy as np
import math
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# =================================================================
# AUDIO INTERFACE CONFIGURATION
# Using Pycaw to access system volume controls
# =================================================================
print("[INFO] Initializing Audio Interface...")
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_min, vol_max = volume.GetVolumeRange()[:2]
print("[SUCCESS] Audio Interface Ready.")

# =================================================================
# MEDIAPIPE HANDS INITIALIZATION
# static_image_mode=False for video stream processing
# =================================================================
print("[INFO] Loading Mediapipe Hand Tracking Model...")
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils
print("[SUCCESS] Model Loaded. Starting Camera...")

cap = cv2.VideoCapture(0)
tip_ids = [4, 8, 12, 16, 20]  # Landmarks for Thumb, Index, Middle, Ring, Pinky
finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# Variables for state and UI management
hand_open_start_time = None
laser_coords = []
last_status = ""
vol_bar = 400
vol_percent = 0

while True:
    success, img = cap.read()
    if not success:
        print("[ERROR] Could not read from webcam.")
        break

    img = cv2.flip(img, 1)  # Mirror for natural interaction
    h, w, _ = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    status_text = "IDLE"
    pause_video = False
    active_fingers_info = ""
    current_finger_count = 0

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lm_list = []
            for lm in handLms.landmark:
                # Convert normalized coordinates to pixel values
                lm_list.append((int(lm.x * w), int(lm.y * h)))

            # HANDEDNESS DETECTION: Identifies Left vs Right hand
            hand_label = results.multi_handedness[results.multi_hand_landmarks.index(handLms)].classification[0].label

            fingers = []
            open_names = []

            # THUMB LOGIC: Adjusted based on hand side (X-axis comparison)
            if hand_label == "Left":
                if lm_list[tip_ids[0]][0] > lm_list[tip_ids[0] - 1][0]:
                    fingers.append(1)
                    open_names.append(f"{finger_names[0]}")
                else:
                    fingers.append(0)
            else:
                if lm_list[tip_ids[0]][0] < lm_list[tip_ids[0] - 1][0]:
                    fingers.append(1)
                    open_names.append(f"{finger_names[0]}")
                else:
                    fingers.append(0)

            # VERTICAL FINGERS LOGIC: Compares tip Y-coordinate with PIP joint
            for id in range(1, 5):
                if lm_list[tip_ids[id]][1] < lm_list[tip_ids[id] - 2][1]:
                    fingers.append(1)
                    open_names.append(f"{finger_names[id]}")
                else:
                    fingers.append(0)

            active_fingers_info = ", ".join(open_names)
            current_finger_count = fingers.count(1)
            x2, y2 = lm_list[8]  # Index tip (Landmark 8)

            # ---------------- GESTURE PROCESSING ----------------

            # 1. VOLUME CONTROL: Triggered by Thumb (0) and Index (1)
            if current_finger_count == 2 and fingers[0] == 1 and fingers[1] == 1:
                x1, y1 = lm_list[4]  # Thumb tip
                length = math.hypot(x2 - x1, y2 - y1)  # Euclidean distance
                vol = np.interp(length, [30, 200], [vol_min, vol_max])
                volume.SetMasterVolumeLevel(vol, None)
                status_text = "VOLUME CONTROL"

                # UI feedback for volume
                vol_bar = np.interp(length, [30, 200], [400, 150])
                vol_percent = int(np.interp(length, [30, 200], [0, 100]))
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.circle(img, (x1, y1), 8, (255, 0, 255), -1)
                cv2.circle(img, (x2, y2), 8, (255, 0, 255), -1)

            # 2. EXIT TIMER: Triggered by 5 fingers open for a duration
            elif current_finger_count == 5:
                if hand_open_start_time is None:
                    hand_open_start_time = time.time()

                elapsed_time = int(time.time() - hand_open_start_time)
                status_text = f"EXITING IN {5 - elapsed_time}s"

                if elapsed_time >= 5:
                    print("[SHUTDOWN] Program terminated by gesture.")
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()
                pause_video = True

            # 3. LASER DRAWING: Only Index finger active
            elif current_finger_count == 1 and fingers[1] == 1:
                laser_coords.append((x2, y2))
                if len(laser_coords) > 15: laser_coords.pop(0)  # Maintain trail length
                status_text = "LASER"

            # 4. MUTE: All fingers closed (Fist)
            elif current_finger_count == 0:
                volume.SetMute(1, None)
                status_text = "MUTED"

            else:
                hand_open_start_time = None
                volume.SetMute(0, None)

            # RUNTIME CONSOLE LOGGING (Prints only on state change)
            if status_text != last_status:
                print(f"[EVENT] Mode: {status_text} | Fingers: {current_finger_count} ({active_fingers_info})")
                last_status = status_text

            # Visualizing hand skeleton
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            # Drawing laser trail
            for i in range(1, len(laser_coords)):
                cv2.line(img, laser_coords[i - 1], laser_coords[i], (0, 0, 255), 3)
    else:
        if last_status != "NO HAND":
            print("[WARN] Tracking lost.")
            last_status = "NO HAND"
        hand_open_start_time = None

    # --------- ONSCREEN DASHBOARD (UI) ---------
    cv2.putText(img, f'STATUS: {status_text}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(img, f'FINGERS: {current_finger_count}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, f'OPEN: {active_fingers_info}', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # Graphical Volume Bar
    cv2.rectangle(img, (50, 150), (85, 400), (200, 200, 200), 2)
    cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), -1)
    cv2.putText(img, f'{int(vol_percent)} %', (40, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    if pause_video:
        cv2.putText(img, "PAUSED / EXITING", (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

    cv2.imshow("Advanced Hand Control System", img)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()