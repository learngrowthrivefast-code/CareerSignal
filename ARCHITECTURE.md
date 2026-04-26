# CareerSignal — System Architecture

**Version:** 0.1 (MVP)
**Stack:** Python · Streamlit · ChromaDB · Haiku API · JWT Auth
**Target:** Local development → 50+ newsletter users
**Last updated:** April 2026

---

## 1. System Overview

CareerSignal is an AI-powered career coaching platform that maintains a **persistent, personalized user journey** across sessions. Each user's profile, coaching history, fears, roadmap progress, and STAR stories are stored in a local vector database and retrieved contextually to make every coaching session feel like a continuation — not a restart.

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                         │
│                    Streamlit Frontend                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP (localhost:8501)
┌──────────────────────▼──────────────────────────────────────┐
│                   STREAMLIT APP SERVER                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │  Auth Layer │  │ Session Mgr  │  │  Page Router    │    │
│  │  (JWT)      │  │ (st.session) │  │  (multipage)    │    │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘    │
│         └────────────────┼───────────────────┘             │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────────┐  │
│  │                  CORE SERVICES                        │  │
│  │  ┌──────────────┐   ┌──────────────┐                 │  │
│  │  │ Coach Engine │   │Journey Store │                 │  │
│  │  │ (LLM calls)  │   │(CRUD ops)    │                 │  │
│  │  └──────┬───────┘   └──────┬───────┘                 │  │
│  │         │                  │                          │  │
│  │  ┌──────▼───────┐   ┌──────▼───────┐                 │  │
│  │  │ Prompt Builder│  │ Memory Mgr   │                 │  │
│  │  │ (per user)   │   │(retrieval)   │                 │  │
│  │  └──────┬───────┘   └──────┬───────┘                 │  │
│  └─────────┼──────────────────┼─────────────────────────┘  │
└────────────┼──────────────────┼─────────────────────────────┘
             │                  │
┌────────────▼──────┐  ┌────────▼──────────────────────────┐
│   HAIKU API       │  │         ChromaDB (Local)           │
│   claude-haiku-*  │  │                                    │
│                   │  │  Collections:                      │
│   ~$0.001/msg     │  │  ├── users          (profiles)     │
│   Fast responses  │  │  ├── journeys       (sessions)     │
│   Low cost for    │  │  ├── star_stories   (STAR bank)    │
│   50+ users       │  │  ├── fears          (fear tracker) │
│                   │  │  └── roadmap_tasks  (progress)     │
└───────────────────┘  └────────────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 Frontend — Streamlit Multipage App

```
careersignal/
└── app/
    ├── Home.py                  # Login / Register landing
    └── pages/
        ├── 1_Profile.py         # Intake form (runs once, editable)
        ├── 2_Coach.py           # Main AI coaching chat
        ├── 3_Roadmap.py         # Milestone tracker with checkboxes
        ├── 4_Fears.py           # Fear inventory with reframes
        ├── 5_STAR_Stories.py    # Story bank (Premium)
        └── 6_JD_Analyzer.py     # JD gap analysis (Premium)
```

Streamlit handles all UI rendering. No React, no JavaScript, no build step. `st.session_state` manages in-session state. ChromaDB manages cross-session persistence.

---

### 2.2 Auth Layer — JWT + SQLite Users Table

**Why not OAuth for MVP:** Google OAuth requires a public redirect URI. For local + 50 users, JWT with bcrypt passwords is faster to ship and simpler to debug.

```
Auth Flow:
Register → hash password (bcrypt) → store in users.db (SQLite)
Login    → verify password        → issue JWT token (24hr expiry)
Request  → decode JWT             → load user_id → fetch ChromaDB journey
```

**Token storage:** `st.session_state["token"]` — lives for the browser session. User re-logs in on new session. No persistent cookies in MVP.

