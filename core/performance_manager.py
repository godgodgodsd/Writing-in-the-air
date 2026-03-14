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

        # Keep queues tiny to prioritize fresh data and reduce lag.
        self.frame_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)
        self.running = True

        self.last_gesture_result = None
        self.last_hands = []

        self.fps = 0
        self.last_time = time.time()
        self.fps_smoothed = 0.0

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
            try:
                frame = self.frame_queue.get(timeout=0.02)
            except queue.Empty:
                continue

            try:
                # Run AI on the downscaled frame in a background thread.
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

            # Drop stale result and keep only latest inference.
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.result_queue.put_nowait((gesture_data, hands))
            except queue.Full:
                pass

    def process(self, frame):
        self.frame_counter += 1
        if self.frame_counter % self.skip_rate == 0:
            # Resize only when we actually schedule AI work.
            small_frame = cv2.resize(frame, (self.ai_width, self.ai_height))
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            try:
                self.frame_queue.put_nowait(small_frame)
            except queue.Full:
                pass

        # Get the most recent AI result if available.
        while not self.result_queue.empty():
            gesture_data, hands = self.result_queue.get()
            self.last_gesture_result = gesture_data
            self.last_hands = hands

        return self.last_gesture_result, self.last_hands

    def update_fps(self):
        current = time.time()
        instant_fps = 1 / max(1e-5, (current - self.last_time))
        if self.fps_smoothed == 0.0:
            self.fps_smoothed = instant_fps
        else:
            self.fps_smoothed = (0.15 * instant_fps) + (0.85 * self.fps_smoothed)
        self.fps = self.fps_smoothed
        self.last_time = current
        return int(self.fps)

    def stop(self):
        self.running = False
        self.worker.join(timeout=0.5)
