# CareerSignal — Implementation Guide

**Stack:** Python 3.11 · Streamlit · ChromaDB · Anthropic Haiku · JWT
**OS:** macOS Apple Silicon (M1/M2/M3)
**Time to first run:** ~20 minutes

---

## 1. Prerequisites & Local Setup

### Step 1 — Install Python 3.11 via Homebrew

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Verify
python3.11 --version
```

### Step 2 — Create Project & Virtual Environment

```bash
mkdir careersignal && cd careersignal

# Create virtual environment
python3.11 -m venv venv

# Activate it (you need to run this every time you open a new terminal)
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

### Step 3 — Install Dependencies

```bash
pip install streamlit==1.32.0 \
            anthropic==0.25.0 \
            chromadb==0.4.24 \
            bcrypt==4.1.2 \
            PyJWT==2.8.0 \
            python-dotenv==1.0.1 \
            uuid \
            pandas==2.2.0
```

Or create `requirements.txt` first (recommended):

```
streamlit==1.32.0
anthropic==0.25.0
chromadb==0.4.24
bcrypt==4.1.2
PyJWT==2.8.0
python-dotenv==1.0.1
pandas==2.2.0
```

```bash
pip install -r requirements.txt
```

### Step 4 — Environment Variables

Create `.env` in project root:

```bash
# .env — NEVER commit this file to git
ANTHROPIC_API_KEY=sk-ant-your-key-here
JWT_SECRET=your-random-secret-string-change-this-in-production
APP_ENV=development
```

Get your Anthropic API key at: **console.anthropic.com → API Keys**

Create `.gitignore`:

```
.env
data/
venv/
__pycache__/
*.pyc
.DS_Store
```

---

## 2. Core Module: `config/settings.py`

```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL   = "claude-haiku-4-5-20251001"  # Cheapest, fastest

# Auth
JWT_SECRET      = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM   = "HS256"
JWT_EXPIRY_HRS  = 24

# ChromaDB
CHROMA_PATH = "./data/chromadb"

# SQLite
SQLITE_PATH = "./data/users.db"

# Tiers
FREE_SESSION_LIMIT    = 10   # messages per month
PREMIUM_MONTHLY_PRICE = 49   # USD

# Coaching config
MEMORY_CONTEXT_K = 3    # how many past turns to retrieve
MAX_TOKENS       = 800  # per Haiku response

# Cohorts
COHORTS = {
    "FreshGraduate":     "Fresh Builder (20–35)",
    "AgeAbove35Less50":  "Bridge Builder (35–50)",
    "AgeAbove50":        "Navigator (50+)",
}

# Target roles
TARGET_ROLES = [
    "Director of AI",
    "VP of AI",
    "Director of AI Strategy",
    "Director of AI Programs",
    "Head of AI / ML",
    "Director of AI Governance",
    "VP of Engineering (AI)",
]
```

---

## 3. Core Module: `core/database.py`

```python
# core/database.py
import sqlite3
import uuid
from datetime import datetime
from config.settings import SQLITE_PATH
import os

def get_connection():
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    return sqlite3.connect(SQLITE_PATH, check_same_thread=False)

def init_db():
    """Create tables on first run."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    TEXT PRIMARY KEY,
            email      TEXT UNIQUE NOT NULL,
            name       TEXT NOT NULL,
            password   TEXT NOT NULL,
            tier       TEXT DEFAULT 'free',
            cohort     TEXT,
            created_at TEXT,
            last_login TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_counts (
            user_id    TEXT,
            month      TEXT,
            count      INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, month)
        )
    """)
    conn.commit()
    conn.close()

def create_user(email: str, name: str, hashed_password: str) -> str:
    """Insert new user. Returns user_id."""
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
            (user_id, email.lower(), name, hashed_password, 'free', None, now, now)
        )
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        raise ValueError("Email already registered.")
    finally:
        conn.close()

def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower(),)
    ).fetchone()
    conn.close()
    if not row:
        return None
    cols = ["user_id","email","name","password","tier","cohort","created_at","last_login"]
    return dict(zip(cols, row))

def update_last_login(user_id: str):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET last_login = ? WHERE user_id = ?",
        (datetime.utcnow().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

def update_user_cohort(user_id: str, cohort: str):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET cohort = ? WHERE user_id = ?",
        (cohort, user_id)
    )
    conn.commit()
    conn.close()

def increment_session_count(user_id: str) -> int:
    """Track monthly message count for free tier limits."""
    month = datetime.utcnow().strftime("%Y-%m")
    conn = get_connection()
    conn.execute("""
        INSERT INTO session_counts (user_id, month, count) VALUES (?,?,1)
        ON CONFLICT(user_id, month) DO UPDATE SET count = count + 1
    """, (user_id, month))
    conn.commit()
    count = conn.execute(
        "SELECT count FROM session_counts WHERE user_id=? AND month=?",
        (user_id, month)
    ).fetchone()[0]
    conn.close()
    return count
```

