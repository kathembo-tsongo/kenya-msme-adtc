"""
login.py — Kenya MSME Advisor: Login Page
Credentials loaded from config/credentials.json (not hardcoded).
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import verify_password, get_user

st.set_page_config(
    page_title="Kenya MSME Advisor — Login",
    page_icon="🇰🇪",
    layout="centered"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Already logged in ──────────────────────────────────────────────────────────
if st.session_state.get("logged_in"):
    role = st.session_state.get("role")
    name = st.session_state.get("user_name")
    st.success(f"✅ Logged in as **{name}**")
    col1, col2 = st.columns(2)
    if role == "operator":
        if col1.button("Go to Chat →", type="primary", use_container_width=True):
            st.switch_page("app.py")
    elif role == "admin":
        if col1.button("Go to Admin Panel →", type="primary", use_container_width=True):
            st.switch_page("pages/admin.py")
    elif role == "researcher":
        if col1.button("Go to Research Dashboard →", type="primary", use_container_width=True):
            st.switch_page("pages/analytics.py")
    if col2.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.stop()

# ── Login form ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#006600 0%,#cc0000 100%);
color:white;padding:2rem;border-radius:12px;text-align:center;
margin-bottom:2rem;">
    <h2 style="margin:0">🇰🇪 Kenya MSME Advisor</h2>
    <p style="margin:0.5rem 0 0 0;opacity:0.9">Sign in to continue</p>
</div>
""", unsafe_allow_html=True)

role_choice = st.selectbox(
    "Select your role",
    ["MSME Operator", "System Administrator", "Researcher"]
)

role_map = {
    "MSME Operator":        "operator",
    "System Administrator": "admin",
    "Researcher":           "researcher",
}
selected_role = role_map[role_choice]

if selected_role == "operator":
    st.info("👤 MSME Operators access the advisory chat directly — no password required.")
    username = "operator"
    password = None
else:
    username = st.text_input(
        "Username",
        placeholder="Enter your username..."
    )
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password..."
    )

if st.button("Sign In →", type="primary", use_container_width=True):
    if selected_role == "operator":
        st.session_state["logged_in"]  = True
        st.session_state["role"]       = "operator"
        st.session_state["username"]   = "operator"
        st.session_state["user_name"]  = "MSME Operator"
        st.session_state["admin_auth"] = False
        st.session_state["researcher_auth"] = False
        st.switch_page("app.py")

    elif not username or not password:
        st.error("Please enter both username and password.")

    elif verify_password(username, password):
        user = get_user(username)
        # Verify role matches selection
        if user.get("role") != selected_role:
            st.error(
                f"❌ This account does not have {role_choice} access."
            )
        else:
            st.session_state["logged_in"]  = True
            st.session_state["role"]       = user["role"]
            st.session_state["username"]   = username
            st.session_state["user_name"]  = user["name"]

            if user["role"] == "admin":
                st.session_state["admin_auth"] = True
                st.switch_page("pages/admin.py")
            elif user["role"] == "researcher":
                st.session_state["researcher_auth"] = True
                st.switch_page("pages/analytics.py")
    else:
        st.error("❌ Incorrect username or password.")

st.markdown("---")
st.caption("🔒 Admin and Researcher access requires username and password.")
st.caption("👤 MSME Operators access the chat directly without credentials.")
