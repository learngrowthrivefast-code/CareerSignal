# pages/2_Coach.py
import streamlit as st
import uuid
from core.auth import require_login
from core.vector_store import get_user_profile, get_recent_turns
from core.coach_engine import get_coaching_response
from core.database import increment_session_count
from core.styles import apply_styles, page_header
from config.settings import FREE_SESSION_LIMIT

st.set_page_config(page_title="AI Coach — CareerSignal", layout="wide")
apply_styles()

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
col1, col2 = st.columns([5, 1])
with col1:
    page_header(
        "◎ Your AI Coach",
        f"{meta.get('current_role', '')}  →  {meta.get('target_role', 'Director of AI')}"
    )
with col2:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    tier_color = "#6ee7b7" if tier == "premium" else "#a5b4fc"
    tier_label = "⭐ Premium" if tier == "premium" else "Free tier"
    st.markdown(f"""
    <div style="text-align:right; padding-top:8px;">
        <span style="background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.25);
                     border-radius:20px; padding:4px 12px; font-size:12px;
                     font-weight:600; color:{tier_color};">
            {tier_label}
        </span>
    </div>
    """, unsafe_allow_html=True)

# ── Prompt chips ──────────────────────────────────────────────────────────
st.markdown("<p style='font-size:13px; color:#94a3b8; font-weight:500; margin-bottom:8px;'>Quick prompts</p>",
            unsafe_allow_html=True)
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
        if st.button(prompt[:26]+"…" if len(prompt) > 26 else prompt,
                     key=f"chip_{i}", use_container_width=True):
            st.session_state["pending_message"] = prompt

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

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
