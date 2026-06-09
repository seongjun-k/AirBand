# core/hand_tracker.py
import cv2
import mediapipe as mp
from config import (
    MP_MODEL_COMPLEXITY, MP_MAX_NUM_HANDS,
    MP_MIN_DETECTION_CONF, MP_MIN_TRACKING_CONF,
    FINGERTIP_IDS
)


class HandTracker:
    """
    MediaPipe Hands 래퍼.
    손가락 끝 5점(landmark 4,8,12,16,20)만 추출하여 반환.
    """

    def __init__(self):
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            model_complexity=MP_MODEL_COMPLEXITY,
            max_num_hands=MP_MAX_NUM_HANDS,
            min_detection_confidence=MP_MIN_DETECTION_CONF,
            min_tracking_confidence=MP_MIN_TRACKING_CONF,
        )
        self._draw = mp.solutions.drawing_utils

    def process(self, bgr_frame):
        """
        BGR 프레임 입력 → (results, fingertips) 반환.

        fingertips: List[Dict]
            [{'hand': 'Left'|'Right', 'tips': [(x,y,z) ×5]}, ...]
            좌표는 0.0~1.0 정규화 값
        """
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        fingertips = []

        if results.multi_hand_landmarks and results.multi_handedness:
            for landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                label = handedness.classification[0].label
                tips = [
                    (landmarks.landmark[i].x,
                     landmarks.landmark[i].y,
                     landmarks.landmark[i].z)
                    for i in FINGERTIP_IDS
                ]
                fingertips.append({'hand': label, 'tips': tips})

        return results, fingertips

    def draw_landmarks(self, frame, results):
        """AI 인식 결과 오버레이 (시각화용)"""
        if results.multi_hand_landmarks:
            for lm in results.multi_hand_landmarks:
                self._draw.draw_landmarks(
                    frame, lm, self._mp_hands.HAND_CONNECTIONS
                )
        return frame

    def close(self):
        self._hands.close()
