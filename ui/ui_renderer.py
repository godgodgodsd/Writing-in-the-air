import cv2


class UIRenderer:

    def draw_brush_preview(self, frame, point, size, color):
        cv2.circle(frame, point, size, color, 1)

    def draw_status(self, frame, text, y_offset=20, color=(0, 255, 0)):
        cv2.putText(
            frame,
            text,
            (20, frame.shape[0] - y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )
