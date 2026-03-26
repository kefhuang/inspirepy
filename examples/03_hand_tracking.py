"""Track your hand with a webcam and mirror movements on the RH56.

Uses MediaPipe HandLandmarker for hand landmark detection. Uses joint
angles (not distance ratios) for curl estimation, plus a two-pose
calibration step (open hand + fist) to normalize per-person differences.

Install dependencies: pip install -e ".[demo]"

First run will download the hand landmark model (~10MB).

Usage: python examples/03_hand_tracking.py [port]

Press 'q' to quit.
"""

import sys
import os
import math
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)
from inspirepy import InspireHand

# MediaPipe hand landmark indices
WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
LITTLE_MCP, LITTLE_PIP, LITTLE_DIP, LITTLE_TIP = 17, 18, 19, 20

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")

# Finger definitions: (name, MCP, PIP, DIP, TIP)
FINGERS = [
    ("little", LITTLE_MCP, LITTLE_PIP, LITTLE_DIP, LITTLE_TIP),
    ("ring",   RING_MCP,   RING_PIP,   RING_DIP,   RING_TIP),
    ("middle", MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
    ("index",  INDEX_MCP,  INDEX_PIP,  INDEX_DIP,  INDEX_TIP),
]


def ensure_model():
    """Download hand landmarker model if not present."""
    if not os.path.exists(MODEL_PATH):
        print("Downloading hand landmark model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Download complete.")


def angle_between(a, b, c):
    """Angle in degrees at point b, formed by points a-b-c. Uses x,y only."""
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    if mag1 == 0 or mag2 == 0:
        return 180.0
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def finger_joint_angle(landmarks, mcp, pip, dip, tip):
    """Average joint angle across PIP and DIP joints.

    180 = straight, 0 = fully curled.
    """
    pip_angle = angle_between(landmarks[mcp], landmarks[pip], landmarks[dip])
    dip_angle = angle_between(landmarks[pip], landmarks[dip], landmarks[tip])
    return (pip_angle + dip_angle) / 2.0


def thumb_joint_angle(landmarks):
    """Thumb bend angle at MCP and IP joints. 180 = extended, 0 = bent."""
    mcp_angle = angle_between(landmarks[THUMB_CMC], landmarks[THUMB_MCP], landmarks[THUMB_IP])
    ip_angle = angle_between(landmarks[THUMB_MCP], landmarks[THUMB_IP], landmarks[THUMB_TIP])
    return (mcp_angle + ip_angle) / 2.0


def thumb_abduction(landmarks):
    """Thumb distance from palm center, normalized by palm width.

    Higher = thumb away from palm (open), lower = thumb across palm.
    """
    palm_cx = (landmarks[INDEX_MCP].x + landmarks[LITTLE_MCP].x) / 2
    palm_cy = (landmarks[INDEX_MCP].y + landmarks[LITTLE_MCP].y) / 2
    palm_w = math.sqrt(
        (landmarks[INDEX_MCP].x - landmarks[LITTLE_MCP].x) ** 2 +
        (landmarks[INDEX_MCP].y - landmarks[LITTLE_MCP].y) ** 2
    )
    if palm_w == 0:
        return 1.0
    dist = math.sqrt(
        (landmarks[THUMB_TIP].x - palm_cx) ** 2 +
        (landmarks[THUMB_TIP].y - palm_cy) ** 2
    )
    return dist / palm_w


def get_raw_values(landmarks):
    """Extract 6 raw values from landmarks (not yet mapped to 0-1000)."""
    values = []
    for _, mcp, pip, dip, tip in FINGERS:
        values.append(finger_joint_angle(landmarks, mcp, pip, dip, tip))
    values.append(thumb_joint_angle(landmarks))
    values.append(thumb_abduction(landmarks))
    return values


def make_mapper(open_values, closed_values):
    """Create a mapping function from calibrated open/closed raw values.

    Returns a function that maps 6 raw values to 6 ints in 0-1000.
    """
    def mapper(raw_values):
        angles = []
        for raw, open_v, closed_v in zip(raw_values, open_values, closed_values):
            if abs(open_v - closed_v) < 0.001:
                angles.append(500)
                continue
            ratio = (raw - closed_v) / (open_v - closed_v)
            ratio = max(0.0, min(1.0, ratio))
            angles.append(int(ratio * 1000))
        return angles
    return mapper


def draw_landmarks(frame, hand_landmarks, w, h):
    """Draw hand landmarks and connections on frame."""
    connections = [
        (WRIST, THUMB_CMC), (THUMB_CMC, THUMB_MCP), (THUMB_MCP, THUMB_IP), (THUMB_IP, THUMB_TIP),
        (WRIST, INDEX_MCP), (INDEX_MCP, INDEX_PIP), (INDEX_PIP, INDEX_DIP), (INDEX_DIP, INDEX_TIP),
        (WRIST, MIDDLE_MCP), (MIDDLE_MCP, MIDDLE_PIP), (MIDDLE_PIP, MIDDLE_DIP), (MIDDLE_DIP, MIDDLE_TIP),
        (WRIST, RING_MCP), (RING_MCP, RING_PIP), (RING_PIP, RING_DIP), (RING_DIP, RING_TIP),
        (WRIST, LITTLE_MCP), (LITTLE_MCP, LITTLE_PIP), (LITTLE_PIP, LITTLE_DIP), (LITTLE_DIP, LITTLE_TIP),
        (INDEX_MCP, MIDDLE_MCP), (MIDDLE_MCP, RING_MCP), (RING_MCP, LITTLE_MCP),
    ]
    points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
    for a, b in connections:
        cv2.line(frame, points[a], points[b], (0, 255, 0), 2)
    for pt in points:
        cv2.circle(frame, pt, 4, (0, 0, 255), -1)


def detect_hand(landmarker, frame):
    """Run detection and return landmarks or None."""
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
    )
    results = landmarker.detect(mp_image)
    if results.hand_landmarks:
        return results.hand_landmarks[0]
    return None


