# GitOps CI/CD Automation

A lightweight, webhook-driven GitOps pipeline that automatically deploys a Dockerized Flask application whenever changes are pushed to a Git repository. The system combines a Flask webhook listener, a shell-based auto-flipper bot, and a Docker deployment script to create a fully automated, Git-as-source-of-truth deployment loop — no CI platform required.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Repository Structure](#repository-structure)
- [Components](#components)
- [Prerequisites](#prerequisites)
- [Setup and Usage](#setup-and-usage)
- [Configuration](#configuration)
- [Limitations](#limitations)

---

## How It Works

The pipeline operates in two parallel tracks:

**Event-driven track:** GitHub sends a webhook POST to the listener whenever a push occurs. The listener calls `deploy.sh`, which pulls the latest code, rebuilds the Docker image, and restarts the container.

**Polling track:** `autoflipper.sh` runs in a continuous 30-second loop — pulling the latest state from the remote, toggling `config.json` between `Standby` and `Active`, and pushing the commit back. Each push triggers the webhook, which drives a fresh deployment.

The web app (`app.py`) reads `config.json` on every request, so the live UI reflects the current state within seconds of each commit.

```
Developer push / Bot commit
        │
        ▼
   GitHub Webhook ──► ngrok tunnel ──► webhook-listener.py (port 5001)
                                               │
                                               ▼
                                          deploy.sh
                                     ┌─────────────────┐
                                     │ git pull         │
                                     │ docker build     │
                                     │ docker stop/rm   │
                                     │ docker run       │
                                     └─────────────────┘
                                               │
                                               ▼
                                     app.py (port 8080)
                                     reads config.json → UI
```

---

## Repository Structure

```
USP_MiniProject/
├── app.py                    # Flask web app — serves the status UI and /api/theme
├── webhook-listener.py       # Flask webhook receiver — listens on port 5001
├── deploy.sh                 # Deployment script — build, stop, run Docker container
├── autoflipper.sh            # Bot — continuously toggles config and pushes commits
├── Dockerfile                # Builds the app image (python:3.9-slim, port 5000)
├── config.json               # Live state file (toggled by autoflipper)
├── config.active.json        # Template: Active state config
├── config.standby.json       # Template: Standby state config
├── requirements.txt          # Python dependencies (Flask)
├── static/
│   ├── styles.css
│   └── animations.js
└── templates/
    └── index.html            # Status UI — polls /api/theme for live updates
```

---

## Components

### `app.py` — Web Application (port 5000 / 8080 externally)

A minimal Flask app with three routes:

- `GET /` — renders `index.html` with the current config baked in at load time
- `GET /api/theme` — returns the current `config.json` as JSON; polled by the frontend for live state updates
- `GET /health` — returns `"OK"` for container health checks

The app reads `config.json` from disk on every request, so a new deployment immediately reflects the latest state — no restart needed.

### `webhook-listener.py` — Webhook Receiver (port 5001)

Listens for `POST /webhook` requests from GitHub (forwarded via ngrok). On each request, it runs `deploy.sh` using `subprocess.run` with `check=True`, captures stdout/stderr, and returns `200` on success or `500` with the error message on failure.

Runs on port 5001 so it doesn't conflict with the app on 8080.

### `deploy.sh` — Deployment Script

Runs with `set -e` (exits immediately on any error). Steps:

1. `git pull origin main` — fetch latest code
2. `docker build -t myapp:latest .` — rebuild the image
3. `docker stop myapp` / `docker rm myapp` — tear down the old container (failures tolerated via `|| true`)
4. `docker run -d --name myapp -p 8080:5000 myapp:latest` — start the new container

> Requires `sudo` for Docker commands. The script uses the full path `/usr/local/bin/docker` to avoid PATH issues when invoked by the webhook listener subprocess.

### `autoflipper.sh` — State Toggle Bot

Runs in an infinite loop with a 30-second sleep between cycles:

1. `git pull` — sync with remote
2. Read `config.json` — check whether the current state is `Standby` or `Active`
3. Copy the appropriate template (`config.active.json` or `config.standby.json`) over `config.json`
4. `git add` → `git commit` → `git push origin main` — commit the state change
5. The push triggers the GitHub webhook, which triggers a fresh deployment

This creates a self-driving demo loop. Stop it with `Ctrl+C`.

### `Dockerfile`

Builds from `python:3.9-slim`. Copies `requirements.txt` first for layer caching, installs dependencies, copies the rest of the app, exposes port 5000, and runs `python3 app.py`.

---

## Prerequisites

- Python 3.x with `pip`
- Docker (with `sudo` access, or configure Docker to run without sudo)
- Git, configured with push access to the repository
- [ngrok](https://ngrok.com/) — for exposing the local webhook listener to GitHub
- A GitHub repository with a webhook configured (see [Setup](#setup-and-usage))

Install Python dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt` should contain at minimum:

```
Flask
```

---

## Setup and Usage

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/USP_MiniProject.git
cd USP_MiniProject
```

### 2. Start the webhook listener

```bash
python3 webhook-listener.py
```

This starts the listener on `http://0.0.0.0:5001`. Keep this running in its own terminal.

### 3. Expose the listener via ngrok

In a separate terminal:

```bash
ngrok http 5001
```

Copy the generated HTTPS forwarding URL (e.g. `https://xxxx.ngrok-free.app`).

### 4. Configure the GitHub webhook

In your repository on GitHub: **Settings → Webhooks → Add webhook**

- **Payload URL:** `https://xxxx.ngrok-free.app/webhook`
- **Content type:** `application/json`
- **Events:** Just the push event
- **Active:** ✓

### 5. Run the auto-flipper bot (optional — for the demo loop)

In a separate terminal:

```bash
chmod +x autoflipper.sh
./autoflipper.sh
```

The bot will start committing state toggles every 30 seconds, each of which triggers a deployment.

### 6. Trigger a deployment manually

Push any change to the `main` branch:

```bash
git add .
git commit -m "test: trigger deployment"
git push origin main
```

The webhook will fire, the listener will call `deploy.sh`, and the app will be rebuilt and restarted at `http://localhost:8080`.

---

## Configuration

The app's visual state is controlled by `config.json`. Two templates are included:

**`config.standby.json`** — idle/waiting state:
```json
{
  "theme_name": "Standby",
  "main_text": "AWAITING DEPLOYMENT",
  "app_state": "theme-standby"
}
```

**`config.active.json`** — active/deploying state:
```json
{
  "theme_name": "Active",
  "main_text": "DEPLOYMENT IN PROGRESS!",
  "app_state": "theme-active"
}
```

`autoflipper.sh` detects which state is current by checking for `"theme_name": "Standby"` in the live `config.json` and copies the appropriate template over it.

To change the polling interval, edit the `sleep 30` line in `autoflipper.sh`.

---

## Limitations

- **Not production-ready:** `webhook-listener.py` uses the Flask development server. For production, serve it behind Gunicorn or uWSGI.
- **No webhook authentication:** The `/webhook` endpoint accepts any POST request. A real deployment should verify the GitHub `X-Hub-Signature-256` header.
- **ngrok dependency:** The free tier of ngrok assigns a new URL on every restart, requiring the GitHub webhook URL to be updated each time. A paid ngrok plan or a fixed public server would remove this friction.
- **Single-threaded loop:** `autoflipper.sh` is sequential. If a `git push` or `docker build` takes longer than expected, the next cycle is delayed.
- **No health checks or rollback:** If the new container crashes after `docker run`, the script reports success regardless. There is no automated rollback to the previous image.
- **Hardcoded 30-second interval:** The cycle time in `autoflipper.sh` is fixed. It does not adapt to load or change frequency.
- **sudo required for Docker:** The `deploy.sh` script calls Docker with explicit `sudo`. Configure `/etc/sudoers` to allow the user to run these specific commands without a password prompt, or add the user to the `docker` group.