---

## 4. Core Module: `core/auth.py`

```python
# core/auth.py
import bcrypt
import jwt
from datetime import datetime, timedelta
from config.settings import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HRS

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(user_id: str, email: str, tier: str) -> str:
    payload = {
        "user_id": user_id,
        "email":   email,
        "tier":    tier,
        "exp":     datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HRS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict | None:
    """Returns payload dict or None if invalid/expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def require_login(session_state) -> dict | None:
    """
    Call at top of every page.
    Returns user payload or None (caller should st.stop() if None).
    """
    token = session_state.get("token")
    if not token:
        return None
    return decode_token(token)
```

---

## 5. Core Module: `core/vector_store.py`

```python
# core/vector_store.py
import chromadb
from chromadb.config import Settings
from datetime import datetime
import os
from config.settings import CHROMA_PATH

# ── CLIENT ────────────────────────────────────────────────────────────────
def get_client():
    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)

def get_collection(name: str):
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

# ── USER PROFILE ──────────────────────────────────────────────────────────
def save_user_profile(user_id: str, profile: dict):
    """
    profile keys: name, current_role, target_role, cohort,
                  biggest_asset, biggest_fear, tier
    """
    col = get_collection("user_profiles")
    doc = (
        f"Name: {profile.get('name')}. "
        f"Current role: {profile.get('current_role')}. "
        f"Target role: {profile.get('target_role')}. "
        f"Cohort: {profile.get('cohort')}. "
        f"Biggest career asset: {profile.get('biggest_asset')}. "
        f"Biggest fear or gap: {profile.get('biggest_fear')}. "
        f"Tier: {profile.get('tier', 'free')}."
    )
    col.upsert(
        ids=[user_id],
        documents=[doc],
        metadatas=[{**profile, "user_id": user_id, "updated_at": datetime.utcnow().isoformat()}]
    )

def get_user_profile(user_id: str) -> dict | None:
    col = get_collection("user_profiles")
    try:
        result = col.get(ids=[user_id])
        if result["ids"]:
            return {
                "document":  result["documents"][0],
                "metadata":  result["metadatas"][0]
            }
    except Exception:
        pass
    return None

# ── JOURNEY / CHAT HISTORY ────────────────────────────────────────────────
def save_turn(user_id: str, session_id: str, turn_num: int,
              role: str, content: str, topic_tag: str = "general"):
    col = get_collection("journeys")
    turn_id = f"{user_id}_{session_id}_{turn_num}"
    col.upsert(
        ids=[turn_id],
        documents=[f"{role.upper()}: {content}"],
        metadatas=[{
            "user_id":    user_id,
            "session_id": session_id,
            "turn_num":   turn_num,
            "role":       role,
            "topic_tag":  topic_tag,
            "timestamp":  datetime.utcnow().isoformat()
        }]
    )

def get_recent_turns(user_id: str, limit: int = 20) -> list[str]:
    """Get most recent turns for display in chat UI."""
    col = get_collection("journeys")
    results = col.get(
        where={"user_id": user_id},
        include=["documents", "metadatas"]
    )
    if not results["ids"]:
        return []
    # Sort by timestamp
    combined = sorted(
        zip(results["documents"], results["metadatas"]),
        key=lambda x: x[1].get("timestamp", ""),
        reverse=False
    )
    return [doc for doc, _ in combined[-limit:]]

def search_relevant_turns(user_id: str, query: str, k: int = 3) -> list[str]:
    """Semantic search — retrieve past turns relevant to current query."""
    col = get_collection("journeys")
    try:
        results = col.query(
            query_texts=[query],
            where={"user_id": user_id},
            n_results=k
        )
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []

# ── STAR STORIES ──────────────────────────────────────────────────────────
def save_star_story(user_id: str, story_slug: str, story: dict):
    """
    story keys: title, situation, task, action, result,
                competency, impact, role_level
    """
    col = get_collection("star_stories")
    doc = (
        f"STAR Story: {story.get('title')}. "
        f"Situation: {story.get('situation')}. "
        f"Task: {story.get('task')}. "
        f"Action: {story.get('action')}. "
        f"Result: {story.get('result')}."
    )
    col.upsert(
        ids=[f"{user_id}_{story_slug}"],
        documents=[doc],
        metadatas=[{**story, "user_id": user_id, "updated_at": datetime.utcnow().isoformat()}]
    )

def get_user_stories(user_id: str) -> list[dict]:
    col = get_collection("star_stories")
    results = col.get(where={"user_id": user_id}, include=["documents","metadatas"])
    if not results["ids"]:
        return []
    return [{"document": d, "metadata": m}
            for d, m in zip(results["documents"], results["metadatas"])]

# ── ROADMAP TASKS ─────────────────────────────────────────────────────────
def save_task_progress(user_id: str, task_slug: str, done: bool, phase: int):
    col = get_collection("roadmap_tasks")
    col.upsert(
        ids=[f"{user_id}_{task_slug}"],
        documents=[task_slug],
        metadatas=[{
            "user_id":      user_id,
            "task_slug":    task_slug,
            "phase":        phase,
            "done":         done,
            "completed_at": datetime.utcnow().isoformat() if done else ""
        }]
    )

def get_user_tasks(user_id: str) -> dict[str, bool]:
    """Returns {task_slug: done_bool}"""
    col = get_collection("roadmap_tasks")
    results = col.get(where={"user_id": user_id}, include=["metadatas"])
    if not results["ids"]:
        return {}
    return {m["task_slug"]: m["done"] for m in results["metadatas"]}

# ── FEARS ─────────────────────────────────────────────────────────────────
def save_fear_status(user_id: str, fear_slug: str, status: str, notes: str = ""):
    col = get_collection("fears")
    col.upsert(
        ids=[f"{user_id}_{fear_slug}"],
        documents=[f"Fear: {fear_slug}. Status: {status}. Notes: {notes}"],
        metadatas=[{
            "user_id":      user_id,
            "fear_slug":    fear_slug,
            "status":       status,
            "notes":        notes,
            "last_updated": datetime.utcnow().isoformat()
        }]
    )

def get_user_fears(user_id: str) -> dict[str, str]:
    """Returns {fear_slug: status}"""
    col = get_collection("fears")
    results = col.get(where={"user_id": user_id}, include=["metadatas"])
    if not results["ids"]:
        return {}
    return {m["fear_slug"]: m["status"] for m in results["metadatas"]}
```

