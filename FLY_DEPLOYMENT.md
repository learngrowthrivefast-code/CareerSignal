# CareerSignal — Fly.io Deployment Guide

**Time to live URL: ~45 minutes**
**Cost: Free tier (up to 3 shared VMs + 3GB storage)**
**Your app URL will be: `https://careersignal.fly.dev`**

---

## Overview

```
Your Mac (code)  →  Docker image  →  Fly.io server  →  careersignal.fly.dev
                                         │
                                    Persistent Volume
                                    /data/chromadb/      ← ChromaDB (user journeys)
                                    /data/users.db        ← SQLite (auth)
```

Data survives every deploy and restart. Users log in once, their journey persists forever.

---

## Step 1 — Install Docker Desktop (Mac)

```bash
# Option A: Homebrew
brew install --cask docker

# Option B: Download directly
# https://www.docker.com/products/docker-desktop/
# Choose: Apple Silicon (M1/M2/M3)
```

After install, open Docker Desktop and wait for the whale icon to show "Docker Desktop is running."

Verify:
```bash
docker --version
# Docker version 24.x.x
```

---

## Step 2 — Install Fly CLI

```bash
# Install flyctl
brew install flyctl

# Verify
fly version
# fly v0.x.x
```

---

## Step 3 — Create Fly.io Account & Login

```bash
# Sign up and login in one step
fly auth signup

# OR if you already have an account
fly auth login
```

Go to **fly.io** → sign up with GitHub or email. Free tier requires no credit card initially.

---

## Step 4 — Prepare Your Project Structure

Your project folder must look exactly like this before deploying:

```
careersignal/
├── Home.py
├── pages/
│   ├── 1_Profile.py
│   ├── 2_Coach.py
│   ├── 3_Roadmap.py
│   ├── 4_Fears.py
│   ├── 5_STAR_Stories.py
│   └── 6_JD_Analyzer.py
├── core/
│   ├── __init__.py
│   ├── auth.py
│   ├── database.py
│   ├── vector_store.py
│   ├── memory_manager.py
│   ├── coach_engine.py
│   ├── prompt_builder.py
│   └── roadmap.py
├── config/
│   └── settings.py          ← Use the updated Fly.io version
├── requirements.txt
├── Dockerfile               ← From this guide
├── fly.toml                 ← From this guide
└── .dockerignore            ← From this guide
```

Create `.dockerignore` (keeps image small):

```
.env
venv/
__pycache__/
*.pyc
.DS_Store
data/
.git/
*.md
```

---

## Step 5 — Update `config/settings.py`

Replace your local `settings.py` with the Fly.io version that uses `/data` as the
persistent volume path in production:

```python
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL   = "claude-haiku-4-5-20251001"

JWT_SECRET     = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM  = "HS256"
JWT_EXPIRY_HRS = 24

APP_ENV = os.getenv("APP_ENV", "development")

# Key line: production uses Fly.io volume, local uses ./data
DATA_DIR    = "/data" if APP_ENV == "production" else "./data"
CHROMA_PATH = os.path.join(DATA_DIR, "chromadb")
SQLITE_PATH = os.path.join(DATA_DIR, "users.db")

FREE_SESSION_LIMIT    = 10
PREMIUM_MONTHLY_PRICE = 49
MEMORY_CONTEXT_K      = 3
MAX_TOKENS            = 800

COHORTS = {
    "FreshGraduate":    "Fresh Builder (20–35)",
    "AgeAbove35Less50": "Bridge Builder (35–50)",
    "AgeAbove50":       "Navigator (50+)",
}

TARGET_ROLES = [
    "Director of AI", "VP of AI", "Director of AI Strategy",
    "Director of AI Programs", "Head of AI / ML",
    "Director of AI Governance", "VP of Engineering (AI)",
]
```

---

## Step 6 — Test Docker Build Locally First

```bash
cd careersignal

# Build the Docker image
docker build -t careersignal .

# Run it locally to verify it works
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=sk-ant-your-key-here \
  -e JWT_SECRET=test-secret-123 \
  -e APP_ENV=development \
  careersignal

# Open: http://localhost:8501
# If it works → proceed to deploy
# Ctrl+C to stop
```

---

## Step 7 — Create the Fly.io App

```bash
cd careersignal

# Launch — this creates the app on Fly.io
# When prompted:
#   App name: careersignal  (or careersignal-waseem if taken)
#   Region: iad (US East) — or choose closest to your users
#   Would you like to set up a Postgresql database? → No
#   Would you like to set up an Upstash Redis? → No
fly launch --no-deploy
```

