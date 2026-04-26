# core/coach_engine.py
import anthropic
from config.settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_TOKENS
from core.prompt_builder import build_system_prompt
from core.memory_manager import get_relevant_context
from core.vector_store import save_turn
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
    # 1–2. Retrieve profile + relevant past turns + STAR stories
    ctx = get_relevant_context(user_id, user_message)
    profile      = ctx["profile"]
    past_context = ctx["past_turns"]

    # 3. Build system prompt
    system_prompt = build_system_prompt(profile, past_context, ctx["star_stories"])

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
