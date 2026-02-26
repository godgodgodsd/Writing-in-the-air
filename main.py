"""
Enterprise AI Paint
Entry Point
"""

import cv2
from core.app_controller import AppController
import time



def main(show_gesture_ui=False):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera not found")
        return

    # Get camera resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    app = AppController(width, height)


    cv2.namedWindow("AI Paint",cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("AI Paint", app.handle_mouse)
    # Ensure window matches camera resolution so mouse coords map correctly
    cv2.resizeWindow("AI Paint", width, height)
    if show_gesture_ui:
        cv2.namedWindow("Gesture UI", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Gesture UI", app.handle_gesture_ui_mouse)
        cv2.resizeWindow("Gesture UI", 520, 720)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        frame = app.process_frame(frame)
    
        cv2.imshow("AI Paint", frame)
        if show_gesture_ui:
            cv2.imshow("Gesture UI", app.get_gesture_ui_frame())

        key = cv2.waitKey(1) & 0xFF
        app.handle_key(key)
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main(show_gesture_ui=False)