---

## 6. Core Module: `core/prompt_builder.py`

```python
# core/prompt_builder.py
from config.settings import COHORTS

COACHING_METHODOLOGY = """
You are CareerSignal — a senior-level AI career coach specializing in helping
experienced IT professionals transition into Director and VP of AI roles.

Your coaching methodology:
- You are recruiter-calibrated: you know what Director/VP AI hiring committees look for
- You start from what people ALREADY HAVE and reframe it — never just listing gaps
- You name fears specifically and provide concrete reframes, not generic encouragement
- You distinguish How work (execution) from Why/What work (strategy/vision)
- The moving target of AI job requirements is NOT the real obstacle
- Developing judgment and pattern recognition IS the real work

The Four Permanent Director Questions (never change regardless of JD trends):
1. Can you make the right bets on which AI investments matter before it's obvious?
2. Can you translate between technical reality and business risk for executives?
3. Can you build and retain teams that execute through ambiguity?
4. Can you establish organizational trust in AI systems?

New Director/VP AI requirements in 2025-2026:
- Agentic AI oversight and governance frameworks
- EU AI Act compliance (enforcing Aug 2026 for high-risk systems)
- LLMOps and GenAI production operations
- Governance-as-enablement (not compliance-as-blocker)
- AI workforce enablement and change management at scale

Response style:
- Warm but direct. Honest about gaps without being discouraging.
- Use specific language. Vague encouragement is useless; specific reframes are valuable.
- When identifying a fear: name it specifically, say what's underneath it, give the concrete reframe.
- When giving action items: specific, time-bound, doable — not generic advice.
- Keep responses under 300 words unless the user asks for detail.
"""

def build_system_prompt(profile: dict, past_context: list[str]) -> str:
    cohort_name = COHORTS.get(profile.get("cohort", ""), "Unknown cohort")

    cohort_guidance = {
        "AgeAbove50": (
            "This is a Navigator (50+). Emphasize scar tissue advantage — they have lived through "
            "multiple full technology cycles. Their narrative: 'I've done this before — not with this "
            "technology, but with this kind of organizational challenge.' Reframe experience as "
            "cross-cycle judgment. Never suggest they lack relevance."
        ),
        "AgeAbove35Less50": (
            "This is a Bridge Builder (35-50). They speak both technical and executive languages. "
            "Their risk is waiting for permission to operate at a higher level. Push them to stop "
            "waiting and start generating strategic conversations proactively."
        ),
        "FreshGraduate": (
            "This is a Fresh Builder (20-35). First-mover governance play is key — find what nobody "
            "owns and own it. Portfolio over tenure. One senior mentor relationship is worth more than "
            "six certifications. They cannot compete on experience — they compete on speed and ownership."
        ),
    }.get(profile.get("cohort", ""), "Apply general Director/VP AI coaching principles.")

    past_ctx = ""
    if past_context:
        past_ctx = "\n\nRELEVANT PAST COACHING CONTEXT:\n" + "\n---\n".join(past_context)

    return f"""{COACHING_METHODOLOGY}

USER PROFILE:
- Name: {profile.get('name', 'the user')}
- Current role: {profile.get('current_role', 'not specified')}
- Target role: {profile.get('target_role', 'Director of AI')}
- Cohort: {cohort_name}
- Biggest career asset: {profile.get('biggest_asset', 'not specified')}
- Biggest fear or gap: {profile.get('biggest_fear', 'not specified')}
- Tier: {profile.get('tier', 'free')}

COHORT-SPECIFIC GUIDANCE:
{cohort_guidance}
{past_ctx}

Remember: this user's profile and history are above. Reference their specific situation.
Do not give generic advice. Connect every insight to what they have told you about themselves."""
```

