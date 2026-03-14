import cv2


class UIRenderer:

    def draw_brush_preview(self, frame, point, size, color):
        cv2.circle(frame, point, size, color, 1)

    def draw_status(self, frame, text, y_offset=20, color=(0, 255, 0), scale=0.7, thickness=2):
        cv2.putText(
            frame,
            text,
            (20, frame.shape[0] - y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness
        )
