"""
Custom Gesture Detector
Handles gestures that aren't in the MediaPipe model:
- Pinch detection based on thumb-index distance
- User-defined gestures based on finger extension patterns
"""

import json
import os
from collections import Counter, deque


class CustomGestureDetector:

    def __init__(self, gestures_path="config/custom_gestures.json"):
        self.gestures_path = gestures_path

        # Pinch detection settings
        self.pinch_threshold = 60.0
        self.pinch_cooldown = 0.5
        self.pinch_release_multiplier = 1.25
        self.pinch_ratio_threshold = 0.55
        self.pinch_stable_frames = 2
        self.pinch_smoothing = 0.35

        # Finger extension settings
        self.extension_on_ratio = 1.12
        self.extension_off_ratio = 1.04
        self._extended_state = [False] * 5

        # Custom gesture stabilization
        self.custom_stable_frames = 3
        self.custom_cooldown = 0.45
        self.mask_match_tolerance_bits = 1
        self.mask_history = deque(maxlen=6)

        self.last_pinch_time = 0.0
        self.last_custom_time = 0.0
        self.custom_gestures = []

        self._pinch_active = False
        self._pinch_candidate_frames = 0
        self._pinch_distance_ema = None
        self._custom_candidate_name = None
        self._custom_candidate_frames = 0
        self._active_custom_name = None

        self._load_custom_gestures()

    def _load_custom_gestures(self):
        data = []
        if os.path.exists(self.gestures_path):
            try:
                with open(self.gestures_path, "r") as f:
                    loaded = json.load(f)
            except (OSError, json.JSONDecodeError):
                loaded = []

            if isinstance(loaded, list):
                data = loaded

        normalized = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            try:
                mask = int(item.get("mask"))
            except (TypeError, ValueError):
                continue
            if 0 <= mask <= 31:
                normalized.append({"name": name, "mask": mask})

        self.custom_gestures = normalized
        if not os.path.exists(self.gestures_path) or normalized != data:
            self._save_custom_gestures()

    def _save_custom_gestures(self):
        directory = os.path.dirname(self.gestures_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.gestures_path, "w") as f:
            json.dump(self.custom_gestures, f, indent=4)

    def on_no_hand(self):
        self._pinch_active = False
        self._pinch_candidate_frames = 0
        self._pinch_distance_ema = None
        self._custom_candidate_name = None
        self._custom_candidate_frames = 0
        self._active_custom_name = None
        self.mask_history.clear()
        self._extended_state = [False] * 5

    def detect(self, hand_landmarks, width, height, current_time):
        """
        Detect custom gestures from hand landmarks.
        Returns: (gesture_name, confidence) or (None, None)
        """
        if not hand_landmarks:
            self.on_no_hand()
            return None, None

        pinch_result = self._detect_pinch(hand_landmarks, width, height, current_time)
        if pinch_result[0] is not None:
            return pinch_result

        custom_result = self._detect_custom_finger_gesture(
            hand_landmarks,
            width,
            height,
            current_time
        )
        if custom_result[0] is not None:
            return custom_result

        return None, None

    def _detect_pinch(self, hand_landmarks, width, height, current_time):
        """
        Detects pinch gesture (thumb and index finger touching).
        Returns tuple of (gesture_name, confidence) only on pinch-down transitions.
        """
        thumb = hand_landmarks[4]
        index = hand_landmarks[8]

        x1 = thumb.x * width
        y1 = thumb.y * height
        x2 = index.x * width
        y2 = index.y * height
        raw_distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        if self._pinch_distance_ema is None:
            smoothed_distance = raw_distance
        else:
            alpha = self.pinch_smoothing
            smoothed_distance = (alpha * raw_distance) + ((1.0 - alpha) * self._pinch_distance_ema)
        self._pinch_distance_ema = smoothed_distance

        palm_size = self._distance(hand_landmarks[0], hand_landmarks[9], width, height)
        dynamic_threshold = min(
            self.pinch_threshold,
            max(16.0, palm_size * self.pinch_ratio_threshold)
        )
        release_threshold = dynamic_threshold * self.pinch_release_multiplier

        if not self._pinch_active:
            if smoothed_distance <= dynamic_threshold:
                self._pinch_candidate_frames += 1
            else:
                self._pinch_candidate_frames = 0

            if self._pinch_candidate_frames >= self.pinch_stable_frames:
                self._pinch_active = True
                self._pinch_candidate_frames = 0
                if current_time - self.last_pinch_time > self.pinch_cooldown:
                    self.last_pinch_time = current_time
                    closeness = max(0.0, 1.0 - (smoothed_distance / max(1e-6, dynamic_threshold)))
                    confidence = max(0.3, min(1.0, 0.3 + (0.7 * closeness)))
                    return "Pinch", confidence
        elif smoothed_distance >= release_threshold:
            self._pinch_active = False

        return None, None

    def _detect_custom_finger_gesture(self, hand_landmarks, width, height, current_time):
        if not self.custom_gestures:
            self._custom_candidate_name = None
            self._custom_candidate_frames = 0
            self._active_custom_name = None
            self.mask_history.clear()
            return None, None

        mask = self._compute_finger_mask(hand_landmarks, width, height)
        self.mask_history.append(mask)

        stable_mask, stable_count = self._get_stable_mask()
        if stable_mask is None or stable_count < self.custom_stable_frames:
            return None, None

        matched_name, bit_difference = self._match_custom_mask(stable_mask)
        if matched_name is None:
            self._custom_candidate_name = None
            self._custom_candidate_frames = 0
            self._active_custom_name = None
            return None, None

        if matched_name != self._custom_candidate_name:
            self._custom_candidate_name = matched_name
            self._custom_candidate_frames = 1
        else:
            self._custom_candidate_frames += 1

        if matched_name != self._active_custom_name and self._active_custom_name is not None:
            self._active_custom_name = None

        if self._custom_candidate_frames < self.custom_stable_frames:
            return None, None

        if matched_name == self._active_custom_name:
            return None, None

        if current_time - self.last_custom_time <= self.custom_cooldown:
            return None, None

        self.last_custom_time = current_time
        self._active_custom_name = matched_name

        stability = stable_count / float(len(self.mask_history))
        match_quality = 1.0 - (bit_difference / float(self.mask_match_tolerance_bits + 1))
        confidence = 0.55 + (0.30 * stability) + (0.15 * match_quality)
        confidence = max(0.55, min(0.95, confidence))
        return matched_name, confidence

    def _compute_finger_mask(self, hand_landmarks, width, height):
        wrist = hand_landmarks[0]

        def is_extended(finger_idx, tip_idx, pip_idx):
            tip = hand_landmarks[tip_idx]
            pip = hand_landmarks[pip_idx]
            tip_dist = self._distance(tip, wrist, width, height)
            pip_dist = self._distance(pip, wrist, width, height)
            ratio = tip_dist / max(1e-6, pip_dist)

            threshold = self.extension_on_ratio
            if self._extended_state[finger_idx]:
                threshold = self.extension_off_ratio

            state = ratio > threshold
            self._extended_state[finger_idx] = state
            return state

        extended = [
            is_extended(0, 4, 3),
            is_extended(1, 8, 6),
            is_extended(2, 12, 10),
            is_extended(3, 16, 14),
            is_extended(4, 20, 18),
        ]

        mask = 0
        for i, state in enumerate(extended):
            if state:
                mask |= (1 << i)
        return mask

    @staticmethod
    def _distance(point_a, point_b, width, height):
        dx = (point_a.x - point_b.x) * width
        dy = (point_a.y - point_b.y) * height
        return (dx * dx + dy * dy) ** 0.5

    def _get_stable_mask(self):
        if not self.mask_history:
            return None, 0
        counts = Counter(self.mask_history)
        stable_mask, stable_count = counts.most_common(1)[0]
        return stable_mask, stable_count

    def _match_custom_mask(self, observed_mask):
        best_name = None
        best_distance = None
        for gesture in self.custom_gestures:
            target_mask = int(gesture.get("mask", -1))
            distance = (target_mask ^ observed_mask).bit_count()
            if distance > self.mask_match_tolerance_bits:
                continue
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_name = gesture.get("name")
        return best_name, best_distance if best_distance is not None else 99

    def create_custom_gesture(self, hand_landmarks, width, height, name=None):
        if not hand_landmarks:
            return None

        mask = self._compute_finger_mask(hand_landmarks, width, height)
        gesture_name = self._resolve_unique_name(name) if name else self._generate_name()

        self.custom_gestures.append({
            "name": gesture_name,
            "mask": mask
        })

        self._save_custom_gestures()
        return gesture_name

    def _generate_name(self):
        base = "Custom"
        existing = {gesture.get("name") for gesture in self.custom_gestures}
        index = 1
        while f"{base}_{index}" in existing:
            index += 1
        return f"{base}_{index}"

    def get_custom_gesture_names(self):
        return [gesture.get("name") for gesture in self.custom_gestures if gesture.get("name")]

    def delete_custom_gesture(self, gesture_name):
        original_len = len(self.custom_gestures)
        self.custom_gestures = [
            gesture for gesture in self.custom_gestures
            if gesture.get("name") != gesture_name
        ]
        if len(self.custom_gestures) != original_len:
            self._save_custom_gestures()
            return True
        return False

    def _resolve_unique_name(self, requested_name):
        cleaned = requested_name.strip()
        if not cleaned:
            return self._generate_name()

        existing = {gesture.get("name") for gesture in self.custom_gestures}
        if cleaned not in existing:
            return cleaned

        suffix = 2
        while f"{cleaned}_{suffix}" in existing:
            suffix += 1
        return f"{cleaned}_{suffix}"

    def set_pinch_threshold(self, threshold):
        """Adjust the pinch detection threshold"""
        self.pinch_threshold = max(8.0, float(threshold))

    def set_pinch_cooldown(self, cooldown):
        """Adjust the cooldown between pinch detections"""
        self.pinch_cooldown = max(0.0, float(cooldown))
