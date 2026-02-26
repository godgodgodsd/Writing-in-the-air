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
        self.valid_actions = [
            "DRAW",
            "STOP",
            "CLEAR",
            "ERASE",
            "UNDO",
            "REDO",
            "BUTTON_CLICK",
            None
        ]
        self.custom_actions = []
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
        if action not in self.get_valid_actions():
            raise ValueError(f"Unsupported action: {action}")
        self.gesture_map[gesture_name] = action
        self.save()

    def get_action(self, gesture_name):
        return self.gesture_map.get(gesture_name)

    def get_all(self):
        return self.gesture_map

    def cycle_action(self, gesture_name):
        valid_actions = self.get_valid_actions()
        current = self.gesture_map.get(gesture_name)
        if current not in valid_actions:
            current = None
        idx = valid_actions.index(current)
        new_action = valid_actions[(idx + 1) % len(valid_actions)]
        self.gesture_map[gesture_name] = new_action
        self.save()
        return new_action

    def get_valid_actions(self):
        return self.valid_actions[:-1] + self.custom_actions + [None]

    def set_custom_actions(self, custom_actions):
        self.custom_actions = list(custom_actions)

    def delete_gesture_mapping(self, gesture_name):
        if gesture_name in self.gesture_map:
            del self.gesture_map[gesture_name]
            self.save()

    def clear_action_references(self, action_name):
        changed = False
        for gesture_name, mapped_action in list(self.gesture_map.items()):
            if mapped_action == action_name:
                self.gesture_map[gesture_name] = None
                changed = True
        if changed:
            self.save()
