import cv2
import time

from ai.hand_tracker import HandTracker
from ai.gesture_controller import GestureController

from engine.layer_manager import LayerManager
from engine.stroke_engine import StrokeEngine

from ui.toolbar import Toolbar
from ui.ui_renderer import UIRenderer

from core.performance_manager import PerformanceManager
from core.session_manager import SessionManager
from core.plugin_system import PluginSystem
from core.logger import AppLogger
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

        # State
        self.current_action = None

        self.logger = AppLogger()
        self.session_manager = SessionManager()
        self.plugins = PluginSystem()
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
                f"{gesture_name} ({confidence:.2f})"
            )
        
        fps = self.performance.update_fps()
        cv2.putText(frame, f"FPS: {fps}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)



        # === AI Gesture Recognition ===

        return frame

    def handle_mouse(self, event, x, y, flags, param):
        # Mouse clicks disabled - only pinch gestures trigger buttons
        pass

    def _apply_button_action(self, button):
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
        except Exception as e:
            print(f"Error exporting canvas: {e}")