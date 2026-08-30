#!/usr/bin/env python3
"""
Motion detection by diffing consecutive frames.
"""
# Import third-party libraries
import cv2
import numpy as np

# Import custom settings
from src.config import config

FRAME_AREA = int(config.WIDTH) * int(config.HEIGHT)

DIFF_THRESHOLD = 30
MIN_CONTOUR_AREA = int(FRAME_AREA * 0.01)  # ~1% of the frame, scales with resolution


class MotionDetector:
    """Flags motion by diffing each incoming frame against the previous one."""

    def __init__(self, diff_threshold=DIFF_THRESHOLD, min_area=MIN_CONTOUR_AREA):
        self.diff_threshold = diff_threshold
        self.min_area = min_area
        self._prev_gray = None

    def update(self, frame):
        """Feed in the next frame (BGR numpy array). Returns True if
        motion was detected relative to the previous frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self._prev_gray is None:
            self._prev_gray = gray
            return False

        diff = cv2.absdiff(self._prev_gray, gray)
        self._prev_gray = gray

        thresh = cv2.threshold(diff, self.diff_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion = any(cv2.contourArea(c) >= self.min_area for c in contours)
        if motion:
            print("[motion_detector] motion detected")
        return motion

    def update_from_jpeg(self, jpeg_bytes):
        """Decode a JPEG frame (as produced by the camera server) and run
        motion detection on it. Returns True if motion was detected."""
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return False
        return self.update(frame)


if __name__ == "__main__":
    cap = cv2.VideoCapture(config.DEVICE)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(config.WIDTH))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(config.HEIGHT))

    detector = MotionDetector()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue
            detector.update(frame)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
