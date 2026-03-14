import cv2
import numpy as np


class GestureManagementUI:
    def __init__(self, width=520, height=720):
        self.width = width
        self.height = height
        self.click_targets = []
        self.open_dropdown_for = None
        self.gesture_name_input = ""
        self.action_name_input = ""
        self.active_input = None

    def draw(
        self,
        current_gesture_name,
        current_confidence,
        gesture_map,
        valid_actions,
        last_toolbar_click,
        is_recording_action,
        recorded_clicks,
        custom_gesture_names,
        custom_actions_map,
        info_message=None
    ):
        panel = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        panel[:] = (28, 28, 28)
        self.click_targets = []

        cv2.putText(panel, "Gesture Management", (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        gesture_text = "Current: None"
        if current_gesture_name:
            gesture_text = f"Current: {current_gesture_name} ({current_confidence:.2f})"
        cv2.putText(panel, gesture_text[:60], (15, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 220, 255), 1)

        self._draw_button(panel, 15, 70, 120, 30, "Type Name", ("focus_gesture_name", None), 0.45)
        self._draw_button(panel, 140, 70, 160, 30, "Create Gesture", ("create_custom_named", None), 0.45)
        self._draw_button(panel, 305, 70, 90, 30, "Clear", ("clear_gesture_name", None), 0.45)
        self._draw_button(panel, 400, 70, 100, 30, "Delete Curr", ("delete_current_gesture", None), 0.45)

        self._draw_input_box(panel, 15, 104, 485, 28, "Gesture Name", self.gesture_name_input, "gesture_name")

        record_label = "Stop Recording" if is_recording_action else "Start Recording"
        self._draw_button(panel, 15, 140, 130, 30, record_label, ("toggle_action_recording", None), 0.45)
        self._draw_button(panel, 150, 140, 150, 30, "Type Action Name", ("focus_action_name", None), 0.45)
        self._draw_button(panel, 305, 140, 95, 30, "Save Action", ("save_recorded_action", None), 0.45)
        self._draw_button(panel, 405, 140, 95, 30, "Clear Name", ("clear_action_name", None), 0.45)

        self._draw_input_box(panel, 15, 174, 485, 28, "Action Name", self.action_name_input, "action_name")

        click_text = f"Last toolbar click: {last_toolbar_click}" if last_toolbar_click else "Last toolbar click: None"
        cv2.putText(panel, click_text[:78], (15, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 210, 255), 1)
        rec_text = "Recorded clicks: " + (", ".join(recorded_clicks) if recorded_clicks else "<none>")
        cv2.putText(panel, rec_text[:78], (15, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140, 230, 170), 1)

        cv2.putText(panel, "Gesture -> Action", (15, 294), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1)
        y = 320
        for gesture_name in sorted(gesture_map.keys()):
            action = gesture_map.get(gesture_name)
            action_text = "None" if action is None else str(action)

            cv2.putText(panel, gesture_name[:24], (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (210, 210, 210), 1)
            self._draw_button(panel, 210, y - 16, 175, 24, action_text, ("toggle_dropdown", gesture_name), 0.43)

            if gesture_name in custom_gesture_names:
                self._draw_button(panel, 390, y - 16, 110, 24, "Delete", ("delete_custom_gesture", gesture_name), 0.43)

            y += 30
            if self.open_dropdown_for == gesture_name:
                for action_name in valid_actions:
                    option_text = "None" if action_name is None else str(action_name)
                    self._draw_button(
                        panel,
                        210,
                        y - 16,
                        175,
                        24,
                        option_text,
                        ("set_named_action", (gesture_name, action_name)),
                        0.43
                    )
                    y += 26
            if y > 560:
                break

        cv2.putText(panel, "Custom Actions", (15, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1)
        ay = 616
        for action_name, clicks in sorted(custom_actions_map.items()):
            sequence_text = " > ".join(clicks)
            cv2.putText(panel, action_name[:20], (15, ay), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (210, 210, 210), 1)
            cv2.putText(panel, sequence_text[:28], (160, ay), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (170, 170, 170), 1)
            self._draw_button(panel, 430, ay - 16, 70, 24, "Delete", ("delete_custom_action", action_name), 0.42)
            ay += 28
            if ay > self.height - 42:
                break

        if info_message:
            cv2.putText(panel, info_message[:80], (15, self.height - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 255, 255), 1)

        return panel

    def _draw_input_box(self, panel, x, y, w, h, label, value, input_id):
        color = (90, 140, 220) if self.active_input == input_id else (120, 120, 120)
        cv2.rectangle(panel, (x, y), (x + w, y + h), (50, 50, 50), -1)
        cv2.rectangle(panel, (x, y), (x + w, y + h), color, 1)
        shown = value if value else "<auto>"
        cv2.putText(panel, f"{label}: {shown}"[:76], (x + 5, y + 19), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (240, 240, 240), 1)

    def _draw_button(self, panel, x, y, w, h, text, payload, font_scale=0.5):
        cv2.rectangle(panel, (x, y), (x + w, y + h), (70, 70, 70), -1)
        cv2.rectangle(panel, (x, y), (x + w, y + h), (130, 130, 130), 1)
        cv2.putText(panel, text, (x + 6, y + int(h * 0.65)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1)
        self.click_targets.append({"x1": x, "y1": y, "x2": x + w, "y2": y + h, "payload": payload})

    def detect_click(self, x, y):
        for target in self.click_targets:
            if target["x1"] <= x <= target["x2"] and target["y1"] <= y <= target["y2"]:
                action, value = target["payload"]

                if action == "toggle_dropdown":
                    self.open_dropdown_for = None if self.open_dropdown_for == value else value
                    return ("refresh", None)

                if action == "set_named_action":
                    self.open_dropdown_for = None
                    self.active_input = None
                    return target["payload"]

                if action == "focus_gesture_name":
                    self.active_input = "gesture_name"
                    return ("refresh", None)

                if action == "focus_action_name":
                    self.active_input = "action_name"
                    return ("refresh", None)

                if action == "clear_gesture_name":
                    self.gesture_name_input = ""
                    return ("refresh", None)

                if action == "clear_action_name":
                    self.action_name_input = ""
                    return ("refresh", None)

                self.open_dropdown_for = None
                self.active_input = None
                return target["payload"]

        self.open_dropdown_for = None
        self.active_input = None
        return None

    def handle_key(self, key):
        if self.active_input not in ("gesture_name", "action_name"):
            return None

        if key in (13, 10, 27):
            self.active_input = None
            return ("refresh", None)

        if key in (8, 127):
            if self.active_input == "gesture_name":
                self.gesture_name_input = self.gesture_name_input[:-1]
            else:
                self.action_name_input = self.action_name_input[:-1]
            return ("refresh", None)

        if 32 <= key <= 126:
            if self.active_input == "gesture_name" and len(self.gesture_name_input) < 32:
                self.gesture_name_input += chr(key)
                return ("refresh", None)
            if self.active_input == "action_name" and len(self.action_name_input) < 32:
                self.action_name_input += chr(key)
                return ("refresh", None)

        return None
