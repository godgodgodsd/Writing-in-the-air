"""
Custom Gesture Detector
Handles gestures that aren't in the MediaPipe model:
- Pinch detection based on thumb-index distance
"""


class CustomGestureDetector:

    def __init__(self):
        self.pinch_threshold = 40  # pixels; distance below this = pinch
        self.pinch_cooldown = 0.5 # seconds between pinch detections
        self.last_pinch_time = 0

    def detect(self, hand_landmarks, width, height, current_time):
        """
        Detect custom gestures from hand landmarks.
        Returns: (gesture_name, confidence) or (None, None)
        """
        if not hand_landmarks:
            return None, None

        # Detect pinch
        pinch_result = self._detect_pinch(hand_landmarks, width, height, current_time)
        if pinch_result:
            gesture_name, confidence = pinch_result
            return gesture_name, confidence

        return None, None

    def _detect_pinch(self, hand_landmarks, width, height, current_time):
        """
        Detects pinch gesture (thumb and index finger touching).
        Returns tuple of (gesture_name, confidence) if detected.
        """
        thumb = hand_landmarks[4]
        index = hand_landmarks[8]

        x1 = thumb.x * width
        y1 = thumb.y * height
        x2 = index.x * width
        y2 = index.y * height

        distance = ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5

        # Check if pinch is active (distance below threshold)
        is_pinching = distance < self.pinch_threshold

        if is_pinching:
            # Check cooldown to avoid duplicate detections
            if current_time - self.last_pinch_time > self.pinch_cooldown:
                self.last_pinch_time = current_time
                # Confidence based on how close the fingers are
                # Closer = higher confidence (distance 0 = 1.0, at threshold = 0.3)
                confidence = max(0.3, 1.0 - (distance / self.pinch_threshold))
                return "Pinch", confidence

        return None, None

    def set_pinch_threshold(self, threshold):
        """Adjust the pinch detection threshold"""
        self.pinch_threshold = threshold

    def set_pinch_cooldown(self, cooldown):
        """Adjust the cooldown between pinch detections"""
        self.pinch_cooldown = cooldown
