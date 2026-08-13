"""
About Us page.
"""

import streamlit as st
from config import APP_VERSION_NO, APP_VERSION_DATE

def render_about_us() -> None:
    st.title("About Us")

    st.markdown(
        """
        ### AI Automation Assistant
        A secure, AI-powered web application designed to help Excel automation developers
        and RPA practitioners review and improve VBA, Power Query, and UiPath workflows.
        """
    )
    st.markdown("---")

    st.subheader("Project Purpose")
    st.markdown(
        """
        Manual code review of VBA macros, Power Query (M) scripts, and UiPath XAML workflows
        is time-consuming and inconsistent.

        This application uses **Retrieval-Augmented Generation (RAG)** together with
        domain-specific expertise to deliver structured, professional code reviews that focus on:
        - Security and best practices
        - Performance and maintainability
        - Redundancy detection
        - UiPath compatibility (for VBA)
        """
    )

    st.subheader("Key Features")
    st.markdown(
        """
        - Native VBA macro extraction from `.xlsm` / `.xlsb` files using **oletools**
        - Power Query M code review and optimisation suggestions
        - UiPath XAML workflow review (modularity, structure, Workflow Analyzer rules)
        - Context-aware analysis powered by vector retrieval (FAISS + OpenAI embeddings)
        - Selectable language model for each review (e.g. GPT-4o, GPT-4o-mini)
        - Role-based access (Admin / User)
        - Knowledge Base for reference documents
        - Downloadable review reports (`.txt` and `.md`) with date-time stamp
        - Session review history
        - Sample files for testing
        """
    )

    st.subheader("Technology Stack")
    st.markdown(
        """
        - **Frontend**: Streamlit
        - **VBA Extraction**: oletools
        - **Embeddings**: OpenAI `text-embedding-3-large`
        - **Vector Store**: FAISS
        - **Language Model**: OpenAI chat models (selectable per review; default GPT-4o)
        - **Security**: Streamlit Secrets + role-based password protection
        """
    )

    st.markdown("---")
    st.subheader("Project Team")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Chng Chyi Da**  \nchng_chyi_da@vital.gov.sg")
    with col2:
        st.markdown("**Jean Chua Yi Juan**  \njean_chua@vital.gov.sg")
    with col3:
        st.markdown("**Lim Yi Jun**  \nlim_yi_jun@vital.gov.sg")

    st.markdown("---")
    st.caption(f"{APP_VERSION_NO} • Last updated: {APP_VERSION_DATE}")