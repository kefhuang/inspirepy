"""Play rock-paper-scissors against the RH56 hand.

The robot picks randomly, you show your gesture to the camera.
Countdown: 3, 2, 1, shoot! Then both reveal.

Install dependencies: pip install -e ".[demo]"
Usage: python examples/04_rock_paper_scissors.py [port]

Press 'q' to quit, 'r' to play again.
"""

import sys
import os
import math
import random
import time
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

# Robot hand poses (0=closed, 1000=open)
ROCK = [0, 0, 0, 0, 148, 894]
PAPER = [1000, 1000, 1000, 1000, 1000, 1000]
SCISSORS = [0, 0, 1000, 1000, 148, 894]  # middle + index open
FIST = ROCK


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading hand landmark model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Download complete.")


def angle_between(a, b, c):
    """Angle in degrees at point b, formed by a-b-c. Uses x,y only."""
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    if mag1 == 0 or mag2 == 0:
        return 180.0
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def is_finger_extended(landmarks, mcp, pip, dip, tip):
    """Check if a finger is extended based on PIP joint angle. >140 = extended."""
    pip_angle = angle_between(landmarks[mcp], landmarks[pip], landmarks[dip])
    return pip_angle > 140


def is_thumb_extended(landmarks):
    """Check if thumb is extended."""
    angle = angle_between(landmarks[THUMB_CMC], landmarks[THUMB_MCP], landmarks[THUMB_IP])
    return angle > 140


def classify_gesture(landmarks):
    """Classify hand gesture as rock, paper, or scissors. Returns None if unclear."""
    index = is_finger_extended(landmarks, INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP)
    middle = is_finger_extended(landmarks, MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP)
    ring = is_finger_extended(landmarks, RING_MCP, RING_PIP, RING_DIP, RING_TIP)
    little = is_finger_extended(landmarks, LITTLE_MCP, LITTLE_PIP, LITTLE_DIP, LITTLE_TIP)

    extended = sum([index, middle, ring, little])

    if extended <= 1:
        return "rock"
    elif extended >= 3:
        return "paper"
    elif index and middle and not ring and not little:
        return "scissors"
    return None


def judge(human, robot):
    """Return 'win', 'lose', or 'draw' from human's perspective."""
    if human == robot:
        return "draw"
    wins = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    if wins[human] == robot:
        return "win"
    return "lose"


def draw_landmarks(frame, hand_landmarks, w, h):
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


def detect_hands(landmarker, frame):
    """Run detection and return list of hand landmarks (possibly empty)."""
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
    )
    results = landmarker.detect(mp_image)
    return results.hand_landmarks


def bbox_area(landmarks):
    """Bbox area in normalized image coords. Larger = closer to camera."""
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def select_hand(hands, last_wrist):
    """Pick which detected hand to track.

    Without a prior position, locks onto the largest bbox (closest to camera).
    With one, picks the hand whose wrist is nearest to last_wrist.
    """
    if not hands:
        return None
    if last_wrist is None:
        return max(hands, key=bbox_area)
    lx, ly = last_wrist
    return min(
        hands,
        key=lambda h: (h[WRIST].x - lx) ** 2 + (h[WRIST].y - ly) ** 2,
    )


# Re-acquire after this many consecutive frames without a detection.
LOST_THRESHOLD = 15


def track_hand(landmarker, frame, tracker):
    """Detect hands, lock onto one, and follow it across frames.

    tracker is a dict with 'last_wrist' (tuple|None) and 'lost_frames' (int);
    it is mutated in place. Returns the tracked hand's landmarks or None.
    """
    hands = detect_hands(landmarker, frame)
    if tracker['lost_frames'] > LOST_THRESHOLD:
        tracker['last_wrist'] = None
    landmarks = select_hand(hands, tracker['last_wrist'])
    if landmarks:
        tracker['last_wrist'] = (landmarks[WRIST].x, landmarks[WRIST].y)
        tracker['lost_frames'] = 0
    else:
        tracker['lost_frames'] += 1
    return landmarks


