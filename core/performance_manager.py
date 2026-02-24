import time
import threading
import queue
import cv2

class PerformanceManager:

    def __init__(self, gesture_controller, hand_tracker, ai_width=320, ai_height=240, skip_rate=3):
        self.gesture_controller = gesture_controller
        self.hand_tracker = hand_tracker

        self.ai_width = ai_width
        self.ai_height = ai_height
        self.skip_rate = skip_rate
        self.frame_counter = 0

        self.frame_queue = queue.Queue(maxsize=2)
        self.result_queue = queue.Queue(maxsize=2)
        self.running = True

        self.last_gesture_result = None
        self.last_hands = []

        self.fps = 0
        self.last_time = time.time()

        self.worker = threading.Thread(target=self._ai_worker, daemon=True)
        self.worker.start()

        # Warm-up
        self._warmup_models()

    def _warmup_models(self):
        dummy = cv2.imread("dummy.jpg") if False else None
        try:
            self.gesture_controller.recognize(dummy)
        except:
            pass

    def _ai_worker(self):
        while self.running:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                try:
                    hands = self.hand_tracker.detect(frame)
                    hand_landmarks = hands[0] if hands else None
                    gesture_data = self.gesture_controller.recognize(
                        frame,
                        hand_landmarks=hand_landmarks,
                        width=self.ai_width,
                        height=self.ai_height
                    )
                except Exception:
                    gesture_data = None
                    hands = []
                self.result_queue.put((gesture_data, hands))

    def process(self, frame):
        # Resize for AI only
        small_frame = cv2.resize(frame, (self.ai_width, self.ai_height))

        self.frame_counter += 1
        if self.frame_counter % self.skip_rate == 0:
            if not self.frame_queue.full():
                self.frame_queue.put(small_frame)

        # Get AI result if available
        if not self.result_queue.empty():
            gesture_data, hands = self.result_queue.get()
            self.last_gesture_result = gesture_data
            self.last_hands = hands

        return self.last_gesture_result, self.last_hands

    def update_fps(self):
        current = time.time()
        self.fps = 1 / max(1e-5, (current - self.last_time))
        self.last_time = current
        return int(self.fps)

    def stop(self):
        self.running = False
        self.worker.join()