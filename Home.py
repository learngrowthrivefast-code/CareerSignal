# Home.py — App entry point
import streamlit as st
from core.auth import hash_password, verify_password, create_token, decode_token
from core.database import init_db, create_user, get_user_by_email, update_last_login, get_user_count
from core.styles import apply_styles

st.set_page_config(
    page_title="CareerSignal",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_styles()
init_db()

# ── Session check ─────────────────────────────────────────────────────────
if "token" in st.session_state and st.session_state["token"]:
    payload = decode_token(st.session_state["token"])
    if payload:
        st.switch_page("pages/2_Coach.py")

# ── Layout ────────────────────────────────────────────────────────────────
hero_col, form_col = st.columns([11, 9], gap="large")

with hero_col:
    total_users = get_user_count()
    spots_left  = max(0, 50 - total_users)

    st.markdown("""
    <div style="padding: 48px 24px 24px 8px;">
        <div style="font-size:13px; font-weight:600; letter-spacing:3px;
                    text-transform:uppercase; color:#6366f1; margin-bottom:20px;">
            ◎ &nbsp; C A R E E R S I G N A L
        </div>
        <h1 style="font-size:46px; font-weight:800; line-height:1.15; margin:0 0 20px 0;
                   background:linear-gradient(135deg,#f1f5f9 30%,#a5b4fc 100%);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            The AI coach that<br>remembers your journey.
        </h1>
        <p style="font-size:17px; color:#94a3b8; line-height:1.7; margin-bottom:36px; max-width:480px;">
            Personalized career coaching for IT professionals targeting
            <strong style="color:#e2e8f0;">Director and VP of AI</strong> roles —
            with memory that persists across every session.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Value props
    props = [
        ("◈", "Persistent memory", "Every session picks up exactly where the last one left off."),
        ("◈", "Recruiter-calibrated coaching", "Built around what Director/VP AI hiring panels actually look for."),
        ("◈", "18-month structured roadmap", "Five phases from narrative reframe to offer negotiation."),
        ("◈", "Full interview preparation", "All 5 rounds — recruiter screen through comp negotiation."),
    ]
    for icon, title, desc in props:
        st.markdown(f"""
        <div style="display:flex; align-items:flex-start; gap:14px;
                    margin-bottom:18px; padding:0 8px;">
            <span style="font-size:20px; color:#6366f1; margin-top:2px;">{icon}</span>
            <div>
                <span style="font-weight:600; font-size:15px; color:#e2e8f0;">{title}</span>
                <span style="color:#94a3b8; font-size:14px;"> — {desc}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    # Founder cohort urgency
    if spots_left > 0:
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3);
                    border-radius:10px; padding:14px 18px; max-width:460px;">
            <span style="font-size:13px; color:#a5b4fc; font-weight:600;">
                🔥 Founder Cohort — {spots_left} of 50 spots remaining
            </span><br>
            <span style="font-size:13px; color:#94a3b8;">
                First 50 users get free access to all Premium features permanently.
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25);
                    border-radius:10px; padding:14px 18px; max-width:460px;">
            <span style="font-size:13px; color:#6ee7b7; font-weight:600;">
                ✓ Founder cohort full — Premium features now available on paid plan
            </span>
        </div>
        """, unsafe_allow_html=True)

with form_col:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["  Sign In  ", "  Create Account  "])

        with tab1:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown("#### Welcome back")
            email    = st.text_input("Email", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            if st.button("Sign In →", type="primary", use_container_width=True, key="signin_btn"):
                user = get_user_by_email(email)
                if user and verify_password(password, user["password"]):
                    token = create_token(user["user_id"], user["email"], user["tier"])
                    st.session_state["token"]   = token
                    st.session_state["user_id"] = user["user_id"]
                    st.session_state["name"]    = user["name"]
                    st.session_state["tier"]    = user["tier"]
                    update_last_login(user["user_id"])
                    st.success("Signed in! Redirecting...")
                    st.switch_page("pages/2_Coach.py")
                else:
                    st.error("Invalid email or password.")

        with tab2:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown("#### Create your account")
            name    = st.text_input("Full name", key="reg_name", placeholder="Your name")
            email_r = st.text_input("Email", key="reg_email", placeholder="you@example.com")
            pass_r  = st.text_input("Password (min 8 chars)", type="password", key="reg_pass", placeholder="••••••••")
            pass_r2 = st.text_input("Confirm password", type="password", key="reg_pass2", placeholder="••••••••")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            if st.button("Create Account →", type="primary", use_container_width=True, key="signup_btn"):
                if len(pass_r) < 8:
                    st.error("Password must be at least 8 characters.")
                elif pass_r != pass_r2:
                    st.error("Passwords do not match.")
                elif not name or not email_r:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        hashed  = hash_password(pass_r)
                        user_id = create_user(email_r, name, hashed)
                        token   = create_token(user_id, email_r, "free")
                        st.session_state["token"]   = token
                        st.session_state["user_id"] = user_id
                        st.session_state["name"]    = name
                        st.session_state["tier"]    = "free"
                        st.success("Account created! Setting up your profile...")
                        st.switch_page("pages/1_Profile.py")
                    except ValueError as e:
                        st.error(str(e))

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