---

## 7. Core Module: `core/coach_engine.py`

```python
# core/coach_engine.py
import anthropic
from config.settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_TOKENS
from core.prompt_builder import build_system_prompt
from core.vector_store import (
    get_user_profile, search_relevant_turns,
    save_turn, get_user_stories
)
import uuid

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def get_coaching_response(
    user_id: str,
    session_id: str,
    turn_num: int,
    user_message: str,
    conversation_history: list[dict]
) -> str:
    """
    Main coaching call. Assembles layered context and calls Haiku.
    Returns the assistant response string.
    """
    # 1. Load user profile
    profile_data = get_user_profile(user_id)
    profile = profile_data["metadata"] if profile_data else {}

    # 2. Retrieve semantically relevant past turns
    past_context = search_relevant_turns(user_id, user_message, k=3)

    # 3. Build system prompt
    system_prompt = build_system_prompt(profile, past_context)

    # 4. Build messages — last 6 turns for immediate context
    messages = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
    messages = messages + [{"role": "user", "content": user_message}]

    # 5. Call Haiku
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=messages
    )
    reply = response.content[0].text

    # 6. Persist both turns to ChromaDB
    save_turn(user_id, session_id, turn_num,
              "user", user_message, tag_topic(user_message))
    save_turn(user_id, session_id, turn_num + 1,
              "assistant", reply, tag_topic(reply))

    return reply

def tag_topic(text: str) -> str:
    """Simple keyword topic tagger for metadata."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["fear", "afraid", "worried", "anxiety"]):
        return "fears"
    if any(w in text_lower for w in ["roadmap", "plan", "timeline", "months"]):
        return "roadmap"
    if any(w in text_lower for w in ["star", "story", "situation", "result"]):
        return "star_stories"
    if any(w in text_lower for w in ["gap", "missing", "lack", "need"]):
        return "gaps"
    if any(w in text_lower for w in ["director", "vp", "title", "role"]):
        return "target_role"
    return "general"
```

