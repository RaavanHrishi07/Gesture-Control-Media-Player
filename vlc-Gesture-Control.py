
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import mediapipe as mp
import pyautogui


# ============================================================
# Gesture Control Media Player
# MediaPipe Hand Landmarker + Stable Gesture Recognition
# ============================================================

CAMERA_INDEX = 1
CAMERA_BACKEND = cv2.CAP_DSHOW

MODEL_PATH = Path(__file__).parent / "models" / "hand_landmarker.task"

MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.60
MIN_TRACKING_CONFIDENCE = 0.60

HISTORY_SIZE = 9
CONFIRMATION_FRAMES = 6
COMMAND_COOLDOWN = 1.0

# One command per stable gesture.
# Show a different finger count or remove the hand to re-arm.
GESTURE_ACTIONS = {
    1: ("Volume Up", "volumeup"),
    2: ("Volume Down", "volumedown"),
    3: ("Mute", "volumemute"),
    4: ("Play / Pause", "playpause"),
    5: ("Stop", "stop"),
}

FINGER_TIPS = [8, 12, 16, 20]
FINGER_PIPS = [6, 10, 14, 18]


def count_extended_fingers(landmarks):
    """Count extended fingers using hand landmark positions."""
    count = 0

    # Index, middle, ring and little fingers.
    # In image coordinates, smaller y means higher on screen.
    for tip, pip in zip(FINGER_TIPS, FINGER_PIPS):
        if landmarks[tip].y < landmarks[pip].y:
            count += 1

    # Thumb: check whether its tip is extended away from the palm.
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    index_mcp = landmarks[5]

    thumb_extension = abs(thumb_tip.x - thumb_ip.x)
    palm_width = abs(landmarks[5].x - landmarks[17].x)

    if (
        thumb_extension > palm_width * 0.35
        and abs(thumb_tip.x - index_mcp.x) > palm_width * 0.65
    ):
        count += 1

    return count


def draw_hand_landmarks(frame, landmarks):
    """Draw hand joints and connections without the legacy Solutions API."""
    height, width = frame.shape[:2]

    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (17, 18), (18, 19), (19, 20),
        (0, 17),
    ]

    points = []

    for point in landmarks:
        x = int(point.x * width)
        y = int(point.y * height)
        points.append((x, y))

    for start, end in connections:
        cv2.line(
            frame, points[start], points[end],
            (80, 220, 80), 2
        )

    for x, y in points:
        cv2.circle(frame, (x, y), 4, (0, 180, 255), -1)


def main():
    if not MODEL_PATH.is_file():
        print(f"Model file not found: {MODEL_PATH}")
        print("Check that models/hand_landmarker.task exists.")
        return

    camera = cv2.VideoCapture(CAMERA_INDEX, CAMERA_BACKEND)

    if not camera.isOpened():
        print(f"Could not open camera index {CAMERA_INDEX}.")
        print("Close other camera apps and check camera permissions.")
        return

    mp_image = mp.Image
    mp_options = mp.tasks.vision.HandLandmarkerOptions
    mp_base_options = mp.tasks.BaseOptions
    running_mode = mp.tasks.vision.RunningMode

    options = mp_options(
        base_options=mp_base_options(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=running_mode.VIDEO,
        num_hands=MAX_HANDS,
        min_hand_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_hand_presence_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
    )

    history = deque(maxlen=HISTORY_SIZE)
    candidate_gesture = None
    candidate_frames = 0
    active_gesture = None
    last_command_time = 0.0
    frame_timestamp_ms = 0

    print("Gesture Control Media Player started.")
    print("Show 1-5 fingers inside the camera view.")
    print("Remove your hand or change the gesture to re-arm.")
    print("Press Q to quit.")

    try:
        with mp.tasks.vision.HandLandmarker.create_from_options(
            options
        ) as landmarker:

            while True:
                success, frame = camera.read()

                if not success or frame is None:
                    print("Could not read a camera frame.")
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                image = mp_image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame
                )

                frame_timestamp_ms += 33
                result = landmarker.detect_for_video(
                    image, frame_timestamp_ms
                )

                detected_count = None
                status = "Show your hand"

                if result.hand_landmarks:
                    landmarks = result.hand_landmarks[0]
                    draw_hand_landmarks(frame, landmarks)

                    detected_count = count_extended_fingers(landmarks)
                    history.append(detected_count)

                    most_common_count, occurrences = Counter(
                        history
                    ).most_common(1)[0]

                    if occurrences >= 6:
                        status = f"Stable fingers: {most_common_count}"

                        if most_common_count in GESTURE_ACTIONS:
                            if most_common_count == candidate_gesture:
                                candidate_frames += 1
                            else:
                                candidate_gesture = most_common_count
                                candidate_frames = 1

                            if (
                                candidate_frames >= CONFIRMATION_FRAMES
                                and most_common_count != active_gesture
                                and time.monotonic() - last_command_time
                                >= COMMAND_COOLDOWN
                            ):
                                label, action = GESTURE_ACTIONS[
                                    most_common_count
                                ]

                                try:
                                    pyautogui.press(action)
                                    print(f"Gesture: {label}")

                                    active_gesture = most_common_count
                                    last_command_time = time.monotonic()
                                    status = f"Action: {label}"

                                except Exception as error:
                                    print(
                                        f"Could not send media command: {error}"
                                    )

                        else:
                            candidate_gesture = None
                            candidate_frames = 0
                            status = "Fist / 0 fingers - no action"

                else:
                    history.clear()
                    candidate_gesture = None
                    candidate_frames = 0
                    active_gesture = None
                    status = "No hand detected - ready"

                cv2.putText(
                    frame,
                    status,
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    "1: Volume+  2: Volume-  3: Mute",
                    (15, frame.shape[0] - 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    "4: Play/Pause  5: Stop  |  Q: Quit",
                    (15, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2,
                )

                cv2.imshow("Gesture Control Media Player", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\nStopped by user.")

    except Exception as error:
        print(f"Application error: {error}")

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released. Application closed.")


if __name__ == "__main__":
    main()
