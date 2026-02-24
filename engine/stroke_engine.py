"""
Stroke Engine
Handles:
- Stroke lifecycle
- Pressure from pinch
- Velocity thickness
- Undo checkpoints
"""

from engine.smoothing import StrokeSmoother
from engine.brush_engine import BrushEngine


class StrokeEngine:

    def __init__(self, layer_manager):
        self.layer_manager = layer_manager
        self.smoother = StrokeSmoother()
        self.brush = BrushEngine()
        self.drawing = False

    def start_stroke(self):
        self.layer_manager.get_active_layer().push_state()
        self.smoother.reset()
        self.drawing = True

    def end_stroke(self):
        self.drawing = False

    def update(self, point, pinch_distance=None):

        if not self.drawing:
            return

        smoothed, velocity = self.smoother.smooth(point)
        if smoothed is None:
            return

        active_layer = self.layer_manager.get_active_layer()

        self.brush.draw(
            active_layer.canvas,
            smoothed,
            velocity
        )
        self.layer_manager.dirty = True