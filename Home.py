# Home.py — App entry point
import streamlit as st
from core.auth import hash_password, verify_password, create_token, decode_token
from core.database import init_db, create_user, get_user_by_email, update_last_login

st.set_page_config(
    page_title="CareerSignal",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB on first run
init_db()

# ── Session check ──────────────────────────────────────────────────────────
if "token" in st.session_state and st.session_state["token"]:
    payload = decode_token(st.session_state["token"])
    if payload:
        st.switch_page("pages/2_Coach.py")

# ── UI ─────────────────────────────────────────────────────────────────────
st.markdown("## ◎ CareerSignal")
st.markdown("*AI-powered career coaching for IT professionals targeting Director and VP of AI roles.*")
st.divider()

tab1, tab2 = st.tabs(["Sign In", "Create Account"])

with tab1:
    st.subheader("Welcome back")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Sign In", type="primary", use_container_width=True):
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
    st.subheader("Create your account")
    name     = st.text_input("Full name", key="reg_name")
    email_r  = st.text_input("Email", key="reg_email")
    pass_r   = st.text_input("Password (min 8 chars)", type="password", key="reg_pass")
    pass_r2  = st.text_input("Confirm password", type="password", key="reg_pass2")

    if st.button("Create Account", type="primary", use_container_width=True):
        if len(pass_r) < 8:
            st.error("Password must be at least 8 characters.")
        elif pass_r != pass_r2:
            st.error("Passwords do not match.")
        elif not name or not email_r:
            st.error("Please fill in all fields.")
        else:
            try:
                hashed = hash_password(pass_r)
                user_id = create_user(email_r, name, hashed)
                token = create_token(user_id, email_r, "free")
                st.session_state["token"]   = token
                st.session_state["user_id"] = user_id
                st.session_state["name"]    = name
                st.session_state["tier"]    = "free"
                st.success("Account created! Setting up your profile...")
                st.switch_page("pages/1_Profile.py")
            except ValueError as e:
                st.error(str(e))