**User record (SQLite `users` table):**
```sql
user_id     TEXT PRIMARY KEY    -- UUID4
email       TEXT UNIQUE
name        TEXT
password    TEXT                -- bcrypt hash, never plaintext
tier        TEXT                -- 'free' | 'premium'
cohort      TEXT                -- 'FreshGraduate' | 'AgeAbove35Less50' | 'AgeAbove50'
created_at  DATETIME
last_login  DATETIME
```

---

### 2.3 ChromaDB — Vector Store & Journey Persistence

ChromaDB runs **embedded** (no server, no Docker). Data persists to disk at `./data/chromadb/`.

#### Collections Architecture

**`users_profiles`**
Stores the full intake profile as a document. Retrieved on every session start to seed the system prompt.
```
id:        user_id
document:  "Name: Waseem. Role: Senior Manager GPU Capacity. Target: Director of AI.
            Asset: Built QuotaMaster agentic system. Fear: Mostly How, not Why..."
metadata:  {user_id, cohort, tier, target_role, updated_at}
```

**`journeys`**
Every coaching session turn stored as a vector. Retrieved by semantic similarity to build context window for next session — so the AI "remembers" relevant past conversations.
```
id:        {user_id}_{session_id}_{turn_number}
document:  "User: What is my biggest gap? | Coach: Your gap is narrative, not work..."
metadata:  {user_id, session_id, role, timestamp, topic_tag}
```

**`star_stories`**
User's STAR stories stored and tagged by competency. Retrieved when coach needs relevant evidence.
```
id:        {user_id}_{story_slug}
document:  "PCDW Hardware + DB Upgrade. Situation: ... Task: ... Action: ... Result: ..."
metadata:  {user_id, competency, role_level, impact_score, created_at}
```

**`fears`**
Fear inventory — which fears are active, which have been reframed, progress over time.
```
id:        {user_id}_{fear_slug}
document:  "Fear: Moving target. Status: active. Reframe attempted: yes. Notes: ..."
metadata:  {user_id, fear_id, status, last_updated}
```

**`roadmap_tasks`**
Roadmap milestone progress per user.
```
id:        {user_id}_{task_slug}
document:  "Task: Rewrite top 3 STAR stories in Director language. Phase: 1. Done: true"
metadata:  {user_id, phase, done, completed_at}
```

---

### 2.4 Coach Engine — LLM Orchestration

The coach engine builds a **layered context** for each API call:

```
Layer 1: System prompt (role, methodology, coaching principles)
Layer 2: User profile (from ChromaDB users_profiles)
Layer 3: Relevant past sessions (top-k semantic search from journeys)
Layer 4: Relevant STAR stories (if coaching needs evidence)
Layer 5: Current conversation turn
```

This means the AI coach has access to the user's full history without sending everything every time — only the semantically relevant past turns are retrieved.

**Token budget per call (Haiku):**
```
System prompt:      ~800 tokens
User profile:       ~200 tokens
Past context (k=3): ~600 tokens
Current turn:       ~300 tokens
Response:           ~500 tokens
─────────────────────────────
Total per call:     ~2,400 tokens
Cost per call:      ~$0.0003 (Haiku pricing)
50 users × 20 msgs: ~$0.30/day
```

---

### 2.5 Memory Manager — Retrieval Strategy

```python
def get_relevant_context(user_id: str, current_query: str, k: int = 3):
    """
    Retrieve top-k semantically similar past coaching turns
    for this user, given the current query.
    """
    results = journeys_collection.query(
        query_texts=[current_query],
        where={"user_id": user_id},
        n_results=k
    )
    return results['documents'][0]
```

ChromaDB handles embedding generation internally using its default embedding function (sentence-transformers). No separate embedding API needed.

---

## 3. Data Flow — Full Session Lifecycle

