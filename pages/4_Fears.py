# pages/4_Fears.py
import streamlit as st
from core.auth import require_login
from core.vector_store import get_user_fears, save_fear_status
from core.roadmap import DEFAULT_FEARS
from core.styles import apply_styles, page_header

st.set_page_config(page_title="Fear Inventory — CareerSignal", layout="wide")
apply_styles()

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]

page_header("◎ Fear Inventory", "Name the fear precisely. A named fear can be reframed. A vague fear just loops.")
st.divider()

saved_statuses = get_user_fears(user_id)

STATUS_OPTIONS = ["active", "reframed", "resolved"]
STATUS_LABELS  = {"active": "🔴 Active", "reframed": "🟡 Reframing", "resolved": "🟢 Resolved"}

# Summary counts
counts = {s: 0 for s in STATUS_OPTIONS}
for slug in [f["slug"] for f in DEFAULT_FEARS]:
    counts[saved_statuses.get(slug, {}).get("status", "active")] += 1

c1, c2, c3 = st.columns(3)
c1.metric("Active fears",    counts["active"])
c2.metric("Being reframed",  counts["reframed"])
c3.metric("Resolved",        counts["resolved"])

st.markdown("")

for fear in DEFAULT_FEARS:
    slug       = fear["slug"]
    saved      = saved_statuses.get(slug, {})
    current    = saved.get("status", "active")
    saved_note = saved.get("notes", "")
    status_idx = STATUS_OPTIONS.index(current)

    with st.expander(
        f"{STATUS_LABELS[current]} — **{fear['title']}**",
        expanded=(current == "active")
    ):
        st.markdown(f"**The fear:** {fear['summary']}")
        st.markdown("")
        st.markdown(f"**Reframe:** {fear['reframe']}")
        st.markdown("")

        cols = st.columns([0.4, 0.6])
        with cols[0]:
            new_status = st.selectbox(
                "Status",
                options=STATUS_OPTIONS,
                index=status_idx,
                format_func=lambda s: STATUS_LABELS[s],
                key=f"status_{slug}"
            )
        with cols[1]:
            notes = st.text_input(
                "Your notes (optional)",
                value=saved_note,
                key=f"notes_{slug}",
                placeholder="What shifted for you?"
            )

        if st.button("Save", key=f"save_{slug}", type="secondary"):
            save_fear_status(user_id, slug, new_status, notes)
            st.toast(f"'{fear['title']}' updated to {STATUS_LABELS[new_status]}.", icon="✓")
            st.rerun()

st.divider()
if counts["resolved"] == len(DEFAULT_FEARS):
    st.success("All fears resolved. That is not the absence of fear — that is the work being done.")
else:
    remaining = counts["active"] + counts["reframed"]
    st.markdown(f"*{remaining} fear(s) still in progress. The goal is not zero fear — it's named fear with a reframe.*")
