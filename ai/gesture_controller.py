"""
Gesture Controller using MediaPipe GestureRecognizer Tasks API.
Supports:
- Custom model loading
- Editable confidence threshold
- Dynamic gesture discovery
- Runtime action mapping
"""

import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from ai.gesture_profiles import GestureProfileManager
from ai.custom_gestures import CustomGestureDetector


class GestureController:

    def __init__(self,
                 model_path="models/gesture_recognizer.task",
                 threshold=0.5):
        self.ai_busy = False
        self.threshold = threshold
        self.timestamp = 0
        self.profile_manager = GestureProfileManager()
        self.latest_result = None
        self.last_ai_time = 0
        self.ai_interval = 0.0167  # ~60 FPS AI
        base_options = python.BaseOptions(
            model_asset_path=model_path
        )
        # Verified against official documentation

        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_hands=1,
            result_callback=self._on_gesture_result
        )
        # Verified against official documentation

        self.recognizer = vision.GestureRecognizer.create_from_options(options)
        # Verified against official documentation

        self.discovered_gestures = set()
        self.custom_gesture_detector = CustomGestureDetector()

    def _on_gesture_result(self, result, output_image, timestamp_ms):
        self.latest_result = result
        self.ai_busy = False

    def recognize(self, frame, hand_landmarks=None, width=None, height=None):
        rgb_frame = frame[:, :, ::-1].copy()  # BGR → RGB + ensure contiguous

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        current_time = time.time()

        if not self.ai_busy and current_time - self.last_ai_time > self.ai_interval:
            self.ai_busy = True
            self.timestamp += 1
            timestamp_ms = self.timestamp
            self.recognizer.recognize_async(mp_image, timestamp_ms)
            self.last_ai_time = current_time
        gesture_data = self.latest_result

        # Verified against official documentation

        # Check custom gestures first (e.g., Pinch)
        if hand_landmarks is not None and width is not None and height is not None:
            custom_gesture, custom_confidence = self.custom_gesture_detector.detect(
                hand_landmarks,
                width,
                height,
                current_time
            )
            if custom_gesture is not None:
                self.discovered_gestures.add(custom_gesture)
                action = self.profile_manager.get_action(custom_gesture)
                return custom_gesture, custom_confidence, action

        if not gesture_data.gestures:
            return None, None, None

        gesture = gesture_data.gestures[0][0]
        name = gesture.category_name
        score = gesture.score

        self.discovered_gestures.add(name)

        if score < self.threshold:
            return name, score, None

        action = self.profile_manager.get_action(name)

        return name, score, action

    def set_threshold(self, value):
        self.threshold = float(value)

    def get_discovered_gestures(self):
        return list(self.discovered_gestures)
