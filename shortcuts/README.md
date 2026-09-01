# Shortcuts

## Overview

Apple Shortcuts for starting and stopping `S.U.N.D.A.Y.` remotely from an iPhone, iPad, or Mac — used to drive the [Wi-Fi automation](../README.md#workflow) described in the main README, since the server itself has no public endpoint and is only reachable over Tailscale.

| Shortcut | What it does |
|---|---|
| `Start S.U.N.D.A.Y. over SSH.plist` | Connects to Tailscale → SSHes into the server → runs `task start` → Disconnects from Tailscale |
| `Stop S.U.N.D.A.Y. over SSH.plist` | Connects to Tailscale → SSHes into the server → runs `task stop` → Disconnects from Tailscale |

The `.plist` files here are a **readable record of the actions**, extracted from the Shortcuts app's local database — not signed `.shortcut` bundles, so they won't import by double-clicking. Follow the setup steps below to recreate them by hand.

## Setup

**Prerequisites:**
- The [Shortcuts](https://apps.apple.com/app/shortcuts/id915249334) app (macOS 12+, iOS 13+)
- The [Tailscale](https://tailscale.com/download) app installed and signed into the same tailnet as the server
- SSH access to the server (its Tailscale IP or MagicDNS name, plus a user/password or key)

**Steps:**

1. Open Shortcuts → **New Shortcut**, name it `Start S.U.N.D.A.Y. over SSH` (or `Stop ...`).
2. Add a **Connect to VPN** action, choose the **Tailscale** app.
3. Add a **Run Script Over SSH** action and fill in:
   | Field | Value |
   |---|---|
   | Host | your server's Tailscale IP or MagicDNS name |
   | User | your SSH username |
   | Authentication | password, or a key — see note below |
   | Script | `cd /home/<user>/code/S.U.N.D.A.Y.` then `task start` (or `task stop`) |
4. Add a **Disconnect from VPN** action, choose **Tailscale** again.
5. Repeat for the other shortcut (swap `task start` for `task stop`, or vice versa).

Reference the corresponding `.plist` in this folder if you want the exact step comments/wording used originally.

> **Security note:** the SSH action stores its password in the shortcut itself (readable if the shortcut is ever exported or synced). Prefer key-based auth if the Shortcuts SSH action on your OS version supports it. Never commit an exported `.shortcut` file or plist containing a real password to this repo — the ones here have the password redacted.

## Automating the Trigger

Once both shortcuts exist, you can have them run without manual taps via **Automation** in the Shortcuts app:

1. Go to the **Automation** tab → **+** → **Create Personal Automation**.
2. Pick a trigger, e.g.:
   - **Wi-Fi** connects/disconnects (e.g. leaving your home network — this is what drives the workflow in the main README)
   - **Arrive** / **Leave** a location
   - **Time of Day**
   - **NFC** tag tap
3. Add action → **Run Shortcut** → select `Start S.U.N.D.A.Y. over SSH` (use `Disconnect` → Start, `Connect` → Stop, or whichever pairing matches your trigger).
4. Turn **Ask Before Running** off if you want it fully hands-free (it'll still show a notification banner).

Wi-Fi- and location-based automations only run reliably on iOS/iPadOS devices with Shortcuts installed; on macOS, Time of Day or manual menu-bar triggers are the practical options.
