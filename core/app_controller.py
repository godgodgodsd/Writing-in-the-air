import cv2
import time
import json
import os
import numpy as np

from ai.hand_tracker import HandTracker
from ai.gesture_controller import GestureController

from engine.layer_manager import LayerManager
from engine.stroke_engine import StrokeEngine

from ui.toolbar import Toolbar
from ui.ui_renderer import UIRenderer
from ui.gesture_management_ui import GestureManagementUI

from core.performance_manager import PerformanceManager
from core.export_manager import ExportManager
from core.logger import AppLogger
from core.session_manager import SessionManager
from core.plugin_system import PluginSystem




class AppController:

    def __init__(self, width, height):
        self.app_logger = AppLogger()
        self.logger = self.app_logger.get_logger()
        self.logger.info("AppController initialized")
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
        self.logger.info("Loaded custom actions: %s", list(self.custom_actions.keys()))

        self.export_manager = ExportManager()
        self.session_manager = SessionManager()
        self.plugin_system = PluginSystem()
        self.logger.info("Plugins loaded: %s", len(self.plugin_system.plugins))

        self.performance = PerformanceManager(
            self.gesture_controller,
            self.hand_tracker,
            ai_width=256,
            ai_height=192,
            skip_rate=2
        )
        # Finger click (pinch) state
        self.finger_clicking = False
        self.finger_click_threshold = 60    # threshold to register pinch in pixels
        self.last_pinch_button = None       # track which button is being held
        self.last_size_adjust_time = 0      # throttle size adjustments
        
        # Brush cycling
        self.base_brush_types = ["round", "square", "spray"]
        self.brush_types = list(self.base_brush_types)
        self.current_brush_index = 0
        self.current_color_name = "Red"
        self.color_map = {
            "RED": (0, 0, 255),
            "GREEN": (0, 255, 0),
            "BLUE": (255, 0, 0),
            "YELLOW": (0, 255, 255),
            "WHITE": (255, 255, 255),
            "BLACK": (0, 0, 0),
        }
        self.stroke_engine.brush.set_brush(self.brush_types[self.current_brush_index])
        self.stroke_engine.brush.set_color(self.color_map[self.current_color_name.upper()])
        self.toolbar.update_brush_label(self._format_brush_label(self.brush_types[self.current_brush_index]))
        self.toolbar.update_color_label(self.current_color_name)
        self.logger.info("Brushes loaded: base=%s", self.base_brush_types)

    def process_frame(self, frame):
        now = time.time()
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
        # Map the recognized gesture to drawing actions.
        if action == "DRAW":
            if not self.stroke_engine.drawing:
                self.stroke_engine.start_stroke()
                self.logger.info("Action: DRAW start")

        elif action == "STOP":
            self.stroke_engine.end_stroke()
            self.logger.info("Action: STOP")

        elif action == "CLEAR":
            current_brush = self.stroke_engine.brush.brush_type
            current_size = self.stroke_engine.brush.base_size
            self.layer_manager = LayerManager(self.width, self.height)
            self.stroke_engine = StrokeEngine(self.layer_manager)
            if current_brush in self.brush_types or current_brush == "eraser":
                self.stroke_engine.brush.set_brush(current_brush)
            else:
                self.current_brush_index = 0
                self.stroke_engine.brush.set_brush(self.brush_types[self.current_brush_index])
            self.stroke_engine.brush.set_size(current_size)
            self.logger.info("Action: CLEAR")

        elif action == "ERASE":
            # Switch to eraser brush; start stroke if not already erasing
            self.stroke_engine.brush.set_brush("eraser")
            if not self.stroke_engine.drawing:
                self.stroke_engine.start_stroke()
            self.logger.info("Action: ERASE")

        elif action == "UNDO":
            self.layer_manager.get_active_layer().undo()
            self.layer_manager.dirty = True
            self.logger.info("Action: UNDO")

        elif action == "REDO":
            self.layer_manager.get_active_layer().redo()
            self.layer_manager.dirty = True
            self.logger.info("Action: REDO")

        elif action == "BUTTON_CLICK":
            pass
        elif action in self.custom_actions:
            for mapped_button in self.custom_actions[action]:
                self._apply_button_action(mapped_button, record_click=False)
            self.logger.info("Custom action executed: %s", action)

        if gesture_name:
            self.plugin_system.execute(
                "on_gesture",
                {
                    "gesture": gesture_name,
                    "confidence": confidence,
                    "action": action,
                },
            )

        # === Drawing Update ===
        # Use the index finger point to update the active stroke.
        if index_point:
            self.stroke_engine.update(index_point, pinch_distance)

        # === Composite Layers ===
        # Merge layers into a single canvas for display.
        canvas = self.layer_manager.composite()

        # === Overlay Canvas on Frame (blend only painted region) ===
        # Blend only pixels that were drawn to avoid dimming the whole frame.
        if self.layer_manager.content_bbox is not None:
            x1, y1, x2, y2 = self.layer_manager.content_bbox
            roi_frame = frame[y1:y2, x1:x2]
            roi_canvas = canvas[y1:y2, x1:x2]
            roi_alpha = self.layer_manager.alpha_cache[y1:y2, x1:x2]
            mask = roi_alpha > 0
            if np.any(mask):
                blended = (
                    (roi_frame[mask].astype(np.float32) * 0.4) +
                    (roi_canvas[mask].astype(np.float32) * 0.6)
                ).astype(np.uint8)
                roi_frame[mask] = blended

        # === Draw Toolbar ===
        # Render the UI overlay.
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
        # Treat a pinch as a click on the toolbar buttons.
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
                    self.logger.info("Pinch toolbar click: %s", button)

            elif self.finger_clicking and pinch_distance < self.finger_click_threshold:
                # Pinch held -> continuously adjust size if size button
                if self.last_pinch_button in ("+Size", "-Size"):
                    current_time = now
                    # Throttle to ~10 times per second (100ms per adjustment)
                    if current_time - self.last_size_adjust_time > 0.1:
                        self._apply_button_action(self.last_pinch_button)
                        self.last_size_adjust_time = current_time

            elif pinch_distance >= self.finger_click_threshold:
                # Pinch released
                self.finger_clicking = False
                self.last_pinch_button = None

        # === Status ===
        # Draw gesture confidence and current tool text.
        if gesture_name:
            gesture_label = f"{gesture_name}" if confidence is None else f"{gesture_name} ({confidence:.2f})"
            self.ui_renderer.draw_status(
                frame,
                gesture_label,
                y_offset=18,
                scale=0.55,
                thickness=1
            )
            self.ui_renderer.draw_status(
                frame,
                self._get_tool_label(),
                y_offset=36,
                color=(200, 255, 200),
                scale=0.55,
                thickness=1
            )

        if self.info_message and now < self.info_message_until:
            self.ui_renderer.draw_status(
                frame,
                self.info_message,
                y_offset=50,
                color=(255, 255, 0),
                scale=0.55,
                thickness=1
            )
        
        fps = self.performance.update_fps()
        cv2.putText(frame, f"FPS: {fps}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)



        # === AI Gesture Recognition ===

        self.plugin_system.execute(
            "on_frame",
            {
                "frame": frame,
                "gesture": gesture_name,
                "confidence": confidence,
                "action": action,
            },
        )
        return frame

    def shutdown(self):
        self.performance.stop()
        self.logger.info("AppController shutdown")

    def handle_mouse(self, event, x, y, flags, param):
        # Allow mouse clicks for toolbar when recording custom actions.
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if not self.is_recording_action:
            return
        button = self.toolbar.detect_click(x, y)
        if button:
            self._apply_button_action(button, record_click=True)
            self.logger.info("Mouse toolbar click recorded: %s", button)

    def _apply_button_action(self, button, record_click=True):
        if record_click:
            self.last_toolbar_button_click = button
            if self.is_recording_action:
                self.recorded_action_clicks.append(button)
                self.logger.info("Recorded toolbar click: %s", button)
        # Centralized button action handler used by pinch and mouse clicks.
        if button.startswith("Brush:"):
            # Cycle to next brush type
            self.current_brush_index = (self.current_brush_index + 1) % len(self.brush_types)
            new_brush = self.brush_types[self.current_brush_index]
            self.stroke_engine.brush.set_brush(new_brush)
            self.toolbar.update_brush_label(self._format_brush_label(new_brush))
            self.logger.info("Brush changed: %s", new_brush)

        elif button == "Eraser":
            self.stroke_engine.brush.set_brush("eraser")
            self.logger.info("Brush changed: eraser")

        elif button == "Undo":
            self.layer_manager.get_active_layer().undo()
            self.layer_manager.dirty = True
            self.logger.info("Toolbar: UNDO")

        elif button == "Redo":
            self.layer_manager.get_active_layer().redo()
            self.layer_manager.dirty = True
            self.logger.info("Toolbar: REDO")

        elif button == "-Size":
            current_size = self.stroke_engine.brush.base_size
            self.stroke_engine.brush.set_size(max(2, current_size - 2))
            self.logger.info("Brush size decreased: %s", self.stroke_engine.brush.base_size)

        elif button == "+Size":
            current_size = self.stroke_engine.brush.base_size
            self.stroke_engine.brush.set_size(min(30, current_size + 2))
            self.logger.info("Brush size increased: %s", self.stroke_engine.brush.base_size)

        elif button.startswith("EXPORT_"):
            export_format = button.split("_")[1]
            self._export_canvas(export_format)
        elif button.startswith("COLOR_"):
            color_key = button.split("_", 1)[1]
            color_value = self.color_map.get(color_key)
            if color_value is None:
                return
            self.current_color_name = color_key.capitalize()
            self.stroke_engine.brush.set_color(color_value)
            self.toolbar.update_color_label(self.current_color_name)
            self.logger.info("Color changed: %s", self.current_color_name)

    def _export_canvas(self, export_format):
        """Export the canvas in the specified format"""
        try:
            canvas = self.layer_manager.composite()
            filepath = self.export_manager.export(canvas, export_format)
            print(f"Canvas exported to: {filepath}")
            self._set_info_message(f"Exported {export_format}: {filepath}")
            self.logger.info("Exported canvas: %s", filepath)
            self.plugin_system.execute(
                "on_export",
                {"format": export_format, "path": filepath},
            )
        except Exception as e:
            print(f"Error exporting canvas: {e}")
            self._set_info_message(f"Export failed: {export_format}")
            self.logger.exception("Export failed: %s", export_format)

    def handle_key(self, key):
        ui_payload = self.gesture_ui.handle_key(key)
        if ui_payload:
            action, _ = ui_payload
            if action == "refresh":
                return

        key_char = chr(key).lower() if 0 <= key <= 255 else ""
        if key_char == "c":
            self.create_custom_gesture()
        elif key_char == "s":
            self._save_session()
        elif key_char == "l":
            self._load_session()
        elif key_char == "x":
            self._clear_logs()

    def create_custom_gesture(self, name=None):
        if not self.latest_hand_landmarks:
            self._set_info_message("No hand detected for custom gesture")
            self.logger.warning("Custom gesture creation failed: no hand detected")
            return

        gesture_name = self.gesture_controller.create_custom_gesture(
            self.latest_hand_landmarks,
            self.width,
            self.height,
            name=name
        )
        if not gesture_name:
            self._set_info_message("Failed to create custom gesture")
            self.logger.error("Custom gesture creation failed")
            return

        if self.gesture_controller.get_gesture_action(gesture_name) is None:
            self.gesture_controller.set_gesture_action(gesture_name, "DRAW")

        self._set_info_message(f"Saved {gesture_name} -> DRAW")
        self.gesture_ui.gesture_name_input = ""
        self.logger.info("Custom gesture created: %s", gesture_name)

    def _save_session(self):
        self.session_manager.save_session(self.layer_manager)
        self._set_info_message("Session saved")
        self.logger.info("Session saved")

    def _load_session(self):
        loaded = self.session_manager.load_session(self.layer_manager)
        if loaded:
            self._set_info_message("Session loaded")
            self.logger.info("Session loaded")
        else:
            self._set_info_message("No session found")
            self.logger.warning("Session load failed: no session found")

    def _clear_logs(self):
        self.app_logger.clear_logs()
        self._set_info_message("Logs cleared")
        self.logger.info("Logs cleared")

    def cycle_current_gesture_mapping(self):
        if not self.current_gesture_name:
            self._set_info_message("No active gesture to map")
            return

        self.cycle_gesture_mapping(self.current_gesture_name)

    def cycle_gesture_mapping(self, gesture_name):
        new_action = self.gesture_controller.cycle_gesture_action(gesture_name)
        action_label = "None" if new_action is None else new_action
        self._set_info_message(f"{gesture_name} -> {action_label}")
        self.logger.info("Gesture mapping cycled: %s -> %s", gesture_name, action_label)

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
            self.logger.info("Gesture mapping set: %s -> %s", gesture_name, label)

    def create_action_from_last_click(self, name=None):
        if not self.last_toolbar_button_click:
            self._set_info_message("No toolbar click captured yet")
            self.logger.warning("Create action failed: no toolbar click captured")
            return

        action_name = name or self._generate_custom_action_name()
        self.custom_actions[action_name] = [self.last_toolbar_button_click]
        self._save_custom_actions()
        self.gesture_controller.profile_manager.set_custom_actions(list(self.custom_actions.keys()))
        self._set_info_message(f"Created {action_name} -> {self.last_toolbar_button_click}")
        self.logger.info("Custom action created: %s -> %s", action_name, self.last_toolbar_button_click)

    def toggle_action_recording(self):
        self.is_recording_action = not self.is_recording_action
        if self.is_recording_action:
            self.recorded_action_clicks = []
            self._set_info_message("Recording toolbar clicks...")
            self.logger.info("Action recording started")
        else:
            count = len(self.recorded_action_clicks)
            self._set_info_message(f"Recording stopped ({count} clicks)")
            self.logger.info("Action recording stopped: %s clicks", count)

    def save_recorded_action(self, name=None):
        if not self.recorded_action_clicks:
            self._set_info_message("No recorded clicks to save")
            self.logger.warning("Save action failed: no recorded clicks")
            return

        action_name = name or self._generate_custom_action_name()
        action_name = self._resolve_unique_action_name(action_name)
        self.custom_actions[action_name] = list(self.recorded_action_clicks)
        self._save_custom_actions()
        self.gesture_controller.profile_manager.set_custom_actions(list(self.custom_actions.keys()))
        self.gesture_ui.action_name_input = ""
        self._set_info_message(f"Saved action {action_name} ({len(self.recorded_action_clicks)} clicks)")
        self.logger.info("Custom action saved: %s (%s clicks)", action_name, len(self.recorded_action_clicks))

    def delete_custom_action(self, action_name):
        if action_name not in self.custom_actions:
            self._set_info_message(f"Action not found: {action_name}")
            self.logger.warning("Delete action failed: not found %s", action_name)
            return
        del self.custom_actions[action_name]
        self._save_custom_actions()
        self.gesture_controller.profile_manager.set_custom_actions(list(self.custom_actions.keys()))
        self.gesture_controller.profile_manager.clear_action_references(action_name)
        self._set_info_message(f"Deleted action: {action_name}")
        self.logger.info("Custom action deleted: %s", action_name)

    def delete_custom_gesture(self, gesture_name):
        deleted = self.gesture_controller.delete_custom_gesture(gesture_name)
        if deleted:
            self._set_info_message(f"Deleted gesture: {gesture_name}")
            self.logger.info("Custom gesture deleted: %s", gesture_name)
        else:
            self._set_info_message(f"Gesture not found: {gesture_name}")
            self.logger.warning("Delete gesture failed: not found %s", gesture_name)

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

    def _format_brush_label(self, brush_name):
        return brush_name.capitalize()

    def _get_tool_label(self):
        brush = self.stroke_engine.brush.brush_type
        if brush == "eraser":
            return "Tool: Eraser"
        return f"Tool: Brush ({self._format_brush_label(brush)})"
