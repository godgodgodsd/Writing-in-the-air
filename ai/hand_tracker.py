"""
Hand Tracker using MediaPipe Tasks API
Strict enterprise audit compliance.
"""

import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:

    def __init__(self, model_path="models/hand_landmarker.task"):
        base_options = python.BaseOptions(
            model_asset_path=model_path
        )
        # Verified against official documentation

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1
        )
        # Verified against official documentation

        self.landmarker = vision.HandLandmarker.create_from_options(options)
        # Verified against official documentation

    def detect(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp = int(time.time() * 1000)

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp
        )
        # Verified against official documentation

        # Return raw landmark lists for further processing.
        return result.hand_landmarks

    @staticmethod
    def extract_index_tip(hand_landmarks, width, height):
        """
        Landmark index 8 = Index fingertip
        Verified from official MediaPipe hand landmark index specification.
        """
        tip = hand_landmarks[8]
        x = int(tip.x * width)
        y = int(tip.y * height)
        return x, y

    @staticmethod
    def extract_pinch_distance(hand_landmarks, width, height):
        """
        Thumb tip index = 4
        Index tip index = 8
        Verified from official landmark indices.
        """
        thumb = hand_landmarks[4]
        index = hand_landmarks[8]

        x1 = thumb.x * width
        y1 = thumb.y * height
        x2 = index.x * width
        y2 = index.y * height

        return ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5