---

## 8. Core Module: `core/roadmap.py`

```python
# core/roadmap.py

DEFAULT_ROADMAP = [
    {
        "phase": 1,
        "period": "Days 1–30",
        "name": "Foundation Sprint",
        "goal": "Reframe your narrative. Package what already exists.",
        "tasks": [
            {"slug": "rewrite_star_stories",
             "text": "Rewrite your top 3 STAR stories in Why/What language (not How)",
             "tag": "New", "is_premium": False},
            {"slug": "package_governance_artifacts",
             "text": "Package 2–3 governance artifacts from existing work as one-page briefs",
             "tag": "Portfolio", "is_premium": False},
            {"slug": "write_ai_pov",
             "text": "Write your personal AI point of view (1 page)",
             "tag": "New", "is_premium": False},
            {"slug": "identify_ownership_gap",
             "text": "Identify the one AI gap nobody owns in your current organization",
             "tag": "Signal", "is_premium": False},
        ]
    },
    {
        "phase": 2,
        "period": "Days 31–60",
        "name": "Visibility Build",
        "goal": "Create external signal. Start the conversation.",
        "tasks": [
            {"slug": "publish_linkedin_article",
             "text": "Publish your first LinkedIn article on AI in your specific domain",
             "tag": "Public", "is_premium": False},
            {"slug": "director_conversations",
             "text": "Have 3 conversations with current Directors or VPs in AI roles",
             "tag": "Network", "is_premium": False},
            {"slug": "apply_first_roles",
             "text": "Apply to 3–5 Director-level roles — treat as learning data",
             "tag": "Apply", "is_premium": False},
            {"slug": "regulatory_framework",
             "text": "Read one regulatory framework: NIST AI RMF or EU AI Act summary",
             "tag": "Governance", "is_premium": False},
        ]
    },
    {
        "phase": 3,
        "period": "Months 3–6",
        "name": "Evidence Accumulation",
        "goal": "Build the portfolio. Create the interview-ready narrative.",
        "tasks": [
            {"slug": "first_director_interview",
             "text": "Complete first Director-level interview — debrief regardless of outcome",
             "tag": "Interview", "is_premium": False},
            {"slug": "cross_functional_initiative",
             "text": "Own one cross-functional AI initiative in current role",
             "tag": "Leadership", "is_premium": False},
            {"slug": "monthly_articles",
             "text": "Publish one AI leadership article per month",
             "tag": "Thought Lead", "is_premium": False},
            {"slug": "product_case_study",
             "text": "Document your AI product/project as a formal case study",
             "tag": "Portfolio", "is_premium": True},
        ]
    },
    {
        "phase": 4,
        "period": "Months 7–12",
        "name": "The Title Pursuit",
        "goal": "Close the role. Negotiate the level.",
        "tasks": [
            {"slug": "four_permanent_answers",
             "text": "Refine your four permanent Director answers with story evidence",
             "tag": "Interview", "is_premium": False},
            {"slug": "director_network",
             "text": "Build a network of 10+ people at Director/VP AI level",
             "tag": "Network", "is_premium": False},
            {"slug": "apply_ten_roles",
             "text": "Apply to 10+ roles — filter for IC-to-Director pathways",
             "tag": "Apply", "is_premium": False},
            {"slug": "board_communication",
             "text": "Practice board-level AI communication: consequence → mechanism → recommendation",
             "tag": "New Skill", "is_premium": True},
        ]
    },
    {
        "phase": 5,
        "period": "Months 12–18",
        "name": "Director → VP Signal",
        "goal": "Once in the Director role: build toward VP trajectory.",
        "tasks": [
            {"slug": "governance_framework_90days",
             "text": "Establish AI governance framework in first 90 days in role",
             "tag": "VP Prep", "is_premium": True},
            {"slug": "leadership_bench",
             "text": "Identify and develop the next Senior Manager on your team",
             "tag": "People", "is_premium": True},
            {"slug": "three_year_vision",
             "text": "Define a 3-year AI vision for your function — present to C-suite",
             "tag": "Vision", "is_premium": True},
            {"slug": "external_thought_leadership",
             "text": "Establish external AI thought leadership: speaking, writing, advising",
             "tag": "Market", "is_premium": True},
        ]
    }
]

DEFAULT_FEARS = [
    {"slug": "moving_target",
     "title": "The Moving Target",
     "summary": "By the time I'm ready, the requirements will change again.",
     "reframe": "You are not preparing to know AI. You are preparing to lead through it. Pattern recognition is more valuable than any specific skill list."},
    {"slug": "imposter_syndrome",
     "title": "Imposter Syndrome",
     "summary": "In the interview or first board meeting, they'll realize I'm not the real thing.",
     "reframe": "Impostors use vague language. You have chapter and verse — specific, verified, quantified stories. Specificity is credibility."},
    {"slug": "age_relevance",
     "title": "Age & Relevance",
     "summary": "Am I too old or too early for this transition?",
     "reframe": "Your unfair advantage is scar tissue. You have seen what happens when organizations fall in love with a technology before building the governance for it."},
    {"slug": "how_identity",
     "title": "The How Identity Crisis",
     "summary": "If I stop being the technical expert, who am I?",
     "reframe": "The Director does not need to be the most technical person in the room. They need to ask the right questions of technical people. That is a more valuable skill."},
    {"slug": "no_reports",
     "title": "No Direct Reports",
     "summary": "Every Director JD asks for people management. I don't have formal reports.",
     "reframe": "Target Director of AI Strategy or Director of AI Programs first. These are IC-to-director pathways. Once you have the title, people follow the role."},
    {"slug": "governance_overwhelm",
     "title": "Governance Overwhelm",
     "summary": "I can't learn law and regulation on top of everything else.",
     "reframe": "You need to know enough to ask the right questions of lawyers. Read NIST AI RMF. One page on EU AI Act high-risk systems. That is enough to lead."},
    {"slug": "comparison_trap",
     "title": "The Comparison Trap",
     "summary": "Others on LinkedIn are so much further ahead.",
     "reframe": "LinkedIn shows finished products, not work in progress. The people posting VP titles right now often built that role from scratch with less experience than you have."},
]
```

