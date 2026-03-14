import os
import json
import cv2


class SessionManager:

    def __init__(self, session_dir="sessions", manifest_name="session.json"):
        self.session_dir = session_dir
        self.manifest_path = os.path.join(session_dir, manifest_name)
        os.makedirs(self.session_dir, exist_ok=True)

    def save_session(self, layer_manager):
        session_data = {
            "layer_paths": [],
            "active_index": layer_manager.active_index,
            "size": {
                "width": layer_manager.width,
                "height": layer_manager.height,
            },
        }

        for i, layer in enumerate(layer_manager.layers):
            path = os.path.join(self.session_dir, f"layer_{i}.png")
            cv2.imwrite(path, layer.canvas)
            session_data["layer_paths"].append(path)

        with open(self.manifest_path, "w") as f:
            json.dump(session_data, f, indent=4)

    def load_session(self, layer_manager):
        if not os.path.exists(self.manifest_path):
            return False

        with open(self.manifest_path, "r") as f:
            data = json.load(f)

        paths = data.get("layer_paths", [])
        if not paths:
            return False

        # Ensure layer count matches session.
        while len(layer_manager.layers) < len(paths):
            layer_manager.add_layer(f"Layer {len(layer_manager.layers)}")

        for i, path in enumerate(paths):
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                continue
            layer_manager.layers[i].canvas = img

        # Drop extra layers not in session.
        if len(layer_manager.layers) > len(paths):
            layer_manager.layers = layer_manager.layers[: len(paths)]

        layer_manager.active_index = min(
            data.get("active_index", 0), len(layer_manager.layers) - 1
        )
        layer_manager.dirty = True
        return True
