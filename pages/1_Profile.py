# pages/1_Profile.py
import streamlit as st
from core.auth import require_login
from core.vector_store import save_user_profile, get_user_profile
from core.database import update_user_cohort
from core.roadmap import DEFAULT_ROADMAP, DEFAULT_FEARS
from core.vector_store import save_task_progress, save_fear_status
from core.styles import apply_styles, page_header
from config.settings import COHORTS, TARGET_ROLES

st.set_page_config(page_title="My Profile — CareerSignal", layout="wide")
apply_styles()

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]
existing = get_user_profile(user_id)
meta = existing["metadata"] if existing else {}

page_header("◎ My Profile", "Complete this once. CareerSignal remembers and refines over time.")
st.divider()

with st.form("profile_form"):
    st.markdown("**Which age group are you in?**")
    st.caption("We use this to tailor your coaching — each stage of a career has different leverage points.")
    cohort = st.selectbox(
        "Age group",
        options=list(COHORTS.keys()),
        format_func=lambda k: COHORTS[k],
        index=list(COHORTS.keys()).index(meta.get("cohort", "AgeAbove50"))
              if meta.get("cohort") in COHORTS else 0,
        label_visibility="collapsed"
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
