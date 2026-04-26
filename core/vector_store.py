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
