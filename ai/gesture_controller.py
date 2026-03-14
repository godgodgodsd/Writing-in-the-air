"""
Gesture Controller using MediaPipe GestureRecognizer Tasks API.
Supports:
- Custom model loading
- Editable confidence threshold
- Dynamic gesture discovery
- Runtime action mapping
"""

import time
import cv2
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
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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

        # Check custom gestures first (e.g., Pinch) so they take priority.
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
        else:
            self.custom_gesture_detector.on_no_hand()

        if gesture_data is None or not gesture_data.gestures:
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

    def create_custom_gesture(self, hand_landmarks, width, height, name=None):
        gesture_name = self.custom_gesture_detector.create_custom_gesture(
            hand_landmarks,
            width,
            height,
            name=name
        )
        if gesture_name:
            self.discovered_gestures.add(gesture_name)
        return gesture_name

    def set_gesture_action(self, gesture_name, action):
        self.profile_manager.set_action(gesture_name, action)

    def cycle_gesture_action(self, gesture_name):
        return self.profile_manager.cycle_action(gesture_name)

    def get_gesture_action(self, gesture_name):
        return self.profile_manager.get_action(gesture_name)

    def get_custom_gesture_names(self):
        return self.custom_gesture_detector.get_custom_gesture_names()

    def delete_custom_gesture(self, gesture_name):
        deleted = self.custom_gesture_detector.delete_custom_gesture(gesture_name)
        if deleted:
            self.profile_manager.delete_gesture_mapping(gesture_name)
            if gesture_name in self.discovered_gestures:
                self.discovered_gestures.remove(gesture_name)
        return deleted

