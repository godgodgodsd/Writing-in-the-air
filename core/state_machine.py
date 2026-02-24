"""
State Machine
Manages application state transitions.
"""

class StateMachine:

    IDLE = "IDLE"
    DRAWING = "DRAWING"
    ERASING = "ERASING"
    SETTINGS = "SETTINGS"
    PAUSED = "PAUSED"

    def __init__(self):
        self.state = StateMachine.IDLE

    def set(self, new_state):
        self.state = new_state

    def get(self):
        return self.state

    def is_state(self, state):
        return self.state == state