#!/usr/bin/env python3
"""
Multi-client MJPEG streaming server.
Launches ffmpeg once, reads its MJPEG output from stdout, and fans
individual frames out to any number of simultaneously connected browsers.
"""
# Import standard libraries
import subprocess
import threading
import socket
import socketserver
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

# Import custom settings
from src.config import config

latest_frame = None
frame_lock = threading.Lock()
frame_condition = threading.Condition(frame_lock)


def ffmpeg_reader():
    """Continuously run ffmpeg, read its stdout, split into JPEG frames,
    and store the newest frame for consumers to pick up."""
    global latest_frame

    cmd = [
        "ffmpeg",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-video_size", f"{config.WIDTH}x{config.HEIGHT}",
        "-framerate", config.FRAMERATE,
        "-i", config.DEVICE,
        "-c", "copy",
        "-f", "mjpeg",
        "-",
    ]

    while True:
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=10**8,
            )
            buf = b""
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                buf += chunk

                # Find a complete JPEG frame: starts with FFD8, ends with FFD9
                start = buf.find(b"\xff\xd8")
                end = buf.find(b"\xff\xd9")
                if start != -1 and end != -1 and end > start:
                    frame = buf[start:end + 2]
                    buf = buf[end + 2:]
                    with frame_condition:
                        latest_frame = frame
                        frame_condition.notify_all()
            proc.wait()
        except Exception as e:
            print(f"[ffmpeg_reader] error: {e}, restarting in 2s...")
        import time
        time.sleep(2)


class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path

        if path in ("/", "/live.html"):
            self.serve_live_html()
            return

        if path != "/stream.mjpg":
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header(
            "Content-Type",
            f"multipart/x-mixed-replace; boundary={config.BOUNDARY}",
        )
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        try:
            last_sent = None
            while True:
                with frame_condition:
                    frame_condition.wait(timeout=5)
                    frame = latest_frame
                if frame is None or frame is last_sent:
                    continue
                last_sent = frame
                try:
                    self.wfile.write(f"--{config.BOUNDARY}\r\n".encode())
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                except (BrokenPipeError, ConnectionResetError):
                    break
        except Exception:
            pass

    def serve_live_html(self):
        try:
            body = config.LIVE_HTML_PATH.read_bytes()
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # silence per-request logging


class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    reader_thread = threading.Thread(target=ffmpeg_reader, daemon=True)
    reader_thread.start()

    server = ThreadingHTTPServer(("0.0.0.0", config.LISTEN_PORT), MJPEGHandler)
    print(f"Serving MJPEG stream on port {config.LISTEN_PORT}, path /stream.mjpg")
    server.serve_forever()