This creates the app and generates `fly.toml`. Replace the generated `fly.toml` with the one from this guide (it has the volume mount and health check already configured).

---

## Step 8 — Create the Persistent Volume

```bash
# Create 1GB volume for ChromaDB + SQLite
# This is where ALL user data lives permanently
fly volumes create careersignal_data \
  --region iad \
  --size 1

# Verify
fly volumes list
# NAME                  ID          SIZE  REGION  ZONE
# careersignal_data     vol_xxxxx   1GB   iad     ...
```

**Important:** The volume name `careersignal_data` must match exactly what's in `fly.toml` under `[mounts] source`.

---

## Step 9 — Set Secret Environment Variables

```bash
# Set your API keys as Fly.io secrets
# These are encrypted and injected as env vars at runtime
# NEVER go in fly.toml or your code

fly secrets set ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
fly secrets set JWT_SECRET=$(openssl rand -base64 32)
fly secrets set APP_ENV=production

# Verify secrets are set (values are hidden)
fly secrets list
# NAME               DIGEST    CREATED AT
# ANTHROPIC_API_KEY  abc123    2026-04-26
# JWT_SECRET         def456    2026-04-26
# APP_ENV            ghi789    2026-04-26
```

---

## Step 10 — Deploy

```bash
fly deploy

# You'll see:
# ==> Building image
# ==> Pushing image to registry
# ==> Creating release
# ==> Monitoring deployment
# 1 desired, 1 placed, 1 healthy, 0 unhealthy
# --> v1 deployed successfully

# Your app is live at:
echo "https://$(fly status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Hostname"])')"
# → https://careersignal.fly.dev
```

---

## Step 11 — Verify Everything Works

```bash
# Check app status
fly status

# View live logs
fly logs

# Open in browser
fly open
```

Test the full flow:
1. Go to `https://careersignal.fly.dev`
2. Create an account
3. Complete the profile
4. Send a coaching message
5. Close the browser, reopen → your history should still be there

---

## Common Issues & Fixes

### App crashes on startup
```bash
fly logs
# Read the error. 99% of issues are:
# - Missing env var → fly secrets set KEY=value
# - Port mismatch → check Dockerfile EXPOSE 8501
```

### ChromaDB permission error
```bash
# SSH into the running machine
fly ssh console

# Check the volume is mounted
ls /data
# Should show: chromadb/  users.db

# Fix permissions if needed
chmod -R 755 /data
```

### App sleeping (auto_stop_machines = true)
First request after idle takes 3-5 seconds to wake up. This is normal on free tier.
To keep it always warm (costs ~$3/month):
```toml
# In fly.toml
min_machines_running = 1
```

### Ran out of free tier storage
```bash
# Extend volume size
fly volumes extend vol_xxxxxxxx --size 3
```

---

## Updating the App (After Code Changes)

```bash
# Every time you change code and want to push to production:
cd careersignal
fly deploy

# Takes ~2 minutes. Zero downtime — Fly.io does rolling deploy.
# Your data on the volume is untouched.
```

---

## Sharing With Your Newsletter Audience

Your permanent URL: `https://careersignal.fly.dev`

Send this to your newsletter:

> "I've built an AI career coaching tool for IT professionals targeting Director and VP of AI roles.
> It remembers your journey, reframes your experience in recruiter language, and gives you a personalized
> 18-month roadmap. It's free to try: careersignal.fly.dev
> First 50 users get permanent free access. I'd love your feedback."

---

## Free Tier Limits

| Resource | Free tier | What it means |
|---|---|---|
| Compute | 3 shared VMs | More than enough for 50 users |
| RAM | 256MB per VM | Upgrade to 512MB if ChromaDB is slow |
| Storage | 3GB volumes | ~500,000 coaching messages before upgrade |
| Bandwidth | 160GB/month | Effectively unlimited for 50 users |
| Cost | $0 | Until you exceed limits above |

**When to upgrade:** When you hit 200+ active users or ChromaDB volume approaches 2GB.
Upgrade path: `fly scale memory 512` and `fly volumes extend` — no migration needed.

---

## Month 2 — Custom Domain (Optional)

```bash
# Add your own domain (e.g. careersignal.io)
fly certs add careersignal.io

# Fly.io gives you the DNS records to add at your domain registrar
fly certs show careersignal.io

# Once DNS propagates (~10 min):
# https://careersignal.io is live with auto-SSL
```

---

*Deployment guide version: 0.1*
*Stack: Python 3.11 · Streamlit · ChromaDB · Fly.io*
*Estimated time to live URL: 45 minutes*
