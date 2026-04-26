# core/memory_manager.py
from core.vector_store import (
    get_user_profile,
    search_relevant_turns,
    get_user_stories,
)
from config.settings import MEMORY_CONTEXT_K


def get_relevant_context(user_id: str, current_query: str, k: int = MEMORY_CONTEXT_K) -> dict:
    """
    Assembles layered context for a coaching turn:
      - user profile document
      - top-k semantically relevant past turns
      - relevant STAR stories (if any)
    Returns a dict consumed by prompt_builder.
    """
    profile_data = get_user_profile(user_id)
    profile = profile_data["metadata"] if profile_data else {}

    past_turns = search_relevant_turns(user_id, current_query, k=k)

    stories = get_user_stories(user_id)
    relevant_stories = _filter_relevant_stories(stories, current_query)

    return {
        "profile":  profile,
        "past_turns": past_turns,
        "star_stories": relevant_stories,
    }


def _filter_relevant_stories(stories: list[dict], query: str) -> list[str]:
    """Return story documents whose competency or content matches the query keywords."""
    if not stories:
        return []
    query_lower = query.lower()
    keywords = {"star", "story", "situation", "evidence", "example",
                "leadership", "result", "impact", "achievement"}
    if not any(kw in query_lower for kw in keywords):
        return []
    return [s["document"] for s in stories[:2]]
