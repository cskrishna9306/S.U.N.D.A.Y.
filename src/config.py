# Import standard libraries
import os
from pathlib import Path

# Import third-party libraries
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Settings for our surveillance system.
    """
    DEVICE = "/dev/video0"
    WIDTH = "1280"
    HEIGHT = "720"
    FRAMERATE = "30"
    LISTEN_PORT = 8080

    BOUNDARY = "ffmpegboundary"
    LIVE_HTML_PATH = Path(__file__).parent / "live.html"

    # Motion-triggered clip recording. AWS credentials are picked up by
    # boto3 from the environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    # AWS_DEFAULT_REGION) - nothing to configure here.
    S3_BUCKET = os.environ.get("AWS_S3_BUCKET_NAME", "")
    PRE_EVENT_SECONDS = 60
    POST_EVENT_SECONDS = 120

config = Config()