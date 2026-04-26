# pages/3_Roadmap.py
import streamlit as st
from core.auth import require_login
from core.vector_store import get_user_tasks, save_task_progress
from core.roadmap import DEFAULT_ROADMAP

st.set_page_config(page_title="Roadmap — CareerSignal", layout="wide")

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]
tier    = payload["tier"]

st.markdown("## ◎ Your Roadmap")
st.markdown("*Your 18-month Director/VP AI transition plan. Check off milestones as you complete them.*")
st.divider()

# Load persisted progress
saved = get_user_tasks(user_id)

# Track any checkbox changes
changes: list[tuple[str, bool, int]] = []

for phase in DEFAULT_ROADMAP:
    phase_num   = phase["phase"]
    total_tasks = len(phase["tasks"])
    done_count  = sum(1 for t in phase["tasks"] if saved.get(t["slug"], False))

    with st.expander(
        f"**Phase {phase_num} — {phase['name']}** · {phase['period']} · {done_count}/{total_tasks} done",
        expanded=(phase_num == 1)
    ):
        st.markdown(f"*Goal: {phase['goal']}*")
        st.markdown("")

        for task in phase["tasks"]:
            slug        = task["slug"]
            is_premium  = task.get("is_premium", False)
            locked      = is_premium and tier != "premium"
            current_val = saved.get(slug, False)

            cols = st.columns([0.05, 0.75, 0.2])
            with cols[0]:
                if locked:
                    st.markdown("🔒")
                    new_val = current_val
                else:
                    new_val = st.checkbox(
                        label="",
                        value=current_val,
                        key=f"task_{slug}",
                        disabled=locked
                    )
                    if new_val != current_val:
                        changes.append((slug, new_val, phase_num))

            with cols[1]:
                label = task["text"]
                if locked:
                    label = f"~~{label}~~"
                st.markdown(label)

            with cols[2]:
                tag_color = {
                    "New": "🟢", "Portfolio": "🔵", "Signal": "🟡",
                    "Public": "🟠", "Network": "🟣", "Apply": "⚪",
                    "Governance": "🔵", "Interview": "🟤", "Leadership": "🟢",
                    "Thought Lead": "🟡", "VP Prep": "🔴", "People": "🟣",
                    "Vision": "🔵", "Market": "🟠",
                }.get(task["tag"], "⚪")
                badge = "⭐ Premium" if is_premium else f"{tag_color} {task['tag']}"
                st.markdown(badge)

# Persist changes immediately
for slug, done, phase_num in changes:
    save_task_progress(user_id, slug, done=done, phase=phase_num)

if changes:
    st.toast(f"Progress saved — {len(changes)} task(s) updated.", icon="✓")

# Overall progress bar
all_tasks = [t for phase in DEFAULT_ROADMAP for t in phase["tasks"]]
free_tasks = [t for t in all_tasks if not t.get("is_premium")]
done_free  = sum(1 for t in free_tasks if saved.get(t["slug"], False))

st.divider()
st.markdown(f"**Overall progress:** {done_free}/{len(free_tasks)} milestones complete")
st.progress(done_free / len(free_tasks) if free_tasks else 0)

if tier != "premium":
    st.info("⭐ Premium tasks unlock at the Premium tier — 8 additional milestones for Phases 3–5.")
