import cv2
import mediapipe as mp
import numpy as np
import math
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# =========================
# إعداد التحكم بالصوت
# =========================
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_min, vol_max = volume.GetVolumeRange()[:2]


# =========================
# Mediapipe Hand Tracking
# =========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
tip_ids = [4, 8, 12, 16, 20]
finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# =========================
# Variables
# =========================
freeze_frame = None
hand_open_start_time = None
laser_coords = []

while True:
    if freeze_frame is None:
        success, img = cap.read()
        if not success: break
        img = cv2.flip(img, 1)
    else:
        img = freeze_frame.copy()

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    pause_video = False
    status_text = "IDLE"
    active_fingers_info = ""

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lm_list = []
            h, w, _ = img.shape
            for lm in handLms.landmark:
                lm_list.append((int(lm.x * w), int(lm.y * h)))
            hand_label = results.multi_handedness[results.multi_hand_landmarks.index(handLms)].classification[0].label
            # --------- Count Fingers & Names ---------
            fingers = []
            open_names = []

            # 1. منطق الإبهام حسب نوع اليد (Thumb Logic)
            if hand_label == "Left":  # اليد اليسار
                if lm_list[tip_ids[0]][0] > lm_list[tip_ids[0] - 1][0]:
                    fingers.append(1)
                    open_names.append(f"{finger_names[0]}(4)")
                else:
                    fingers.append(0)
            else:  # اليد اليمين (Right)
                if lm_list[tip_ids[0]][0] < lm_list[tip_ids[0] - 1][0]:
                    fingers.append(1)
                    open_names.append(f"{finger_names[0]}(4)")
                else:
                    fingers.append(0)

            # 2. باقي الأصابع (نفس منطقك العمودي)
            for id in range(1, 5):
                if lm_list[tip_ids[id]][1] < lm_list[tip_ids[id] - 2][1]:
                    fingers.append(1)
                    open_names.append(f"{finger_names[id]}({tip_ids[id]})")
                else:
                    fingers.append(0)

            active_fingers_info = ", ".join(open_names)
            x2, y2 = lm_list[8]

            # --------- Volume Control (2 Fingers) ----------
            if fingers.count(1) == 2:
                if fingers[0] == 1 and fingers[1] == 1:
                    x1, y1 = lm_list[4]
                    length = math.hypot(x2 - x1, y2 - y1)
                    vol = np.interp(length, [30, 200], [vol_min, vol_max])
                    volume.SetMasterVolumeLevel(vol, None)

                    cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    cv2.circle(img, (x1, y1), 8, (255, 0, 255), -1)
                    cv2.circle(img, (x2, y2), 8, (255, 0, 255), -1)

                    vol_bar = np.interp(length, [30, 200], [400, 150])
                    vol_percent = np.interp(length, [30, 200], [0, 100])
                    cv2.rectangle(img, (50, 150), (85, 400), (200, 200, 200), 2)
                    cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), -1)
                    cv2.putText(img, f'{int(vol_percent)} %', (40, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    status_text = "VOLUME CONTROL"

            # --------- Pause/Exit Logic (5 Fingers) ----------
            if fingers.count(1) == 5:
                if hand_open_start_time is None:
                    hand_open_start_time = time.time()
                elif time.time() - hand_open_start_time >= 5:
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()
                pause_video = True
                status_text = "EXITING..."
            else:
                hand_open_start_time = None

            # --------- Laser Draw Logic (1 Finger) ----------
            if fingers.count(1) == 1:
                laser_coords.append((x2, y2))
                if len(laser_coords) > 15:
                    laser_coords.pop(0)
                for i in range(1, len(laser_coords)):
                    cv2.line(img, laser_coords[i - 1], laser_coords[i], (0, 0, 255), 3)
                status_text = "LASER"

            if fingers.count(1) == 0:
                volume.SetMute(1, None)
                status_text = "MUTED"
            else:
                volume.SetMute(0, None)


            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
    else:
        hand_open_start_time = None


    # --------- Display Info on Screen ---------
    cv2.putText(img, f'STATUS: {status_text}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(img, f'FINGERS: {fingers.count(1) if results.multi_hand_landmarks else 0}', (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, f'OPEN: {active_fingers_info}', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    if pause_video:
        cv2.putText(img, "PAUSED", (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

    cv2.imshow("Hand Volume Control", img)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()