def collect_stable(cap, landmarker, prompt, ready_fn=None, hold_frames=15):
    """Show prompt, wait until ready_fn returns True, then average hold_frames.

    Args:
        ready_fn: function(raw_values) -> bool. If None, always ready.
    """
    collected = []

    while True:
        ret, frame = cap.read()
        if not ret:
            return None
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        landmarks = detect_hand(landmarker, frame)

        if landmarks:
            draw_landmarks(frame, landmarks, w, h)
            raw = get_raw_values(landmarks)

            is_ready = ready_fn is None or ready_fn(raw)

            if is_ready:
                collected.append(raw)
                progress = min(len(collected), hold_frames)
                cv2.putText(frame, f"{prompt} ({progress}/{hold_frames})",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                if len(collected) >= hold_frames:
                    avg = [sum(v[i] for v in collected) / len(collected) for i in range(6)]
                    return avg
            else:
                collected.clear()
                cv2.putText(frame, prompt, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            collected.clear()
            cv2.putText(frame, prompt, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Hand Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return None


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

    ensure_model()

    hand = InspireHand(port)

    # Start with hand fully open
    print("Opening hand...")
    hand.set_angles([1000, 1000, 1000, 1000, 1000, 1000], speed=500)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam")
        hand.close()
        return

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )
    landmarker = HandLandmarker.create_from_options(options)

    # Calibration: open hand
    # Fingers are "open" when joint angles are large (near 180 = straight)
    def is_open(raw):
        # First 4 values are finger joint angles, check they're mostly straight (>140 deg)
        return all(v > 140 for v in raw[:4])

    print("Step 1: Show your hand FULLY OPEN to the camera and hold steady...")
    open_values = collect_stable(cap, landmarker, "Hold hand FULLY OPEN", ready_fn=is_open)
    if open_values is None:
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()
        hand.close()
        return
    print(f"  Open values: {[f'{v:.1f}' for v in open_values]}")

    # Calibration: closed fist
    # Fingers are "closed" when joint angles drop well below the open values
    def is_closed(raw):
        # First 4 fingers must be significantly more curled than the open position
        return all(raw[i] < open_values[i] * 0.6 for i in range(4))

    print("Step 2: Make a FIST and hold steady...")
    closed_values = collect_stable(cap, landmarker, "Make a FIST", ready_fn=is_closed)
    if closed_values is None:
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()
        hand.close()
        return
    print(f"  Closed values: {[f'{v:.1f}' for v in closed_values]}")

    mapper = make_mapper(open_values, closed_values)
    # Wait for user to open hand again to start tracking
    print("Step 3: Open your hand again to start tracking...")
    start_values = collect_stable(cap, landmarker, "Open hand to START", ready_fn=is_open)
    if start_values is None:
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()
        hand.close()
        return

    print("Tracking started! Press 'q' to quit.")

    # Smoothing: exponential moving average + dead zone
    smoothing = 0.3  # 0.0 = no smoothing, 1.0 = frozen
    dead_zone = 30    # ignore changes smaller than this
    smoothed = [500.0] * 6
    last_sent = [500] * 6

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            landmarks = detect_hand(landmarker, frame)

            if landmarks:
                draw_landmarks(frame, landmarks, w, h)
                raw = get_raw_values(landmarks)
                angles = mapper(raw)

                # Apply EMA smoothing
                for i in range(6):
                    smoothed[i] = smoothed[i] * smoothing + angles[i] * (1 - smoothing)

                # Apply dead zone: only update if change is significant
                send = list(last_sent)
                for i in range(6):
                    if abs(smoothed[i] - last_sent[i]) > dead_zone:
                        send[i] = int(smoothed[i])
                last_sent = send

                hand.set_angles(send, speed=1000)
                angles = send

                names = ["LIT", "RNG", "MID", "IDX", "THB", "THR"]
                for i, (name, angle) in enumerate(zip(names, angles)):
                    cv2.putText(frame, f"{name}: {angle:>4}", (10, 30 + i * 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        print("Resetting to fist pose...")
        hand._serial.reset_input_buffer()
        hand.set_angles([0, 0, 0, 0, 148, 894], speed=500)
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()
        hand.close()
        print("Done.")


if __name__ == "__main__":
    main()
