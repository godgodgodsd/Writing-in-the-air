"""
Gesture Profile System
Handles runtime editable gesture → action mapping.
"""

import json
import os


class GestureProfileManager:

    def __init__(self, profile_path="config/gesture_profile.json"):
        self.profile_path = profile_path
        self.gesture_map = {}
        self.load()

    def load(self):
        if os.path.exists(self.profile_path):
            with open(self.profile_path, "r") as f:
                self.gesture_map = json.load(f)
        else:
            self.gesture_map = {
                "Pointing_Up": "DRAW",
                "Victory": "ERASE",
                "Closed_Fist": "STOP",
                "Open_Palm": "CLEAR",
                "Thumb_Up": "UNDO",
                "Thumb_Down": "REDO"
            }
            self.save()

    def save(self):
        with open(self.profile_path, "w") as f:
            json.dump(self.gesture_map, f, indent=4)

    def set_action(self, gesture_name, action):
        self.gesture_map[gesture_name] = action
        self.save()

    def get_action(self, gesture_name):
        return self.gesture_map.get(gesture_name)

    def get_all(self):
        return self.gesture_map