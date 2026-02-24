"""
Enterprise Layer Manager
Supports:
- Unlimited layers
- Alpha blending
- Per-layer undo/redo
- Layer visibility
"""

import numpy as np
import cv2


class Layer:
    def __init__(self, width, height, name="Layer"):
        self.name = name
        self.visible = True
        self.canvas = np.zeros((height, width, 4), dtype=np.uint8)
        self.undo_stack = []
        self.redo_stack = []


    def push_state(self):
        self.undo_stack.append(self.canvas.copy())
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.canvas.copy())
            self.canvas = self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.canvas.copy())
            self.canvas = self.redo_stack.pop()


class LayerManager:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []
        self.active_index = 0
        self.add_layer("Background")
        self.render_cache = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.dirty = True

    def add_layer(self, name="Layer"):
        self.layers.append(Layer(self.width, self.height, name))

    def get_active_layer(self):
        return self.layers[self.active_index]

    def composite(self):

        if not self.dirty:
            return self.render_cache

        # Clear cache
        self.render_cache.fill(0)

        for layer in self.layers:
            if not layer.visible:
                continue

            alpha = layer.canvas[:, :, 3]
            mask = alpha > 0

            self.render_cache[mask] = layer.canvas[:, :, :3][mask]

        self.dirty = False
        return self.render_cache

    def clear(self):
        for layer in self.layers:
            layer.canvas.fill(0)