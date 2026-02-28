import cv2
import time
import json
import os

from ai.hand_tracker import HandTracker
from ai.gesture_controller import GestureController

from engine.layer_manager import LayerManager
from engine.stroke_engine import StrokeEngine

from ui.toolbar import Toolbar
from ui.ui_renderer import UIRenderer
from ui.gesture_management_ui import GestureManagementUI

from core.performance_manager import PerformanceManager
from core.export_manager import ExportManager




class AppController:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # AI systems
        self.hand_tracker = HandTracker()
        self.gesture_controller = GestureController()

        # Drawing systems
        self.layer_manager = LayerManager(width, height)
        self.stroke_engine = StrokeEngine(self.layer_manager)

        # UI
        self.toolbar = Toolbar(width)
        self.ui_renderer = UIRenderer()
        self.gesture_ui = GestureManagementUI()

        # State
        self.current_action = None
        self.current_gesture_name = None
        self.current_gesture_confidence = None
        self.latest_hand_landmarks = None
        self.info_message = None
        self.info_message_until = 0
        self.last_toolbar_button_click = None
        self.is_recording_action = False
        self.recorded_action_clicks = []
        self.custom_actions_path = "config/custom_actions.json"
        self.custom_actions = self._load_custom_actions()
        self.gesture_controller.profile_manager.set_custom_actions(list(self.custom_actions.keys()))

        self.export_manager = ExportManager()

        self.performance = PerformanceManager(
            self.gesture_controller,
            self.hand_tracker,
            skip_rate=1
        )
        # Finger click (pinch) state
        self.finger_clicking = False
        self.finger_click_threshold = 60    # threshold to register pinch in pixels
        self.last_pinch_button = None       # track which button is being held
        self.last_size_adjust_time = 0      # throttle size adjustments
        
        # Brush cycling
        self.brush_types = ["round", "square", "spray"]
        self.current_brush_index = 0
        self.stroke_engine.brush.set_brush(self.brush_types[self.current_brush_index])

    def process_frame(self, frame):
        gesture_data, hands = self.performance.process(frame)
        gesture_name = None
        confidence = None
        action = None

        if gesture_data:
            gesture_name, confidence, action = gesture_data

        index_point = None
        pinch_distance = None

        if hands:
            hand = hands[0]
            self.latest_hand_landmarks = hand

            index_point = self.hand_tracker.extract_index_tip(
                hand,
                self.width,
                self.height
            )

            pinch_distance = self.hand_tracker.extract_pinch_distance(
                hand,
                self.width,
                self.height
            )

            cv2.circle(frame, index_point, 6, (0, 255, 0), -1)
        else:
            self.latest_hand_landmarks = None

        self.current_gesture_name = gesture_name
        self.current_gesture_confidence = confidence

        # === Gesture Action Handling ===
        if action == "DRAW":
            if not self.stroke_engine.drawing:
                self.stroke_engine.start_stroke()

        elif action == "STOP":
            self.stroke_engine.end_stroke()

        elif action == "CLEAR":
            self.layer_manager = LayerManager(self.width, self.height)
            self.stroke_engine = StrokeEngine(self.layer_manager)

        elif action == "ERASE":
            # Switch to eraser brush; start stroke if not already erasing
            self.stroke_engine.brush.set_brush("eraser")
            if not self.stroke_engine.drawing:
                self.stroke_engine.start_stroke()

        elif action == "UNDO":
            self.layer_manager.get_active_layer().undo()

        elif action == "REDO":
            self.layer_manager.get_active_layer().redo()

        elif action == "BUTTON_CLICK":
            pass
        elif action in self.custom_actions:
            for mapped_button in self.custom_actions[action]:
                self._apply_button_action(mapped_button, record_click=False)

        # === Drawing Update ===
        if index_point:
            self.stroke_engine.update(index_point, pinch_distance)

        # === Composite Layers ===
        canvas = self.layer_manager.composite()

        # === Overlay Canvas on Frame ===
        frame = cv2.addWeighted(frame, 0.4, canvas, 0.6, 0)

        # === Draw Toolbar ===
        self.toolbar.draw(frame)

        # === Brush Preview ===
        if index_point:
            self.ui_renderer.draw_brush_preview(
                frame,
                index_point,
                self.stroke_engine.brush.base_size,
                (0, 255, 0)
            )

        # === Finger (pinch) click handling for toolbar ===
        # Use thumb-index pinch distance to simulate a click when inside toolbar
        if index_point is not None and pinch_distance is not None:
            if pinch_distance < self.finger_click_threshold and not self.finger_clicking:
                # Pinch detected -> register click
                self.finger_clicking = True
                self.last_size_adjust_time = time.time()
                bx, by = index_point
                button = self.toolbar.detect_click(bx, by)
                self.last_pinch_button = button
                if button:
                    self._apply_button_action(button)

            elif self.finger_clicking and pinch_distance < self.finger_click_threshold:
                # Pinch held -> continuously adjust size if size button
                if self.last_pinch_button in ("+Size", "-Size"):
                    current_time = time.time()
                    # Throttle to ~10 times per second (100ms per adjustment)
                    if current_time - self.last_size_adjust_time > 0.1:
                        self._apply_button_action(self.last_pinch_button)
                        self.last_size_adjust_time = current_time

            elif pinch_distance >= self.finger_click_threshold:
                # Pinch released
                self.finger_clicking = False
                self.last_pinch_button = None

        # === Status ===
        if gesture_name:
            self.ui_renderer.draw_status(
                frame,
                f"{gesture_name} ({confidence:.2f})",
                y_offset=20
            )

        if self.info_message and time.time() < self.info_message_until:
            self.ui_renderer.draw_status(
                frame,
                self.info_message,
                y_offset=50,
                color=(255, 255, 0)
            )
        
        fps = self.performance.update_fps()
        cv2.putText(frame, f"FPS: {fps}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)



        # === AI Gesture Recognition ===

        return frame

    def handle_mouse(self, event, x, y, flags, param):
        # Mouse clicks disabled - only pinch gestures trigger buttons
        pass

    def _apply_button_action(self, button, record_click=True):
        if record_click:
            self.last_toolbar_button_click = button
            if self.is_recording_action:
                self.recorded_action_clicks.append(button)
        # Centralized button action handler used by pinch gestures
        if button.startswith("Brush:"):
            # Cycle to next brush type
            self.current_brush_index = (self.current_brush_index + 1) % len(self.brush_types)
            new_brush = self.brush_types[self.current_brush_index]
            self.stroke_engine.brush.set_brush(new_brush)
            self.toolbar.update_brush_label(new_brush)

        elif button == "Eraser":
            self.stroke_engine.brush.set_brush("eraser")

        elif button == "Undo":
            self.layer_manager.get_active_layer().undo()

        elif button == "Redo":
            self.layer_manager.get_active_layer().redo()

        elif button == "-Size":
            current_size = self.stroke_engine.brush.base_size
            self.stroke_engine.brush.set_size(max(2, current_size - 2))

        elif button == "+Size":
            current_size = self.stroke_engine.brush.base_size
            self.stroke_engine.brush.set_size(min(30, current_size + 2))

        elif button.startswith("EXPORT_"):
            export_format = button.split("_")[1]
            self._export_canvas(export_format)

    def _export_canvas(self, export_format):
        """Export the canvas in the specified format"""
        try:
            canvas = self.layer_manager.composite()
            filepath = self.export_manager.export(canvas, export_format)
            print(f"Canvas exported to: {filepath}")
            self._set_info_message(f"Exported {export_format}: {filepath}")
        except Exception as e:
            print(f"Error exporting canvas: {e}")
            self._set_info_message(f"Export failed: {export_format}")

    def handle_key(self, key):
        ui_payload = self.gesture_ui.handle_key(key)
        if ui_payload:
            action, _ = ui_payload
            if action == "refresh":
                return

        key_char = chr(key).lower() if 0 <= key <= 255 else ""
        if key_char == "c":
            self.create_custom_gesture()

    def create_custom_gesture(self, name=None):
        if not self.latest_hand_landmarks:
            self._set_info_message("No hand detected for custom gesture")
            return

        gesture_name = self.gesture_controller.create_custom_gesture(
            self.latest_hand_landmarks,
            self.width,
            self.height,
            name=name
        )
        if not gesture_name:
            self._set_info_message("Failed to create custom gesture")
            return

        if self.gesture_controller.get_gesture_action(gesture_name) is None:
            self.gesture_controller.set_gesture_action(gesture_name, "DRAW")

        self._set_info_message(f"Saved {gesture_name} -> DRAW")
        self.gesture_ui.gesture_name_input = ""

    def cycle_current_gesture_mapping(self):
        if not self.current_gesture_name:
            self._set_info_message("No active gesture to map")
            return

        self.cycle_gesture_mapping(self.current_gesture_name)

    def cycle_gesture_mapping(self, gesture_name):
        new_action = self.gesture_controller.cycle_gesture_action(gesture_name)
        action_label = "None" if new_action is None else new_action
        self._set_info_message(f"{gesture_name} -> {action_label}")

    def _set_info_message(self, message, duration=2.5):
        self.info_message = message
        self.info_message_until = time.time() + duration

    def get_gesture_ui_frame(self):
        mapping = self.gesture_controller.profile_manager.get_all()
        valid_actions = self.gesture_controller.profile_manager.get_valid_actions()
        info = self.info_message if time.time() < self.info_message_until else None
        confidence = self.current_gesture_confidence if self.current_gesture_confidence is not None else 0.0
        custom_gesture_names = self.gesture_controller.get_custom_gesture_names()
        return self.gesture_ui.draw(
            self.current_gesture_name,
            confidence,
            mapping,
            valid_actions,
            self.last_toolbar_button_click,
            self.is_recording_action,
            self.recorded_action_clicks,
            custom_gesture_names,
            self.custom_actions,
            info_message=info
        )

    def handle_gesture_ui_mouse(self, event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        payload = self.gesture_ui.detect_click(x, y)
        if not payload:
            return

        action, value = payload
        if action == "create_custom":
            self.create_custom_gesture()
        elif action == "create_custom_named":
            requested_name = self.gesture_ui.gesture_name_input.strip()
            self.create_custom_gesture(name=requested_name or None)
        elif action == "delete_current_gesture":
            if not self.current_gesture_name:
                self._set_info_message("No active gesture to delete")
            else:
                self.delete_custom_gesture(self.current_gesture_name)
        elif action == "delete_custom_gesture" and value:
            self.delete_custom_gesture(value)
        elif action == "create_action_from_last_click":
            self.create_action_from_last_click()
        elif action == "toggle_action_recording":
            self.toggle_action_recording()
        elif action == "save_recorded_action":
            requested_name = self.gesture_ui.action_name_input.strip()
            self.save_recorded_action(name=requested_name or None)
        elif action == "delete_custom_action" and value:
            self.delete_custom_action(value)
        elif action == "set_named_action" and value:
            gesture_name, action_name = value
            self.gesture_controller.set_gesture_action(gesture_name, action_name)
            label = "None" if action_name is None else action_name
            self._set_info_message(f"{gesture_name} -> {label}")

    def create_action_from_last_click(self, name=None):
        if not self.last_toolbar_button_click:
            self._set_info_message("No toolbar click captured yet")
            return

        action_name = name or self._generate_custom_action_name()
        self.custom_actions[action_name] = [self.last_toolbar_button_click]
        self._save_custom_actions()
        self.gesture_controller.profile_manager.set_custom_actions(list(self.custom_actions.keys()))
        self._set_info_message(f"Created {action_name} -> {self.last_toolbar_button_click}")

    def toggle_action_recording(self):
        self.is_recording_action = not self.is_recording_action
        if self.is_recording_action:
            self.recorded_action_clicks = []
            self._set_info_message("Recording toolbar clicks...")
        else:
            count = len(self.recorded_action_clicks)
            self._set_info_message(f"Recording stopped ({count} clicks)")

    def save_recorded_action(self, name=None):
        if not self.recorded_action_clicks:
            self._set_info_message("No recorded clicks to save")
            return

        action_name = name or self._generate_custom_action_name()
        action_name = self._resolve_unique_action_name(action_name)
        self.custom_actions[action_name] = list(self.recorded_action_clicks)
        self._save_custom_actions()
        self.gesture_controller.profile_manager.set_custom_actions(list(self.custom_actions.keys()))
        self.gesture_ui.action_name_input = ""
        self._set_info_message(f"Saved action {action_name} ({len(self.recorded_action_clicks)} clicks)")

    def delete_custom_action(self, action_name):
        if action_name not in self.custom_actions:
            self._set_info_message(f"Action not found: {action_name}")
            return
        del self.custom_actions[action_name]
        self._save_custom_actions()
        self.gesture_controller.profile_manager.set_custom_actions(list(self.custom_actions.keys()))
        self.gesture_controller.profile_manager.clear_action_references(action_name)
        self._set_info_message(f"Deleted action: {action_name}")

    def delete_custom_gesture(self, gesture_name):
        deleted = self.gesture_controller.delete_custom_gesture(gesture_name)
        if deleted:
            self._set_info_message(f"Deleted gesture: {gesture_name}")
        else:
            self._set_info_message(f"Gesture not found: {gesture_name}")

    def _generate_custom_action_name(self):
        index = 1
        while f"USER_ACTION_{index}" in self.custom_actions:
            index += 1
        return f"USER_ACTION_{index}"

    def _resolve_unique_action_name(self, requested_name):
        cleaned = requested_name.strip()
        if not cleaned:
            return self._generate_custom_action_name()
        if cleaned not in self.custom_actions:
            return cleaned
        suffix = 2
        while f"{cleaned}_{suffix}" in self.custom_actions:
            suffix += 1
        return f"{cleaned}_{suffix}"

    def _load_custom_actions(self):
        if os.path.exists(self.custom_actions_path):
            with open(self.custom_actions_path, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    normalized = {}
                    for key, value in data.items():
                        if isinstance(value, list):
                            normalized[key] = [str(v) for v in value]
                        elif isinstance(value, str):
                            normalized[key] = [value]
                    return normalized
        self._save_custom_actions({})
        return {}

    def _save_custom_actions(self, data=None):
        to_write = self.custom_actions if data is None else data
        with open(self.custom_actions_path, "w") as f:
            json.dump(to_write, f, indent=4)
