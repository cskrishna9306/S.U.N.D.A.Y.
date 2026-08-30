#!/usr/bin/env python3
"""
Entry point: starts the camera reader, motion detector, and MJPEG HTTP
server, in that order.
"""
# Import standard libraries
import threading

# Import project modules
from src import server
from src.clip_recorder import ClipRecorder
from src.config import config
from src.motion_detector import MotionDetector


def motion_detector_loop():
    """
    Watch the camera server's shared frame feed, run motion detection on
    every new frame, and record a clip around any motion event.
    """
    detector = MotionDetector()
    recorder = ClipRecorder()
    last_frame = None

    while True:
        with server.frame_condition:
            server.frame_condition.wait(timeout=5)
            frame = server.latest_frame
        if frame is None or frame is last_frame:
            continue
        last_frame = frame

        recorder.add_frame(frame)
        if detector.update_from_jpeg(frame):
            recorder.trigger_event()


if __name__ == "__main__":
    # 1. Camera reader first, so frames exist before anything consumes them.
    reader_thread = threading.Thread(target=server.ffmpeg_reader, daemon=True)
    reader_thread.start()

    # 2. Motion detector, watching that same frame feed.
    motion_thread = threading.Thread(target=motion_detector_loop, daemon=True)
    motion_thread.start()

    # 3. HTTP server last; it blocks the main thread.
    http_server = server.ThreadingHTTPServer(
        ("0.0.0.0", config.LISTEN_PORT), server.MJPEGHandler
    )
    print(f"Serving MJPEG stream on port {config.LISTEN_PORT}, path /stream.mjpg")
    http_server.serve_forever()