def put_centered_text(frame, text, y, scale=1.0, color=(255, 255, 255), thickness=2):
    h, w = frame.shape[:2]
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0]
    x = (w - text_size[0]) // 2
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

    ensure_model()

    hand = InspireHand(port)
    hand.set_angles(FIST, speed=500)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam")
        hand.close()
        return

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.IMAGE,
        num_hands=4,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )
    landmarker = HandLandmarker.create_from_options(options)

    tracker = {'last_wrist': None, 'lost_frames': 0}

    score_human = 0
    score_robot = 0
    best_of = 0  # 0 = free play
    wins_needed = 0

    print("Rock Paper Scissors!")
    print("  Press '1' for best of 1, '3' for best of 3, '5' for best of 5")
    print("  Press 'r' for free play, 'q' to quit")

    try:
      while True:
        # Mode select
        while True:
            ret, frame = cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            landmarks = track_hand(landmarker, frame, tracker)
            if landmarks:
                draw_landmarks(frame, landmarks, w, h)

            put_centered_text(frame, "ROCK PAPER SCISSORS", h // 2 - 60, 1.0, (255, 255, 255), 2)
            put_centered_text(frame, "1/3/5: best-of  r: free play", h // 2 - 20, 0.7, (0, 255, 255))
            put_centered_text(frame, f"You: {score_human}  Robot: {score_robot}",
                              h // 2 + 20, 0.8, (255, 255, 255))

            cv2.imshow("Rock Paper Scissors", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                return
            if key in (ord('1'), ord('3'), ord('5')):
                best_of = int(chr(key))
                wins_needed = best_of // 2 + 1
                score_human = 0
                score_robot = 0
                break
            if key == ord('r'):
                best_of = 0
                wins_needed = 0
                break

        # Wait for 'r' to start each round
        while True:
            ret, frame = cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            landmarks = track_hand(landmarker, frame, tracker)
            if landmarks:
                draw_landmarks(frame, landmarks, w, h)

            if best_of > 0:
                mode_text = f"Best of {best_of} ({wins_needed} to win)"
                put_centered_text(frame, mode_text, h // 2 - 60, 0.7, (200, 200, 200))

            put_centered_text(frame, "Press 'r' to play!", h // 2 - 20, 1.0, (0, 255, 255))
            put_centered_text(frame, f"You: {score_human}  Robot: {score_robot}",
                              h // 2 + 20, 0.8, (255, 255, 255))

            cv2.imshow("Rock Paper Scissors", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                return
            if key == ord('r'):
                break

            # Robot picks its move
            robot_choice = random.choice(["rock", "paper", "scissors"])

            # Countdown: 3, 2, 1, SHOOT!
            # Robot shakes fist during countdown
            for count in ["3", "2", "1"]:
                # Shake: open slightly then close
                hand.set_angles([200, 200, 200, 200, 148, 894], speed=1000)
                start = time.time()
                while time.time() - start < 0.25:
                    ret, frame = cap.read()
                    if not ret:
                        return
                    frame = cv2.flip(frame, 1)
                    put_centered_text(frame, count, frame.shape[0] // 2, 3.0, (0, 0, 255), 4)
                    cv2.imshow("Rock Paper Scissors", frame)
                    cv2.waitKey(1)

                hand.set_angles(FIST, speed=1000)
                start = time.time()
                while time.time() - start < 0.25:
                    ret, frame = cap.read()
                    if not ret:
                        return
                    frame = cv2.flip(frame, 1)
                    put_centered_text(frame, count, frame.shape[0] // 2, 3.0, (0, 0, 255), 4)
                    cv2.imshow("Rock Paper Scissors", frame)
                    cv2.waitKey(1)

            # SHOOT! Robot shows its move
            robot_pose = {"rock": ROCK, "paper": PAPER, "scissors": SCISSORS}[robot_choice]
            hand.set_angles(robot_pose, speed=1000)

            # Detect human gesture over several frames for reliability
            human_choice = None
            start = time.time()
            while time.time() - start < 2.0:
                ret, frame = cap.read()
                if not ret:
                    return
                frame = cv2.flip(frame, 1)
                h, w = frame.shape[:2]

                landmarks = track_hand(landmarker, frame, tracker)
                if landmarks:
                    draw_landmarks(frame, landmarks, w, h)
                    gesture = classify_gesture(landmarks)
                    if gesture:
                        human_choice = gesture

                put_centered_text(frame, "SHOOT!", h // 2 - 60, 2.0, (0, 0, 255), 3)
                if human_choice:
                    put_centered_text(frame, f"You: {human_choice}", h // 2, 1.0, (255, 255, 0))
                put_centered_text(frame, f"Robot: {robot_choice}", h // 2 + 40, 1.0, (0, 255, 255))

                cv2.imshow("Rock Paper Scissors", frame)
                cv2.waitKey(1)

            # Show result
            if human_choice is None:
                result_text = "No hand detected!"
                result_color = (0, 0, 255)
            else:
                result = judge(human_choice, robot_choice)
                if result == "win":
                    result_text = "You WIN!"
                    result_color = (0, 255, 0)
                    score_human += 1
                elif result == "lose":
                    result_text = "You LOSE!"
                    result_color = (0, 0, 255)
                    score_robot += 1
                else:
                    result_text = "DRAW!"
                    result_color = (0, 255, 255)

            # Check for match winner in best-of mode
            match_winner = None
            if best_of > 0 and wins_needed > 0:
                if score_human >= wins_needed:
                    match_winner = "YOU WIN THE MATCH!"
                    match_color = (0, 255, 0)
                elif score_robot >= wins_needed:
                    match_winner = "ROBOT WINS THE MATCH!"
                    match_color = (0, 0, 255)

            # Display result for 2 seconds (or 3 if match over)
            display_time = 3.0 if match_winner else 2.0
            start = time.time()
            while time.time() - start < display_time:
                ret, frame = cap.read()
                if not ret:
                    return
                frame = cv2.flip(frame, 1)
                h, w = frame.shape[:2]

                landmarks = track_hand(landmarker, frame, tracker)
                if landmarks:
                    draw_landmarks(frame, landmarks, w, h)

                put_centered_text(frame, result_text, h // 2 - 30, 1.5, result_color, 3)
                put_centered_text(frame, f"You: {score_human}  Robot: {score_robot}",
                                  h // 2 + 30, 0.8, (255, 255, 255))
                if match_winner:
                    put_centered_text(frame, match_winner, h // 2 + 80, 1.2, match_color, 3)

                cv2.imshow("Rock Paper Scissors", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return

            # Reset to fist
            hand.set_angles(FIST, speed=500)

            # Match over — go back to mode select
            if match_winner:
                score_human = 0
                score_robot = 0
                best_of = 0
                break

    finally:
        print(f"\nFinal score - You: {score_human}  Robot: {score_robot}")
        hand._serial.reset_input_buffer()
        hand.set_angles(FIST, speed=500)
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()
        hand.close()
        print("Done.")


if __name__ == "__main__":
    main()
