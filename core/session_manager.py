import os
import json
import cv2


class SessionManager:

    def __init__(self):
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("exports", exist_ok=True)

    def save_session(self, layer_manager):
        session_data = []

        for i, layer in enumerate(layer_manager.layers):
            path = f"sessions/layer_{i}.png"
            cv2.imwrite(path, layer.canvas)
            session_data.append(path)

        with open("sessions/session.json", "w") as f:
            json.dump(session_data, f)

    def load_session(self, layer_manager):
        try:
            with open("sessions/session.json", "r") as f:
                paths = json.load(f)

            for i, path in enumerate(paths):
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                layer_manager.layers[i].canvas = img
        except:
            pass

    def export_png(self, layer_manager):
        composite = layer_manager.composite()
        cv2.imwrite("exports/export.png", composite)