---

## 9. Main App: `Home.py`

```python
# Home.py — App entry point
import streamlit as st
from core.auth import hash_password, verify_password, create_token, decode_token
from core.database import init_db, create_user, get_user_by_email, update_last_login

st.set_page_config(
    page_title="CareerSignal",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB on first run
init_db()

# ── Session check ──────────────────────────────────────────────────────────
if "token" in st.session_state and st.session_state["token"]:
    payload = decode_token(st.session_state["token"])
    if payload:
        st.switch_page("pages/2_Coach.py")

# ── UI ─────────────────────────────────────────────────────────────────────
st.markdown("## ◎ CareerSignal")
st.markdown("*AI-powered career coaching for IT professionals targeting Director and VP of AI roles.*")
st.divider()

tab1, tab2 = st.tabs(["Sign In", "Create Account"])

with tab1:
    st.subheader("Welcome back")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Sign In", type="primary", use_container_width=True):
        user = get_user_by_email(email)
        if user and verify_password(password, user["password"]):
            token = create_token(user["user_id"], user["email"], user["tier"])
            st.session_state["token"]   = token
            st.session_state["user_id"] = user["user_id"]
            st.session_state["name"]    = user["name"]
            st.session_state["tier"]    = user["tier"]
            update_last_login(user["user_id"])
            st.success("Signed in! Redirecting...")
            st.switch_page("pages/2_Coach.py")
        else:
            st.error("Invalid email or password.")

with tab2:
    st.subheader("Create your account")
    name     = st.text_input("Full name", key="reg_name")
    email_r  = st.text_input("Email", key="reg_email")
    pass_r   = st.text_input("Password (min 8 chars)", type="password", key="reg_pass")
    pass_r2  = st.text_input("Confirm password", type="password", key="reg_pass2")

    if st.button("Create Account", type="primary", use_container_width=True):
        if len(pass_r) < 8:
            st.error("Password must be at least 8 characters.")
        elif pass_r != pass_r2:
            st.error("Passwords do not match.")
        elif not name or not email_r:
            st.error("Please fill in all fields.")
        else:
            try:
                hashed = hash_password(pass_r)
                user_id = create_user(email_r, name, hashed)
                token = create_token(user_id, email_r, "free")
                st.session_state["token"]   = token
                st.session_state["user_id"] = user_id
                st.session_state["name"]    = name
                st.session_state["tier"]    = "free"
                st.success("Account created! Setting up your profile...")
                st.switch_page("pages/1_Profile.py")
            except ValueError as e:
                st.error(str(e))
```

