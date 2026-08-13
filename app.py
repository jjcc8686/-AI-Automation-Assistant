"""
AI Automation Assistant – Main entry point.

Handles login, sidebar navigation, theme, and dispatches to page modules.
"""

import streamlit as st

from config import APP_VERSION_NO
from helpers.ui_theme import apply_theme
from app_pages import (
    render_ai_tools,
    render_knowledge_base,
    render_sample_files,
    render_review_history,
    render_powerquery_guide,
    render_about_us,
    render_methodology,
)

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="AI Automation Assistant",
    page_icon="⚙",
    layout="wide",
)

# ====================== SESSION STATE ======================
defaults = {
    "authenticated": False,
    "role": None,
    "history": [],
    "uploader_key": 0,
    "current_page": "AI Tools",
    "dark_mode": True,
    "kb_index": None,
    "kb_chunks": [],
    "kb_files": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ====================== LOGIN ======================
if not st.session_state.authenticated:
    st.title("AI Automation Assistant")
    st.markdown("### Login")
    role_choice = st.radio("Select role", ["User", "Admin"], horizontal=True)
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if role_choice == "Admin" and password == st.secrets.get("admin_password", ""):
            st.session_state.authenticated = True
            st.session_state.role = "admin"
            st.rerun()
        elif role_choice == "User" and password == st.secrets.get("user_password", ""):
            st.session_state.authenticated = True
            st.session_state.role = "user"
            st.rerun()
        else:
            st.error("Incorrect password for the selected role.")
    st.stop()

# Safety: force re-login if role is missing
if st.session_state.authenticated and st.session_state.role is None:
    st.session_state.authenticated = False
    st.rerun()

# ====================== SIDEBAR ======================
role_display = (st.session_state.role or "unknown").upper()
st.sidebar.markdown(f"### Logged in as: **{role_display}**")
st.sidebar.markdown("---")

st.sidebar.markdown("### Main")
for label in ["AI Tools", "Review History"]:
    if st.sidebar.button(
        label,
        use_container_width=True,
        type="primary" if st.session_state.current_page == label else "secondary",
    ):
        st.session_state.current_page = label
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Guides & Info")
for label in ["Power Query Export Guide", "Methodology", "About Us", "Sample Files"]:
    if st.sidebar.button(
        label,
        use_container_width=True,
        type="primary" if st.session_state.current_page == label else "secondary",
    ):
        st.session_state.current_page = label
        st.rerun()

if st.session_state.role == "admin":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Admin")
    if st.sidebar.button(
        "Knowledge Base",
        use_container_width=True,
        type="primary"
        if st.session_state.current_page == "Knowledge Base"
        else "secondary",
    ):
        st.session_state.current_page = "Knowledge Base"
        st.rerun()

st.sidebar.markdown("---")

# Theme
dark_mode = st.sidebar.toggle("Dark Mode", value=st.session_state.dark_mode)
st.session_state.dark_mode = dark_mode
apply_theme(dark_mode)

st.sidebar.markdown("---")
st.sidebar.caption(APP_VERSION_NO)
st.sidebar.caption("For best widget colours, also set theme in ⋮ → Settings → Theme")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

# ====================== PAGE DISPATCH ======================
page = st.session_state.current_page

if page == "AI Tools":
    render_ai_tools()
elif page == "Knowledge Base":
    render_knowledge_base()
elif page == "Sample Files":
    render_sample_files()
elif page == "Review History":
    render_review_history()
elif page == "Power Query Export Guide":
    render_powerquery_guide()
elif page == "About Us":
    render_about_us()
elif page == "Methodology":
    render_methodology()
else:
    st.error(f"Unknown page: {page}")
    st.session_state.current_page = "AI Tools"
    st.rerun()
