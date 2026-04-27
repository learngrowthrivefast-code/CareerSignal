# pages/7_Interview_Prep.py
import streamlit as st
import anthropic
from core.auth import require_login
from core.vector_store import (
    get_user_profile, get_user_stories,
    save_interview_readiness, get_interview_readiness
)
from core.styles import apply_styles, page_header
from config.settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

st.set_page_config(page_title="Interview Prep — CareerSignal", layout="wide")
apply_styles()

payload = require_login(st.session_state)
if not payload:
    st.warning("Please sign in first.")
    st.switch_page("Home.py")

user_id = payload["user_id"]

profile_data = get_user_profile(user_id)
if not profile_data:
    st.warning("Complete your profile first.")
    st.switch_page("pages/1_Profile.py")

profile = profile_data["metadata"]
target_role = profile.get("target_role", "Director of AI")
current_role = profile.get("current_role", "your current role")
name = profile.get("name", "")

# ── Round definitions ──────────────────────────────────────────────────────
ROUNDS = [
    {
        "id": "recruiter",
        "label": "Round 1 · Recruiter",
        "title": "Recruiter Screening",
        "duration": "20–30 min · Phone or video",
        "purpose": (
            "A qualification gate, not an evaluation. The recruiter is checking: "
            "are you worth the hiring manager's time? They are scanning for red flags, "
            "not depth. Pass this by being crisp, credible, and clearly motivated."
        ),
        "evaluating": [
            "Does your background match the headline requirements?",
            "Are comp expectations in the right range?",
            "Can you articulate why this role and this company — not generic ambition?",
            "Are there any obvious disqualifiers (wrong level, wrong geography, wrong visa status)?",
        ],
        "your_objectives": [
            "Confirm you meet the headline criteria without over-explaining",
            "Get their comp range before giving yours",
            "Plant one specific hook the HM will want to pull on",
            "Ask what a strong candidate looks like to them",
        ],
        "questions": [
            ("Walk me through your background in 2 minutes.",
             "Lead with your current scope, your biggest AI outcome, and why this role is the next logical step. Under 2 minutes. No life story."),
            ("Why are you interested in this role?",
             "Be specific to the company and role — not generic AI leadership ambition. Name something about their AI trajectory that you've actually researched."),
            ("What are your comp expectations?",
             "Ask for their range first: 'I want to make sure we're aligned — what's the budgeted range for this role?' Then anchor at the top of their range."),
            ("Are you interviewing elsewhere?",
             "Yes, at a similar level. You don't need to disclose where. This creates urgency without desperation."),
            ("What's your current notice period?",
             "State it factually. If negotiable, say so. Do not promise what you can't deliver."),
            ("Why are you leaving your current role?",
             "Frame it as moving toward, not away from. 'I've built X and want to take that to the next level in a role where I own the full AI strategy.'"),
        ],
        "watch_out": (
            "Do not give your comp number first. Do not over-explain your background. "
            "Do not say 'I'm very passionate about AI' — everyone says that. Be specific."
        ),
    },
    {
        "id": "hiring_manager",
        "label": "Round 2 · Hiring Manager",
        "title": "Hiring Manager Screening",
        "duration": "45–60 min · Video or in person",
        "purpose": (
            "This is the real first interview. The HM is deciding whether they want to "
            "work with you and whether you can operate at the level the role demands. "
            "They are not testing knowledge — they are testing judgment and leadership instinct."
        ),
        "evaluating": [
            "Does this person think at the right altitude — strategic, not just tactical?",
            "Can they translate between technical and business language?",
            "Do they have opinions? A point of view? Or do they just agree?",
            "Would I want this person in a room with my executives?",
            "Do they ask good questions — not just answer them?",
        ],
        "your_objectives": [
            "Demonstrate you think at the Why/What level, not just the How",
            "Share one specific, non-obvious opinion about AI in their industry",
            "Ask about the real problem the role is solving — not the job description",
            "Find out who you'd be working with and what success looks like in 90 days",
        ],
        "questions": [
            ("Tell me about your leadership philosophy.",
             "Anchor on judgment, not process. 'I hire for curiosity and accountability, not credentials. My job is to set the direction clearly enough that my team can make good decisions without me in the room.'"),
            ("What's your biggest career accomplishment?",
             "Use your strongest STAR story. Make it specific — numbers, scale, org impact. End with what it means for the next level, not just what you did."),
            ("How do you stay current in AI?",
             "Do not list newsletters. Describe one specific way you've changed your practice or thinking in the last 6 months because of something you learned. Specific > comprehensive."),
            ("What's your AI strategy philosophy?",
             "Lead with a specific point of view. 'The biggest mistake organizations make is optimizing for AI adoption before establishing governance.' Have a stance."),
            ("Describe a time you had to push back on a stakeholder.",
             "Show that you do it respectfully but without retreating. The HM wants to know you won't just say yes to everything."),
            ("Where do you see AI in your industry in 3 years?",
             "Give a specific, calibrated prediction — not a generic 'AI will transform everything.' Show pattern recognition from past tech cycles."),
            ("What questions do you have for me?",
             "Ask: 'What does success look like in the first 90 days?' and 'What's the biggest unsolved problem in your AI function right now?' — these show you're thinking about the job, not just getting it."),
        ],
        "watch_out": (
            "Do not be generic. Do not say 'I'm a strong communicator' — show it. "
            "Do not over-use the word 'passionate.' Every candidate is passionate. "
            "Ask at least 2 substantive questions — silence at the end reads as disinterest."
        ),
    },
    {
        "id": "technical_domain",
        "label": "Round 3 · Domain & Technical",
        "title": "Technical / Domain Screening",
        "duration": "60 min · Panel or specialist",
        "purpose": (
            "A domain-depth check. They are not testing whether you can code — "
            "they are testing whether your technical instincts are calibrated. "
            "Can you ask the right questions of engineers? Can you evaluate trade-offs? "
            "Do you know what you don't know?"
        ),
        "evaluating": [
            "Is their technical vocabulary current and accurate?",
            "Can they evaluate ML/AI system trade-offs at the architecture level?",
            "Do they understand governance, risk, and compliance in AI systems?",
            "Are they aware of what they don't know, or do they bluff?",
            "Can they bridge from technical reality to business consequence?",
        ],
        "your_objectives": [
            "Demonstrate fluency, not exhaustive knowledge",
            "Show you can evaluate technical claims, not just repeat them",
            "Acknowledge limits honestly — it reads as confidence, not weakness",
            "Connect every technical topic to organizational or business impact",
        ],
        "questions": [
            ("Walk us through how you'd evaluate an LLM for production use.",
             "Cover: fit-for-purpose (not best-in-class), latency/cost trade-offs, evaluation framework, monitoring in production, and governance requirements. Show you think beyond accuracy metrics."),
            ("How do you approach AI governance and risk management?",
             "Reference NIST AI RMF or EU AI Act. Frame governance as enablement, not compliance-as-blocker. 'The governance framework is what lets us move fast safely.'"),
            ("Describe your experience with agentic AI systems.",
             "If you have direct experience, lead with it. If not: 'I've overseen agentic implementations and the key risk surface is tool use permissions and human-in-the-loop design.' Show architectural awareness."),
            ("What's your approach to AI model evaluation and monitoring?",
             "Cover: offline evaluation (benchmarks, human eval), online monitoring (distribution shift, hallucination rates, latency), and feedback loops. Show you think about the full lifecycle."),
            ("How do you make build vs. buy decisions for AI capabilities?",
             "Framework: strategic differentiation (build), commodity capability (buy), data moat (build). Show you connect the decision to business strategy, not just technical preference."),
            ("What's your take on the EU AI Act and its implications?",
             "High-risk system categories, August 2026 enforcement. Translate to: 'As a Director, my job is to know which of our systems fall in scope and have the governance process in place before the deadline.'"),
            ("How have you handled a failing AI project?",
             "Show intellectual honesty. What was the early signal? What did you do? What would you do differently? Failure fluency signals leadership maturity."),
        ],
        "watch_out": (
            "Do not bluff on technical depth — specialists will catch it. "
            "Say 'I don't know the details of that, but here's how I'd evaluate it' — "
            "that reads as leadership maturity. Overconfidence on technical specifics is a red flag at the Director level."
        ),
    },
    {
        "id": "behavioral",
        "label": "Round 4 · Behavioral",
        "title": "Behavioral / Leadership Screening",
        "duration": "60 min · HR, panel, or skip-level",
        "purpose": (
            "STAR-format evidence gathering. They are building a pattern from your past "
            "to predict your future behavior. Every answer needs a specific story — "
            "not what you would do, but what you did."
        ),
        "evaluating": [
            "Does this person's behavior under pressure match what they claim to value?",
            "Can they lead through ambiguity without needing a playbook?",
            "Do they build and retain strong teams?",
            "How do they handle conflict — with peers, with executives, with their own team?",
            "Are their stories specific and verifiable, or vague and generic?",
        ],
        "your_objectives": [
            "Have 5–6 strong STAR stories ready — each usable across multiple questions",
            "Make every story specific: numbers, names (if appropriate), timeframes, outcomes",
            "Show range: not all stories from the same project or the same type of challenge",
            "End each story with the permanent lesson, not just the result",
        ],
        "questions": [
            ("Tell me about a time you led through significant ambiguity.",
             "Show: how you established enough clarity to move, how you kept the team aligned without a complete picture, and what you learned about leading when the destination isn't fully visible."),
            ("Describe a time you had to influence without authority.",
             "Cross-functional, no direct control. What was your influence strategy? What did you trade, align, or build to get commitment? Show lateral leadership."),
            ("Tell me about a difficult people decision you had to make.",
             "Performance management, restructuring, a misaligned hire. Show that you made the call, made it with humanity, and learned from it. Avoid both ruthlessness and avoidance."),
            ("Give me an example of when you failed and what you did.",
             "Name the failure clearly. Show what you did in response. Show what changed in your practice afterward. Failure ownership at this level signals psychological safety for the team you'd lead."),
            ("Tell me about a time you had to change direction mid-project.",
             "Show: what triggered the pivot, how you got stakeholder alignment, how you maintained team morale through the change. Adaptability under accountability."),
            ("Describe how you've built and developed talent.",
             "Specific example: someone you spotted, developed, and promoted or placed. Show that you think about team capability as a strategic asset, not just a reporting structure."),
            ("Tell me about a time you drove organizational change.",
             "Not just a project — a change in how the organization thinks or operates. Show that you understand change management as a discipline, not just an announcement."),
        ],
        "watch_out": (
            "Vague answers kill you here. 'We worked together as a team' is not an answer. "
            "'I' — not 'we.' Be specific about YOUR role, YOUR decision, YOUR outcome. "
            "Quantify wherever possible. Interviewers are trained to notice when you switch from 'I' to 'we' — it signals you're inflating your contribution."
        ),
    },
    {
        "id": "negotiation",
        "label": "Final · Negotiation",
        "title": "Offer Negotiation",
        "duration": "Ongoing — 1 to 3 conversations",
        "purpose": (
            "Not a test — a business negotiation. They want you. Now it's about closing "
            "the gap between what they've budgeted and what you're worth. "
            "The goal is not to win. The goal is to reach an agreement both sides "
            "feel good about, so you start the role with goodwill, not resentment."
        ),
        "evaluating": [
            "This round is not evaluation — it is alignment",
            "They are checking: is this person reasonable to work with?",
            "Are they asking for things that signal misaligned expectations?",
            "Will they accept an offer that works for both sides?",
        ],
        "your_objectives": [
            "Never accept the first offer — counter at least once",
            "Negotiate the full package: base, bonus, equity, title, remote policy, start date",
            "Establish 90-day success criteria and 12-month growth expectations in writing",
            "Get clarity on promotion timeline and what the path to VP looks like",
        ],
        "questions": [
            ("The offer is X. Is that in range for you?",
             "Never say yes or no immediately. 'I'm excited about the role. I'd like to take 24–48 hours to review the full package and come back to you.' Then counter 10–15% above the offer. The worst they can say is no."),
            ("What are your comp expectations?",
             "If you haven't given a number yet: 'Based on my research and the scope of this role, I'm targeting $X–$Y. I'm flexible depending on the full package structure.' Anchor high. Leave room."),
            ("We can't move on base — can we offer more equity instead?",
             "Equity is only valuable if it vests and the company performs. Ask: vesting schedule, cliff, strike price, recent 409A valuation. Then decide. Do not accept equity vagueness."),
            ("What would it take to get you to sign by Friday?",
             "Urgency tactics are normal. 'I want to make a decision I'm fully confident in. If the package is right, I can move quickly. What flexibility do you have on [the specific gap]?'"),
            ("What does success look like in this role in 12 months?",
             "Ask this proactively — before they do. It signals you're thinking about performance, not just getting the job. Their answer also tells you whether the expectations are achievable."),
            ("Is there a path to VP from this Director role?",
             "Ask directly. A good answer: timeline, what the criteria are, who makes that decision, and whether there's a recent precedent. A vague answer is data too."),
            ("We're offering Director I — can we start at Director II given your experience?",
             "Level negotiation is often easier than comp negotiation and has longer-term leverage. Push for the higher level. If they say no, ask what would need to be true in 12 months to get there."),
        ],
        "watch_out": (
            "Do not negotiate against yourself by pre-emptively conceding. "
            "Do not make it personal or emotional — it's a business conversation. "
            "Do not accept verbal commitments about future promotions — get specifics: "
            "what the criteria are, when the review happens, who decides. "
            "Vague promises evaporate after you sign."
        ),
    },
]

# ── Page header ───────────────────────────────────────────────────────────
page_header("◎ Interview Prep", f"{current_role}  →  {target_role} · Round-by-round preparation")
st.divider()

# ── Readiness summary ─────────────────────────────────────────────────────
readiness = get_interview_readiness(user_id)
ready_count = sum(1 for r in readiness.values() if r.get("ready"))
cols = st.columns(len(ROUNDS))
for i, (col, rnd) in enumerate(zip(cols, ROUNDS)):
    is_ready = readiness.get(rnd["id"], {}).get("ready", False)
    col.metric(
        f"Round {i+1 if i < 4 else '✓'}",
        "Ready" if is_ready else "Not yet",
        delta=rnd["label"].split("·")[1].strip(),
        delta_color="normal" if is_ready else "off"
    )

if ready_count == len(ROUNDS):
    st.success("All rounds marked ready. You are prepared.")
elif ready_count > 0:
    st.info(f"{ready_count} of {len(ROUNDS)} rounds ready. Keep going.")

st.markdown("")

# ── Round tabs ────────────────────────────────────────────────────────────
tabs = st.tabs([r["label"] for r in ROUNDS])

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

for tab, rnd in zip(tabs, ROUNDS):
    with tab:
        rnd_readiness = readiness.get(rnd["id"], {})

        st.markdown(f"### {rnd['title']}")
        st.markdown(f"*{rnd['duration']}*")
        st.markdown(rnd["purpose"])
        st.markdown("")

        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("**What they're evaluating**")
            for point in rnd["evaluating"]:
                st.markdown(f"- {point}")

        with col_r:
            st.markdown("**Your objectives**")
            for obj in rnd["your_objectives"]:
                st.markdown(f"- {obj}")

        st.markdown("")
        st.markdown(f"> ⚠ **Watch out:** {rnd['watch_out']}")
        st.divider()

        # Question bank + coaching
        st.markdown("#### Question Bank")
        st.markdown("*Select a question to get personalized coaching on your answer.*")
        st.markdown("")

        q_labels = [q[0] for q in rnd["questions"]]
        selected_q = st.selectbox(
            "Choose a question to practice",
            options=q_labels,
            key=f"q_select_{rnd['id']}"
        )

        selected_idx = q_labels.index(selected_q)
        _, coaching_tip = rnd["questions"][selected_idx]

        with st.expander("Coaching tip for this question", expanded=True):
            st.markdown(coaching_tip)

        st.markdown("")
        st.markdown("**Practice your answer:**")
        user_answer = st.text_area(
            "Type your answer here",
            height=160,
            placeholder="Write your answer as you'd actually say it in the interview...",
            key=f"answer_{rnd['id']}_{selected_idx}"
        )

        if st.button(
            "Get AI feedback on my answer",
            key=f"feedback_{rnd['id']}_{selected_idx}",
            type="primary",
            disabled=not user_answer.strip()
        ):
            stories = get_user_stories(user_id)
            story_block = ""
            if stories:
                story_block = "\n\nUSER'S STAR STORIES:\n" + "\n---\n".join(
                    s["document"] for s in stories[:4]
                )

            system = f"""You are CareerSignal, an AI career coach specializing in Director/VP AI interview preparation.

USER PROFILE:
- Name: {name}
- Current role: {current_role}
- Target role: {target_role}
- Biggest asset: {profile.get('biggest_asset', '')}
- Cohort: {profile.get('cohort', '')}
{story_block}

You are reviewing the user's practice answer for this interview round: {rnd['title']}
Interview question: {selected_q}
Coaching tip context: {coaching_tip}

Give feedback in exactly this structure:

## What works
1–3 specific things done well. Be precise, not generic.

## What to strengthen
1–3 specific improvements. Reference their actual words. Show the rewrite.

## Rewritten opening line
One stronger opening sentence they could use to start this answer.

## Readiness verdict
One sentence: is this answer ready for a real interview, or does it need more work?

Keep feedback under 300 words. Be direct — not harsh, but honest."""

            with st.spinner("Analyzing your answer..."):
                response = client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=700,
                    system=system,
                    messages=[{
                        "role": "user",
                        "content": f"My answer to '{selected_q}':\n\n{user_answer}"
                    }]
                )

            st.markdown(response.content[0].text)

        st.divider()

        # Round readiness tracker
        st.markdown("#### Round Readiness")
        saved_note = rnd_readiness.get("notes", "")
        is_ready   = rnd_readiness.get("ready", False)

        rc1, rc2 = st.columns([0.3, 0.7])
        with rc1:
            mark_ready = st.checkbox(
                "Mark this round as ready",
                value=is_ready,
                key=f"ready_{rnd['id']}"
            )
        with rc2:
            round_notes = st.text_input(
                "Notes",
                value=saved_note,
                placeholder="e.g. Need stronger STAR story for ambiguity question",
                key=f"notes_{rnd['id']}"
            )

        if st.button("Save readiness", key=f"save_ready_{rnd['id']}", type="secondary"):
            save_interview_readiness(user_id, rnd["id"], mark_ready, round_notes)
            label = "Ready" if mark_ready else "Not ready"
            st.toast(f"{rnd['title']} marked as {label}.", icon="✓")
            st.rerun()
