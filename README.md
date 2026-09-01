# S.U.N.D.A.Y.
*Sentry Unit for Night and Day All Year*

## Overview

The project is intended to serve as a surveillance system for my room. It automatically turns on when I exit my apartment or at least when my phone exits the premises with me.

Utilizes a `Logitech` camera connected to my 24x7 running server, but can easily be reconfigured to work with any external camera provided the correct device drivers are installed for it.

## Workflow

1. **On exit:** Disconnect from my home Wi-Fi network → Launch `S.U.N.D.A.Y.`
2. **On entry:** Connect to my home Wi-Fi network → Stop `S.U.N.D.A.Y.`

Handled via a Wi-Fi-triggered [Shortcuts automation](shortcuts/README.md) on my phone, which runs the start/stop shortcuts over SSH.

My initial vision was to leverage Alexa's proximity capabilities to detect my arrival and departure from the apartment. However, this introduced numerous hurdles with respect to Alexa joining my Tailscale VPN to talk to my server.

Thanks to Advaith's suggestion *(my 🐐 manager @ Censys)* I set out to explore the Apple Shortcuts route which cleared my initial concerns!

## Setup

**Prerequisites:**
- Python >=3.10
- [`uv`](https://docs.astral.sh/uv/) — dependency management and virtual environment
- [`ffmpeg`](https://ffmpeg.org/) — camera capture
- [`task`](https://taskfile.dev/) — running the commands below
- A V4L2-compatible camera (e.g. `/dev/video0`)
- An AWS S3 bucket, if you want motion-triggered clips uploaded (optional)

**Steps:**

1. Install dependencies and create the virtual environment:
   ```
   uv sync
   ```
2. Adjust camera device, resolution, and framerate in [src/config.py](src/config.py) if needed.
3. If you want motion clips uploaded to S3, create a `.env` file in the project root:
   ```
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_DEFAULT_REGION=...
   AWS_S3_BUCKET_NAME=...
   ```
   The IAM user/role behind these credentials only needs `s3:PutObject` (and `s3:GetObject` if you want to fetch clips back) scoped to that bucket's objects (`arn:aws:s3:::<bucket>/*`). Without a `.env`, clips are still recorded locally but not uploaded.
4. Install and start the systemd service:
   ```
   task install
   task start
   ```

## Task Commands

| Command | Description |
|---|---|
| `task` | List all available tasks |
| `task install` | Install the systemd service (run once) |
| `task start` | Start the camera server |
| `task stop` | Stop the camera server |
| `task restart` | Restart the camera server |
| `task status` | Show camera server status |
| `task logs` | Tail the camera server logs live |
| `task enable` | Enable camera server to start on boot |
| `task disable` | Disable camera server from starting on boot |
| `task kill-ffmpeg` | Force-kill any stray `ffmpeg` processes (use if the camera LED stays on unexpectedly) |
| `task camera-check` | Check if the camera device is present and show supported formats |
| `task test-stream` | Grab 3 seconds of the stream and confirm it's producing real data |
| `task url` | Print the stream URL to open in a browser |
| `task firewall` | Allow the stream port through `ufw` over the `tailscale0` interface |

## Why S.U.N.D.A.Y.?

Like the GH description suggests, consider this project a counterpart to Tony's F.R.I.D.A.Y. To be honest, the idea for this project occurred to me in the  late hours of a random Saturday which I continued to develop until the morning hours of Sunday lol.
