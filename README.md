# ◎ CareerSignal

AI-powered career coaching for IT professionals targeting Director and VP of AI roles.

Built with Python · Streamlit · ChromaDB · Claude Haiku (Anthropic) · JWT Auth

---

## What It Does

CareerSignal maintains a **persistent, personalized coaching journey** across sessions. Every conversation, STAR story, fear, and roadmap milestone is stored in a local vector database and retrieved contextually — so each session picks up exactly where the last one left off.

The AI coach is built around four permanent Director/VP AI questions that never change regardless of what the JD landscape does:

1. Can you make the right bets on which AI investments matter before it's obvious?
2. Can you translate between technical reality and business risk for executives?
3. Can you build and retain teams that execute through ambiguity?
4. Can you establish organizational trust in AI systems?

---

## Features

| Feature | Free | Premium |
|---|---|---|
| AI coaching sessions | 10/month | Unlimited |
| Profile + roadmap | ✓ | ✓ |
| Fear inventory + reframes | ✓ | ✓ |
| STAR story builder | — | ✓ |
| JD gap analyzer | — | ✓ |
| Journey memory | 7 days | Unlimited |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│  Home · Profile · Coach · Roadmap · Fears · STAR · JD       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     Core Services                            │
│  Auth (JWT)  ·  Coach Engine  ·  Memory Manager             │
│  Prompt Builder  ·  Vector Store  ·  Roadmap Defaults        │
└──────────┬──────────────────────────┬───────────────────────┘
           │                          │
┌──────────▼──────┐       ┌───────────▼──────────────────────┐
│  Anthropic API  │       │  ChromaDB (embedded, local)       │
│  claude-haiku   │       │  user_profiles · journeys         │
│  ~$0.001/msg    │       │  star_stories · fears · roadmap   │
└─────────────────┘       └──────────────────────────────────┘
```

**Layered context per coaching call:**

```
Layer 1: System prompt + coaching methodology
Layer 2: User profile (from ChromaDB)
Layer 3: Semantically relevant past turns (top-k retrieval)
Layer 4: STAR stories (when evidence is needed)
Layer 5: Current conversation turn
─────────────────────────────────────────────
~2,400 tokens per call · ~$0.0003 per message
```

---

## Project Structure

```
careersignal/
├── Home.py                  # Login / register landing
├── pages/
│   ├── 1_Profile.py         # Intake form (runs once, editable)
│   ├── 2_Coach.py           # AI coaching chat
│   ├── 3_Roadmap.py         # 5-phase milestone tracker
│   ├── 4_Fears.py           # Fear inventory with reframes
│   ├── 5_STAR_Stories.py    # Story bank (Premium)
│   └── 6_JD_Analyzer.py     # JD gap analysis (Premium)
├── core/
│   ├── auth.py              # JWT + bcrypt
│   ├── database.py          # SQLite user management
│   ├── vector_store.py      # ChromaDB CRUD
│   ├── memory_manager.py    # Semantic retrieval
│   ├── coach_engine.py      # LLM orchestration
│   ├── prompt_builder.py    # Layered prompt assembly
│   └── roadmap.py           # Roadmap + fear defaults
├── config/
│   └── settings.py          # Keys, constants, tier config
├── requirements.txt
├── ARCHITECTURE.md          # Full system design
└── IMPLEMENTATION.md        # Step-by-step build guide
```

---

## Quick Start

**1. Clone and set up environment**

```bash
git clone https://github.com/learngrowthrivefast-code/CareerSignal.git
cd CareerSignal

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

**2. Add your API key**

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# Get one at: console.anthropic.com → API Keys
```

**3. Run**

```bash
streamlit run Home.py
# Opens at http://localhost:8501
```

**4. Share with beta users (no deployment needed)**

```bash
brew install ngrok
ngrok http 8501
# Share the generated URL
```

---

## Cost Estimate

| Users | Tokens/day | Cost/month |
|---|---|---|
| You alone | ~5,000 | ~$0.03 |
| 10 active | ~50,000 | ~$0.30 |
| 50 active | ~250,000 | ~$1.50 |
| 50 power users | ~1M | ~$6.00 |

Haiku pricing: ~$0.25/M input tokens · ~$1.25/M output tokens. **Under $10/month for 50 users.**

---

## Cohorts

| Cohort | Label | Key Insight |
|---|---|---|
| 20–35 | Fresh Builder | First-mover governance play. Portfolio over tenure. |
| 35–50 | Bridge Builder | Speaks both languages. Stop waiting for permission. |
| 50+ | Navigator | Scar tissue advantage. Cross-cycle judgment is the asset. |

---

## Deployment Roadmap

```
Phase 1 (Now):     Local + ngrok, SQLite + ChromaDB on disk
Phase 2 (Month 2): Fly.io / Railway, persistent volume
Phase 3 (Month 4): Pinecone + Postgres + Stripe payments
Phase 4 (Month 6): Full SaaS — custom domain, email auth, community
```

---

## Dependencies

```
streamlit==1.32.0
anthropic==0.25.0
chromadb==0.4.24
bcrypt==4.1.2
PyJWT==2.8.0
python-dotenv==1.0.1
pandas==2.2.0
```

One external API key required (Anthropic). ChromaDB and SQLite run fully embedded — no server, no Docker.

---

*MVP v0.1 · April 2026*
