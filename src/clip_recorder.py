#!/usr/bin/env python3
"""
Records a video clip spanning the moments before and after a motion
event, then uploads it to S3 under a year/month/day key prefix.
"""
# Import standard libraries
import collections
import datetime
import os
import queue
import tempfile
import threading
import time

# Import third-party libraries
import boto3
import cv2
import numpy as np

# Import custom settings
from src.config import config


class ClipRecorder:
    """
    Feed every incoming JPEG frame to `add_frame`. When motion fires,
    call `trigger_event()`: it stitches together the buffered frames from
    the last `pre_seconds` with the next `post_seconds` of incoming
    frames, encodes them into an mp4, and uploads it to
    `s3://<bucket>/<year>/<month>/<day>/<HHMMSS>_motion.mp4`.

    A second trigger while a clip is already recording is ignored, so a
    single event produces one clip rather than overlapping ones.
    """

    def __init__(self, bucket=None, pre_seconds=None, post_seconds=None):
        self.bucket = bucket if bucket is not None else config.S3_BUCKET
        self.pre_seconds = pre_seconds if pre_seconds is not None else config.PRE_EVENT_SECONDS
        self.post_seconds = post_seconds if post_seconds is not None else config.POST_EVENT_SECONDS

        self._pre_buffer = collections.deque()  # (timestamp, jpeg_bytes)
        self._buffer_lock = threading.Lock()

        self._recording = False
        self._record_lock = threading.Lock()
        self._event_frames = None
        self._event_deadline = None
        self._event_started_at = None

        self._upload_queue = queue.Queue()
        self._upload_thread = threading.Thread(target=self._upload_worker, daemon=True)
        self._upload_thread.start()

        if not self.bucket:
            print("[clip_recorder] S3_BUCKET_NAME not set, clips will be encoded but not uploaded")

        try:
            self._s3 = boto3.client("s3")
        except Exception as e:
            print(f"[clip_recorder] could not create S3 client: {e}")
            self._s3 = None

    def add_frame(self, jpeg_bytes):
        """Call this for every new frame coming off the camera."""
        now = time.time()

        with self._buffer_lock:
            self._pre_buffer.append((now, jpeg_bytes))
            cutoff = now - self.pre_seconds
            while self._pre_buffer and self._pre_buffer[0][0] < cutoff:
                self._pre_buffer.popleft()

        with self._record_lock:
            if not self._recording:
                return
            self._event_frames.append((now, jpeg_bytes))
            if now >= self._event_deadline:
                self._finish_event()

    def trigger_event(self):
        """Call this when motion is detected. No-op if a clip is already
        being recorded."""
        with self._record_lock:
            if self._recording:
                return

            with self._buffer_lock:
                self._event_frames = list(self._pre_buffer)

            self._event_started_at = (
                self._event_frames[0][0] if self._event_frames else time.time()
            )
            self._event_deadline = time.time() + self.post_seconds
            self._recording = True
            print("[clip_recorder] motion event triggered, recording clip...")

    def _finish_event(self):
        # Caller must hold self._record_lock.
        frames = self._event_frames
        started_at = self._event_started_at
        self._recording = False
        self._event_frames = None
        self._event_deadline = None
        self._event_started_at = None
        self._upload_queue.put((frames, started_at))

    def _upload_worker(self):
        while True:
            frames, started_at = self._upload_queue.get()
            try:
                self._encode_and_upload(frames, started_at)
            except Exception as e:
                print(f"[clip_recorder] error processing clip: {e}")

    def _encode_and_upload(self, frames, started_at):
        if not frames:
            return

        width, height = int(config.WIDTH), int(config.HEIGHT)
        duration = frames[-1][0] - frames[0][0]
        fps = (len(frames) / duration) if duration > 0 else 1

        tmp_path = tempfile.mktemp(suffix=".mp4")
        writer = cv2.VideoWriter(tmp_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        try:
            for _, jpeg_bytes in frames:
                arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                if (frame.shape[1], frame.shape[0]) != (width, height):
                    frame = cv2.resize(frame, (width, height))
                writer.write(frame)
        finally:
            writer.release()

        key = datetime.datetime.fromtimestamp(started_at).strftime("%Y/%m/%d/%H-%M-%S") + ".mp4"

        if not (self.bucket and self._s3):
            print(f"[clip_recorder] clip ready at {tmp_path} (not uploaded, no bucket configured)")
            return

        try:
            self._s3.upload_file(tmp_path, self.bucket, key)
            print(f"[clip_recorder] uploaded s3://{self.bucket}/{key}")
        except Exception as e:
            print(f"[clip_recorder] upload failed, clip kept at {tmp_path}: {e}")
            return

        os.remove(tmp_path)