---

## 10. Page: `pages/1_Profile.py`

```python
# pages/1_Profile.py
import streamlit as st
from core.auth import require_login
from core.vector_store import save_user_profile, get_user_profile
from core.database import update_user_cohort
from core.roadmap import DEFAULT_ROADMAP, DEFAULT_FEARS
from core.vector_store import save_task_progress, save_fear_status
from config.settings import COHORTS, TARGET_ROLES

st.set_page_config(page_title="My Profile — CareerSignal", layout="wide")

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]
existing = get_user_profile(user_id)
meta = existing["metadata"] if existing else {}

st.markdown("## ◎ My Profile")
st.markdown("*Complete this once. CareerSignal remembers and refines over time.*")
st.divider()

with st.form("profile_form"):
    cohort = st.selectbox(
        "Which cohort are you?",
        options=list(COHORTS.keys()),
        format_func=lambda k: COHORTS[k],
        index=list(COHORTS.keys()).index(meta.get("cohort", "AgeAbove50"))
              if meta.get("cohort") in COHORTS else 0
    )
    current_role = st.text_input(
        "Current role / title",
        value=meta.get("current_role", "")
    )
    target_role = st.selectbox(
        "Target role",
        options=TARGET_ROLES,
        index=TARGET_ROLES.index(meta.get("target_role", "Director of AI"))
              if meta.get("target_role") in TARGET_ROLES else 0
    )
    biggest_asset = st.text_area(
        "Your biggest career asset (be specific — numbers, scale, outcomes)",
        value=meta.get("biggest_asset", ""),
        height=120
    )
    biggest_fear = st.text_area(
        "Your biggest fear or perceived gap for reaching your target role",
        value=meta.get("biggest_fear", ""),
        height=100
    )
    submitted = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

if submitted:
    profile = {
        "name":         st.session_state.get("name", ""),
        "cohort":       cohort,
        "current_role": current_role,
        "target_role":  target_role,
        "biggest_asset": biggest_asset,
        "biggest_fear":  biggest_fear,
        "tier":          st.session_state.get("tier", "free"),
        "user_id":       user_id,
    }
    save_user_profile(user_id, profile)
    update_user_cohort(user_id, cohort)

    # Seed roadmap tasks if first time
    for phase in DEFAULT_ROADMAP:
        for task in phase["tasks"]:
            save_task_progress(user_id, task["slug"], done=False, phase=phase["phase"])

    # Seed fears
    for fear in DEFAULT_FEARS:
        save_fear_status(user_id, fear["slug"], status="active")

    st.success("Profile saved! Your coaching journey begins.")
    st.switch_page("pages/2_Coach.py")
```

---

## 11. Page: `pages/2_Coach.py`

