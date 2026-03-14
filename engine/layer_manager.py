"""
Enterprise Layer Manager
Supports:
- Unlimited layers
- Alpha blending
- Per-layer undo/redo
- Layer visibility
"""

import numpy as np


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
        self.alpha_cache = np.zeros((self.height, self.width), dtype=np.uint8)
        self.dirty = True
        self.content_bbox = None

    def add_layer(self, name="Layer"):
        self.layers.append(Layer(self.width, self.height, name))
        self.dirty = True

    def get_active_layer(self):
        return self.layers[self.active_index]

    def composite(self):

        if not self.dirty:
            return self.render_cache

        # Clear cache before rebuilding the composite.
        self.render_cache.fill(0)
        self.alpha_cache.fill(0)
        x_min = None
        y_min = None
        x_max = None
        y_max = None

        for layer in self.layers:
            if not layer.visible:
                continue

            # Use alpha to decide which pixels are visible.
            alpha = layer.canvas[:, :, 3]
            mask = alpha > 0

            self.render_cache[mask] = layer.canvas[:, :, :3][mask]
            self.alpha_cache[mask] = alpha[mask]
            if np.any(mask):
                ys, xs = np.where(mask)
                lx_min = int(xs.min())
                lx_max = int(xs.max()) + 1
                ly_min = int(ys.min())
                ly_max = int(ys.max()) + 1

                x_min = lx_min if x_min is None else min(x_min, lx_min)
                y_min = ly_min if y_min is None else min(y_min, ly_min)
                x_max = lx_max if x_max is None else max(x_max, lx_max)
                y_max = ly_max if y_max is None else max(y_max, ly_max)

        if x_min is None:
            self.content_bbox = None
        else:
            self.content_bbox = (x_min, y_min, x_max, y_max)

        self.dirty = False
        return self.render_cache

    def clear(self):
        for layer in self.layers:
            layer.canvas.fill(0)
        self.alpha_cache.fill(0)
        self.content_bbox = None
        self.dirty = True
