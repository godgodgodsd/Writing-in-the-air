"""
Brush Engine
Supports:
- Round brush
- Square brush
- Spray brush
- Eraser

"""

import cv2
import random


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

        if self.brush_type == "round":
            cv2.circle(canvas, point, size, (*self.color, 255), -1)

        elif self.brush_type == "square":
            x, y = point
            cv2.rectangle(
                canvas,
                (x-size, y-size),
                (x+size, y+size),
                (*self.color, 255),
                -1
            )

        elif self.brush_type == "spray":
            for _ in range(size * 3):
                offset_x = random.randint(-size, size)
                offset_y = random.randint(-size, size)
                cv2.circle(
                    canvas,
                    (point[0] + offset_x, point[1] + offset_y),
                    1,
                    (*self.color, 255),
                    -1
                )

        elif self.brush_type == "eraser":
            cv2.circle(canvas, point, size, (0, 0, 0, 0), -1)
