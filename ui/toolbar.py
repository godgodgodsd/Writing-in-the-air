import cv2
import numpy as np


class Toolbar:

    def __init__(self, width):
        self.height = 60
        self.width = width

        self.buttons = [
            {"label": "Brush: Round", "x": 5, "w": 100, "id": "brush_toggle"},
            {"label": "Eraser", "x": 110, "w": 70},
            {"label": "Undo", "x": 185, "w": 65},
            {"label": "Redo", "x": 255, "w": 65},
            {"label": "-Size", "x": 325, "w": 55},
            {"label": "+Size", "x": 385, "w": 55},
            {"label": "Color: Red", "x": 445, "w": 70, "id": "color_btn"},
            {"label": "Export", "x": 520, "w": 70, "id": "export_btn"},
        ]
        
        # Dropdown menus
        self.export_formats = ["PNG", "JPEG", "PDF"]
        self.color_options = ["Red", "Green", "Blue", "Yellow", "White", "Black"]
        self.dropdown_mode = None
        self.dropdown_y = 60  # Start below toolbar
        self.dropdown_height = 28
        self.export_dropdown_width = 70
        self.color_dropdown_width = 90
        self._base_cache = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self._cache_dirty = True
    
    def update_brush_label(self, brush_type):
        """Update the brush toggle button label"""
        for btn in self.buttons:
            if btn.get("id") == "brush_toggle":
                btn["label"] = f"Brush: {brush_type.capitalize()}"
                self._cache_dirty = True
    
    def update_color_label(self, color_name):
        for btn in self.buttons:
            if btn.get("id") == "color_btn":
                btn["label"] = f"Color: {color_name}"
                self._cache_dirty = True

    def draw(self, frame):
        if self._cache_dirty:
            self._redraw_base_cache()
        frame[0:self.height, 0:self.width] = self._base_cache
        
        # Draw dropdown menu if visible
        if self.dropdown_mode == "export":
            self._draw_dropdown(frame, "export")
        elif self.dropdown_mode == "color":
            self._draw_dropdown(frame, "color")

    def _redraw_base_cache(self):
        self._base_cache.fill(0)
        cv2.rectangle(self._base_cache, (0, 0), (self.width, self.height), (40, 40, 40), -1)

        for btn in self.buttons:
            cv2.rectangle(
                self._base_cache,
                (btn["x"], 10),
                (btn["x"] + btn["w"], 50),
                (70, 70, 70),
                -1
            )

            cv2.putText(
                self._base_cache,
                btn["label"],
                (btn["x"] + 5, 36),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (255, 255, 255),
                1
            )
        self._cache_dirty = False

    def detect_click(self, x, y):
        # Check dropdown menu first
        if self.dropdown_mode:
            dropdown_result = self._detect_dropdown_click(x, y, self.dropdown_mode)
            if dropdown_result:
                self.dropdown_mode = None
                return dropdown_result
            # If clicked elsewhere, close dropdown
            self.dropdown_mode = None
        
        # Only consider clicks within the toolbar vertical bounds
        if y < 0 or y > self.height:
            return None

        # Buttons are drawn from y=10..50; ensure click is within button vertical range
        if y < 10 or y > 50:
            return None

        for btn in self.buttons:
            if btn["x"] < x < btn["x"] + btn["w"]:
                # If Export button clicked, toggle dropdown
                if btn.get("id") == "export_btn":
                    self.dropdown_mode = "export"
                    return None
                if btn.get("id") == "color_btn":
                    self.dropdown_mode = "color"
                    return None
                return btn["label"]

        return None
    
    def _draw_dropdown(self, frame, mode):
        if mode == "export":
            btn = next((btn for btn in self.buttons if btn.get("id") == "export_btn"), None)
            options = self.export_formats
            width = self.export_dropdown_width
        else:
            btn = next((btn for btn in self.buttons if btn.get("id") == "color_btn"), None)
            options = self.color_options
            width = self.color_dropdown_width

        if not btn:
            return

        start_x = btn["x"]
        start_y = self.dropdown_y

        for i, option_name in enumerate(options):
            y = start_y + (i * self.dropdown_height)
            cv2.rectangle(
                frame,
                (start_x, y),
                (start_x + width, y + self.dropdown_height),
                (100, 100, 100),
                -1
            )
            cv2.rectangle(
                frame,
                (start_x, y),
                (start_x + width, y + self.dropdown_height),
                (150, 150, 150),
                1
            )
            cv2.putText(
                frame,
                option_name,
                (start_x + 5, y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
    
    def _detect_dropdown_click(self, x, y, mode):
        if mode == "export":
            btn = next((btn for btn in self.buttons if btn.get("id") == "export_btn"), None)
            options = self.export_formats
            width = self.export_dropdown_width
            prefix = "EXPORT_"
        else:
            btn = next((btn for btn in self.buttons if btn.get("id") == "color_btn"), None)
            options = self.color_options
            width = self.color_dropdown_width
            prefix = "COLOR_"

        if not btn:
            return None

        start_x = btn["x"]
        start_y = self.dropdown_y

        for i, option_name in enumerate(options):
            item_y = start_y + (i * self.dropdown_height)
            if (start_x <= x <= start_x + width and
                item_y <= y <= item_y + self.dropdown_height):
                return f"{prefix}{option_name.upper()}"

        return None
