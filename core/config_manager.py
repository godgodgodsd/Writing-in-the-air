"""
Configuration Manager
Loads and validates runtime configuration.
"""

import json
import os


class ConfigManager:

    def __init__(self, path="config/default_config.json"):
        self.path = path
        self.config = {}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Config file not found: {self.path}")

        with open(self.path, "r") as f:
            self.config = json.load(f)

        self.validate()

    def validate(self):
        required = [
            "window_width",
            "window_height",
            "toolbar_height",
            "target_fps",
            "frame_skip"
        ]

        for key in required:
            if key not in self.config:
                raise ValueError(f"Missing config key: {key}")

    def get(self, key):
        return self.config.get(key)