"""
Advanced Stroke Smoothing Pipeline

Stages:
1. Distance threshold filtering (jitter rejection)
2. Exponential moving average
3. Velocity smoothing
"""

import math


class StrokeSmoother:

    def __init__(self):
        self.prev_point = None
        self.prev_velocity = 0
        self.alpha = 0.6
        self.min_distance = 2

    def reset(self):
        self.prev_point = None
        self.prev_velocity = 0

    def smooth(self, point):
        if self.prev_point is None:
            self.prev_point = point
            return point, 0

        dx = point[0] - self.prev_point[0]
        dy = point[1] - self.prev_point[1]
        dist = math.sqrt(dx*dx + dy*dy)

        # Ignore tiny movements to avoid jitter.
        if dist < self.min_distance:
            return None, 0

        # Exponential smoothing to stabilize the stroke.
        smoothed_x = int(
            self.alpha * point[0] +
            (1 - self.alpha) * self.prev_point[0]
        )
        smoothed_y = int(
            self.alpha * point[1] +
            (1 - self.alpha) * self.prev_point[1]
        )

        velocity = dist
        self.prev_velocity = velocity
        self.prev_point = (smoothed_x, smoothed_y)

        return self.prev_point, velocity
