"""
login.py — Kenya MSME Advisor: Login Page
Single entry point for all users.
Operators are redirected to chat, Admin and Researcher to their pages.
"""

import streamlit as st

st.set_page_config(
    page_title="Kenya MSME Advisor — Login",
    page_icon="🇰🇪",
    layout="centered"
)

# ── Hide streamlit nav ─────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
header { visibility: hidden; }
.login-card {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
    max-width: 420px;
    margin: 3rem auto;
}
.login-header {
    background: linear-gradient(135deg, #006600 0%, #cc0000 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 2rem;
}
.role-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 4px;
}
</style>
""", unsafe_allow_html=True)

# ── Users database ─────────────────────────────────────────────────────────────
USERS = {
    "operator":   {"password": None,               "role": "operator",   "name": "MSME Operator"},
    "admin":      {"password": "msme2024admin",    "role": "admin",      "name": "System Administrator"},
    "researcher": {"password": "msme2024research", "role": "researcher", "name": "Researcher"},
}

# ── Already logged in ──────────────────────────────────────────────────────────
if st.session_state.get("logged_in"):
    role = st.session_state.get("role")
    name = st.session_state.get("user_name")
    st.success(f"✅ You are logged in as **{name}**")
    col1, col2 = st.columns(2)
    if role == "operator":
        if col1.button("Go to Chat →", type="primary", use_container_width=True):
            st.switch_page("src/app.py")
    elif role == "admin":
        if col1.button("Go to Admin Panel →", type="primary", use_container_width=True):
            st.switch_page("src/pages/admin.py")
    elif role == "researcher":
        if col1.button("Go to Analytics →", type="primary", use_container_width=True):
            st.switch_page("src/pages/analytics.py")
    if col2.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.stop()

# ── Login form ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="login-header">
    <h2 style="margin:0">🇰🇪 Kenya MSME Advisor</h2>
    <p style="margin:0.5rem 0 0 0;opacity:0.9;font-size:0.9rem">
        Sign in to continue
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("**Select your role:**")
role_choice = st.selectbox(
    "Role",
    options=["MSME Operator", "System Administrator", "Researcher"],
    label_visibility="collapsed"
)

role_map = {
    "MSME Operator":        "operator",
    "System Administrator": "admin",
    "Researcher":           "researcher",
}
selected_role = role_map[role_choice]

# Show password field only for admin and researcher
if selected_role == "operator":
    st.info("👤 MSME Operators access the advisory chat directly — no password required.")
    password = None
else:
    password = st.text_input(
        f"Password for {role_choice}",
        type="password",
        placeholder="Enter your password..."
    )

if st.button("Sign In →", type="primary", use_container_width=True):
    user = USERS[selected_role]

    # Validate
    if selected_role == "operator":
        # No password needed
        st.session_state["logged_in"]  = True
        st.session_state["role"]       = "operator"
        st.session_state["username"]   = "operator"
        st.session_state["user_name"]  = "MSME Operator"
        st.session_state["admin_auth"] = False
        st.session_state["researcher_auth"] = False
        st.switch_page("src/app.py")

    elif password == user["password"]:
        st.session_state["logged_in"]  = True
        st.session_state["role"]       = selected_role
        st.session_state["username"]   = selected_role
        st.session_state["user_name"]  = user["name"]
        if selected_role == "admin":
            st.session_state["admin_auth"] = True
            st.switch_page("src/pages/admin.py")
        elif selected_role == "researcher":
            st.session_state["researcher_auth"] = True
            st.switch_page("src/pages/analytics.py")
    else:
        st.error("❌ Incorrect password. Please try again.")

st.markdown("---")
st.caption("🔒 Admin and Researcher access is password protected.")
st.caption("👤 MSME Operators can access the chat directly without a password.")