```python
# pages/2_Coach.py
import streamlit as st
import uuid
from core.auth import require_login
from core.vector_store import get_user_profile, get_recent_turns
from core.coach_engine import get_coaching_response
from core.database import increment_session_count
from config.settings import FREE_SESSION_LIMIT

st.set_page_config(page_title="AI Coach — CareerSignal", layout="wide")

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]
tier    = payload["tier"]

# Initialize session
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []
if "turn_num" not in st.session_state:
    st.session_state["turn_num"] = 0

profile_data = get_user_profile(user_id)
if not profile_data:
    st.warning("Please complete your profile first.")
    st.switch_page("pages/1_Profile.py")

meta = profile_data["metadata"]

# ── Header ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f"## ◎ Your AI Coach")
    st.markdown(f"*{meta.get('current_role', '')} → {meta.get('target_role', 'Director of AI')}*")
with col2:
    st.markdown(f"**Tier:** {tier.capitalize()}")
    if tier == "free":
        st.markdown(f"*Sessions this month counted*")

st.divider()

# ── Prompt chips ──────────────────────────────────────────────────────────
st.markdown("**Quick prompts:**")
chips = st.columns(5)
chip_prompts = [
    "What is my biggest gap right now?",
    "Reframe my experience in Director language",
    "Name my specific fears",
    "Give me my 90-day action plan",
    "What new AI skills do Director roles require?"
]
for i, (col, prompt) in enumerate(zip(chips, chip_prompts)):
    with col:
        if st.button(prompt[:28]+"…" if len(prompt)>28 else prompt,
                     key=f"chip_{i}", use_container_width=True):
            st.session_state["pending_message"] = prompt

# ── Chat history ──────────────────────────────────────────────────────────
for msg in st.session_state["conversation"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────
pending = st.session_state.pop("pending_message", None)
user_input = st.chat_input("Ask your coach anything...") or pending

if user_input:
    # Free tier limit check
    if tier == "free":
        count = increment_session_count(user_id)
        if count > FREE_SESSION_LIMIT:
            st.error(f"You've reached your {FREE_SESSION_LIMIT} free messages this month. Upgrade to Premium for unlimited coaching.")
            st.stop()

    # Show user message
    st.session_state["conversation"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get coaching response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = get_coaching_response(
                user_id=user_id,
                session_id=st.session_state["session_id"],
                turn_num=st.session_state["turn_num"],
                user_message=user_input,
                conversation_history=st.session_state["conversation"][:-1]
            )
        st.markdown(reply)
        st.session_state["conversation"].append({"role": "assistant", "content": reply})
        st.session_state["turn_num"] += 2
```

---

## 12. Running the App

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Make sure .env has your API key
cat .env  # should show ANTHROPIC_API_KEY=sk-ant-...

# 3. Run
streamlit run Home.py

# App opens at: http://localhost:8501
```

**Sharing with 50 newsletter users (no deployment needed yet):**

```bash
# Install ngrok
brew install ngrok

# Sign up at ngrok.com and get your auth token, then:
ngrok config add-authtoken YOUR_NGROK_TOKEN

# In one terminal: run the app
streamlit run Home.py

# In another terminal: expose it publicly
ngrok http 8501

# Share the ngrok URL with your newsletter audience
# e.g. https://abc123.ngrok.io
```

---

## 13. Cost Estimate (Haiku)

| Scenario | Tokens/day | Cost/day |
|---|---|---|
| You alone (testing) | ~5,000 | ~$0.001 |
| 10 active users | ~50,000 | ~$0.01 |
| 50 active users | ~250,000 | ~$0.05 |
| 50 power users | ~1,000,000 | ~$0.20 |

**Haiku pricing:** ~$0.25 per million input tokens, ~$1.25 per million output tokens.
**Monthly estimate for 50 newsletter users:** **under $10/month.**

---

## 14. Next Steps After MVP

1. **Add Stripe** for Premium tier — `stripe` Python library, webhook to update `users.tier`
2. **Deploy to Fly.io** — one `fly.toml` config, persistent volume for ChromaDB data
3. **Add email verification** — `sendgrid` library for signup confirmation
4. **Add STAR Story Builder page** — `pages/5_STAR_Stories.py` with the reframe engine
5. **Add Interview Simulator** — role-play mode with scoring rubric per answer
6. **Swap ChromaDB → Pinecone** when data exceeds 1GB or you need multi-server

---

*Implementation version: 0.1 — Local MVP*
*Estimated build time from scratch: 4–6 hours*
*Next review: when user count exceeds 50*
