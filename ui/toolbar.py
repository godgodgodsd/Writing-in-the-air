import cv2


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
            {"label": "Export", "x": 445, "w": 70, "id": "export_btn"},
        ]
        
        # Dropdown menu for export
        self.export_formats = ["PNG", "JPEG", "PDF"]
        self.dropdown_visible = False
        self.dropdown_y = 60  # Start below toolbar
        self.dropdown_height = 28
        self.dropdown_width = 70
    
    def update_brush_label(self, brush_type):
        """Update the brush toggle button label"""
        for btn in self.buttons:
            if btn.get("id") == "brush_toggle":
                btn["label"] = f"Brush: {brush_type.capitalize()}"

    def draw(self, frame):
        cv2.rectangle(frame, (0, 0), (self.width, self.height), (40, 40, 40), -1)

        for btn in self.buttons:
            cv2.rectangle(
                frame,
                (btn["x"], 10),
                (btn["x"] + btn["w"], 50),
                (70, 70, 70),
                -1
            )

            cv2.putText(
                frame,
                btn["label"],
                (btn["x"] + 5, 36),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (255, 255, 255),
                1
            )
        
        # Draw dropdown menu if visible
        if self.dropdown_visible:
            self._draw_dropdown(frame)

    def detect_click(self, x, y):
        # Check dropdown menu first
        if self.dropdown_visible:
            dropdown_result = self._detect_dropdown_click(x, y)
            if dropdown_result:
                self.dropdown_visible = False
                return dropdown_result
            # If clicked elsewhere, close dropdown
            self.dropdown_visible = False
        
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
                    self.dropdown_visible = True
                    return None
                return btn["label"]

        return None
    
    def _draw_dropdown(self, frame):
        """Draw the export format dropdown menu"""
        export_btn = next((btn for btn in self.buttons if btn.get("id") == "export_btn"), None)
        if not export_btn:
            return
        
        start_x = export_btn["x"]
        start_y = self.dropdown_y
        
        for i, format_name in enumerate(self.export_formats):
            y = start_y + (i * self.dropdown_height)
            # Draw background
            cv2.rectangle(
                frame,
                (start_x, y),
                (start_x + self.dropdown_width, y + self.dropdown_height),
                (100, 100, 100),
                -1
            )
            # Draw border
            cv2.rectangle(
                frame,
                (start_x, y),
                (start_x + self.dropdown_width, y + self.dropdown_height),
                (150, 150, 150),
                1
            )
            # Draw text
            cv2.putText(
                frame,
                format_name,
                (start_x + 5, y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
    
    def _detect_dropdown_click(self, x, y):
        """Detect clicks on dropdown menu items"""
        export_btn = next((btn for btn in self.buttons if btn.get("id") == "export_btn"), None)
        if not export_btn:
            return None
        
        start_x = export_btn["x"]
        start_y = self.dropdown_y
        
        for i, format_name in enumerate(self.export_formats):
            item_y = start_y + (i * self.dropdown_height)
            if (start_x <= x <= start_x + self.dropdown_width and
                item_y <= y <= item_y + self.dropdown_height):
                return f"EXPORT_{format_name.upper()}"
        
        return None
