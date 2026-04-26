# pages/6_JD_Analyzer.py
import streamlit as st
import anthropic
from core.auth import require_login
from core.vector_store import get_user_profile, get_user_stories
from config.settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

st.set_page_config(page_title="JD Analyzer — CareerSignal", layout="wide")

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]
tier    = payload["tier"]

st.markdown("## ◎ JD Gap Analyzer")
st.markdown("*Paste a job description. Get your gap analysis and a tailored narrative.*")
st.divider()

if tier != "premium":
    st.warning("⭐ **Premium feature.** JD gap analysis is available on the Premium plan.")
    st.markdown("Upgrade to Premium to get a personalized gap analysis and interview narrative for any Director/VP AI role.")
    st.stop()

profile_data = get_user_profile(user_id)
if not profile_data:
    st.warning("Complete your profile first before running a JD analysis.")
    st.switch_page("pages/1_Profile.py")

profile = profile_data["metadata"]

jd_text = st.text_area(
    "Paste the job description here",
    height=300,
    placeholder="Copy and paste the full job description — title, requirements, responsibilities..."
)

if st.button("Analyze this JD", type="primary", disabled=not jd_text.strip()):
    stories = get_user_stories(user_id)
    story_block = ""
    if stories:
        story_block = "\n\nUSER'S STAR STORIES:\n" + "\n---\n".join(
            s["document"] for s in stories[:5]
        )

    system = f"""You are CareerSignal, an AI career coach specializing in Director/VP AI transitions.
Analyze job descriptions against the user's profile and return a structured gap analysis.

USER PROFILE:
- Name: {profile.get('name', '')}
- Current role: {profile.get('current_role', '')}
- Target role: {profile.get('target_role', '')}
- Biggest asset: {profile.get('biggest_asset', '')}
- Biggest fear/gap: {profile.get('biggest_fear', '')}
- Cohort: {profile.get('cohort', '')}
{story_block}

Output format (use exactly these headers):
## Match Score
X/10 — one sentence explanation

## Your Strongest Matches
3–5 bullet points: where your background directly matches this JD

## Real Gaps to Address
3–5 bullet points: honest, specific gaps — not generic. What's actually missing.

## Reframed Narrative
2–3 sentences: how this user should position themselves for THIS specific role,
reframing their background in the language this JD uses.

## 3 Actions Before Applying
Concrete, specific — not generic advice. What would move the needle for THIS JD."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    with st.spinner("Analyzing the JD against your profile..."):
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": f"Analyze this job description:\n\n{jd_text}"}]
        )

    analysis = response.content[0].text
    st.markdown(analysis)

    st.divider()
    st.markdown("*Take this analysis to your coach in the [Coach](pages/2_Coach.py) tab for a deeper conversation about this role.*")
