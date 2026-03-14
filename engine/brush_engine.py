"""
Brush Engine
Supports:
- Round brush
- Square brush
- Spray brush
- Eraser

"""

import cv2
import numpy as np


class BrushEngine:

    def __init__(self):
        self.brush_type = "round"
        self.color = (0, 0, 255)
        self.base_size = 8

    def set_brush(self, brush_type):
        self.brush_type = brush_type

    def set_color(self, color):
        self.color = color

    def set_size(self, size):
        self.base_size = size

    def draw(self, canvas, point, velocity):
        size = self.base_size
        color = (*self.color, 255)

        if self.brush_type == "round":
            cv2.circle(canvas, point, size, color, -1)

        elif self.brush_type == "square":
            # Draw a filled square brush.
            x, y = point
            cv2.rectangle(
                canvas,
                (x-size, y-size),
                (x+size, y+size),
                color,
                -1
            )

        elif self.brush_type == "spray":
            count = max(1, size * 3)
            offsets = np.random.randint(-size, size + 1, size=(count, 2), dtype=np.int32)
            points = offsets + np.array([point[0], point[1]], dtype=np.int32)

            h, w = canvas.shape[:2]
            valid = (
                (points[:, 0] >= 0) & (points[:, 0] < w) &
                (points[:, 1] >= 0) & (points[:, 1] < h)
            )
            valid_points = points[valid]
            if valid_points.size:
                canvas[valid_points[:, 1], valid_points[:, 0]] = color

        elif self.brush_type == "eraser":
            cv2.circle(canvas, point, size, (0, 0, 0, 0), -1)

        else:
            # Fallback to round brush for unknown brush ids.
            cv2.circle(canvas, point, size, color, -1)