```
1. USER ARRIVES
   └─▶ Home.py checks st.session_state["token"]
       ├─ Valid token → skip to step 3
       └─ No token   → Login / Register form

2. AUTHENTICATION
   └─▶ Login: verify bcrypt → issue JWT → store in session_state
       Register: hash password → insert SQLite → issue JWT

3. PROFILE LOAD
   └─▶ Fetch user profile from ChromaDB users_profiles
       ├─ Profile exists → populate session_state, go to Coach
       └─ No profile    → redirect to Profile intake form

4. PROFILE INTAKE (first time only)
   └─▶ User fills: cohort, current role, target role, asset, fear
       └─▶ Embed + store in ChromaDB users_profiles
           └─▶ Generate initial roadmap tasks in roadmap_tasks
               └─▶ Seed fear inventory in fears collection

5. COACHING SESSION
   └─▶ User sends message
       ├─▶ Memory Mgr: semantic search journeys for relevant past turns
       ├─▶ Prompt Builder: assemble layered context
       ├─▶ Haiku API call: generate coaching response
       ├─▶ Store turn in journeys collection
       └─▶ Render response in Streamlit chat

6. ROADMAP / FEARS UPDATE
   └─▶ User checks off task → update roadmap_tasks metadata
       User marks fear resolved → update fears metadata

7. SESSION END
   └─▶ All data persisted in ChromaDB / SQLite
       Next session picks up exactly where this left off
```

---

## 4. File Structure

```
careersignal/
├── Home.py                         # App entry point, login/register
├── pages/
│   ├── 1_Profile.py
│   ├── 2_Coach.py
│   ├── 3_Roadmap.py
│   ├── 4_Fears.py
│   ├── 5_STAR_Stories.py
│   └── 6_JD_Analyzer.py
├── core/
│   ├── __init__.py
│   ├── auth.py                     # JWT + bcrypt auth
│   ├── database.py                 # SQLite user management
│   ├── vector_store.py             # ChromaDB CRUD operations
│   ├── memory_manager.py           # Semantic retrieval logic
│   ├── coach_engine.py             # LLM orchestration
│   ├── prompt_builder.py           # Layered prompt assembly
│   └── roadmap.py                  # Roadmap + fear defaults
├── data/
│   ├── chromadb/                   # ChromaDB persistence (auto-created)
│   └── users.db                    # SQLite auth database (auto-created)
├── config/
│   └── settings.py                 # API keys, constants, tier config
├── requirements.txt
├── .env                            # API keys (never commit)
├── .gitignore
├── ARCHITECTURE.md
└── IMPLEMENTATION.md
```

---

## 5. API Keys Required

| Service | Key name | Where to get | Cost |
|---|---|---|---|
| Anthropic (Haiku) | `ANTHROPIC_API_KEY` | console.anthropic.com | ~$0.30/day for 50 users |
| None for ChromaDB | — | Embedded, no API | Free |
| None for SQLite | — | Built into Python | Free |

**Total external dependencies: 1 API key.**

---

## 6. Tier System

| Feature | Free | Premium ($49/mo) |
|---|---|---|
| AI coaching sessions | 10/month | Unlimited |
| Profile + roadmap | ✓ | ✓ |
| Fear inventory | ✓ | ✓ |
| STAR story builder | — | ✓ |
| Interview simulator | — | ✓ |
| JD gap analyzer | — | ✓ |
| Cohort community | — | ✓ |
| Journey memory (sessions) | 7 days | Unlimited |

Tier is stored in SQLite `users.tier`. Checked in each page with a `require_premium()` guard.

---

## 7. Local → Production Path

```
Phase 1 (Now):     Local Mac, SQLite + ChromaDB on disk, you + beta users via ngrok
Phase 2 (Month 2): Fly.io or Railway deployment, same stack, persistent volume for ChromaDB
Phase 3 (Month 4): Swap ChromaDB for Pinecone (managed), SQLite for Postgres, add Stripe for payments
Phase 4 (Month 6): Full SaaS — custom domain, email auth, cohort scheduling, Slack community
```

---

*Architecture version: 0.1 — MVP local deployment*
*Next review: when user count exceeds 50 or ChromaDB hits 1GB*
