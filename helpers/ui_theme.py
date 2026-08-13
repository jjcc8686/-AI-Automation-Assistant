"""
UI theme helpers (dark / light mode CSS).
"""

import streamlit as st

def apply_theme(dark_mode: bool) -> None:
    """Inject CSS for dark or light mode."""
    if dark_mode:
        st.markdown(
            """
            <style>
                .stApp {
                    background-color: #0e1117 !important;
                    color: #fafafa !important;
                }
                section[data-testid="stSidebar"] {
                    background-color: #1a1d24 !important;
                }
                .stMarkdown, .stMarkdown p, .stMarkdown span,
                h1, h2, h3, h4, h5, h6, label {
                    color: #fafafa !important;
                }
                .stTextArea textarea, .stTextInput input {
                    background-color: #262730 !important;
                    color: #fafafa !important;
                }
                .streamlit-expanderHeader {
                    background-color: #262730 !important;
                    color: #fafafa !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
                .stApp {
                    background-color: #ffffff !important;
                    color: #1a1a1a !important;
                }
                section[data-testid="stSidebar"] {
                    background-color: #f0f2f6 !important;
                }
                .stMarkdown, .stMarkdown p, .stMarkdown span,
                h1, h2, h3, h4, h5, h6, label {
                    color: #1a1a1a !important;
                }
                .stTextArea textarea, .stTextInput input {
                    background-color: #ffffff !important;
                    color: #1a1a1a !important;
                    border: 1px solid #d0d0d0 !important;
                }
                .streamlit-expanderHeader {
                    background-color: #f0f2f6 !important;
                    color: #1a1a1a !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )