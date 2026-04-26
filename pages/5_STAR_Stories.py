# pages/5_STAR_Stories.py
import streamlit as st
import re
from core.auth import require_login
from core.vector_store import get_user_stories, save_star_story

st.set_page_config(page_title="STAR Stories — CareerSignal", layout="wide")

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]
tier    = payload["tier"]

st.markdown("## ◎ STAR Story Bank")
st.markdown("*Your interview evidence vault. Situation → Task → Action → Result.*")
st.divider()

if tier != "premium":
    st.warning("⭐ **Premium feature.** STAR story bank is available on the Premium plan.")
    st.markdown("Upgrade to Premium to build your interview evidence vault and let your coach reference your stories in every session.")
    st.stop()

COMPETENCIES = [
    "Strategic Vision", "AI Leadership", "Stakeholder Management",
    "Team Building", "Technical Judgment", "Change Management",
    "Governance & Risk", "Cross-functional Influence", "P&L / Business Impact",
    "Crisis / Ambiguity", "Product Thinking", "Executive Communication",
]

# ── Existing stories ───────────────────────────────────────────────────────
stories = get_user_stories(user_id)

if stories:
    st.markdown(f"### Your stories ({len(stories)})")
    for item in stories:
        meta = item["metadata"]
        title       = meta.get("title", "Untitled")
        competency  = meta.get("competency", "")
        impact      = meta.get("impact", "")
        with st.expander(f"**{title}** · {competency}"):
            st.markdown(f"**Situation:** {meta.get('situation', '')}")
            st.markdown(f"**Task:** {meta.get('task', '')}")
            st.markdown(f"**Action:** {meta.get('action', '')}")
            st.markdown(f"**Result:** {meta.get('result', '')}")
            if impact:
                st.markdown(f"**Impact / metric:** {impact}")
else:
    st.info("No stories yet. Add your first STAR story below — start with your highest-impact achievement.")

st.divider()

# ── Add new story ──────────────────────────────────────────────────────────
st.markdown("### Add a new story")

with st.form("star_form", clear_on_submit=True):
    title = st.text_input(
        "Story title (short, memorable)",
        placeholder="e.g. GPU Capacity System — 47% cost reduction"
    )
    competency = st.selectbox("Primary competency this story demonstrates", COMPETENCIES)

    col1, col2 = st.columns(2)
    with col1:
        situation = st.text_area(
            "Situation — what was the context and problem?",
            height=120,
            placeholder="What was the business challenge, and why did it matter?"
        )
        action = st.text_area(
            "Action — what did YOU specifically do?",
            height=120,
            placeholder="Use 'I' not 'we'. Be specific about your decisions."
        )
    with col2:
        task = st.text_area(
            "Task — what was your specific responsibility?",
            height=120,
            placeholder="What were you accountable for delivering?"
        )
        result = st.text_area(
            "Result — what was the measurable outcome?",
            height=120,
            placeholder="Numbers, percentages, time saved, revenue, risk avoided..."
        )

    impact = st.text_input(
        "One-line impact metric (optional)",
        placeholder="e.g. $2.1M annual savings, 40% faster deployment"
    )

    submitted = st.form_submit_button("Save Story", type="primary", use_container_width=True)

if submitted:
    if not title or not situation or not task or not action or not result:
        st.error("Please fill in all four STAR fields and a title.")
    else:
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:50]
        save_star_story(user_id, slug, {
            "title":      title,
            "competency": competency,
            "situation":  situation,
            "task":       task,
            "action":     action,
            "result":     result,
            "impact":     impact,
        })
        st.success(f"Story saved: '{title}'. Your coach can now reference this in sessions.")
        st.rerun()
