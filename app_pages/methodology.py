"""
Methodology page.
"""

import streamlit as st

def render_methodology() -> None:
    st.title("Methodology")

    st.markdown(
        """
        ### Overview
        The AI Automation Assistant is a secure Streamlit application that combines
        domain-specific code analysis with Retrieval-Augmented Generation (RAG).

        Users can upload VBA, Power Query (M), or UiPath XAML files. The system extracts
        and chunks the content, generates embeddings, stores them in a FAISS vector index,
        retrieves the most relevant segments based on the user’s prompt, and uses a
        selectable OpenAI chat model to produce structured professional reviews.
        Results can be downloaded with a date-time stamp and previous reviews are kept
        in session history.
        """
    )

    st.subheader("Technology Stack")
    st.markdown(
        """
        - **Frontend**: Streamlit
        - **VBA Extraction**: oletools (`olevba`)
        - **Embeddings**: OpenAI `text-embedding-3-large`
        - **Vector Store**: FAISS
        - **Language Model**: OpenAI chat models (user-selectable; default GPT-4o)
        - **Secrets Management**: Streamlit Secrets
        """
    )

    st.subheader("High-Level Architecture")
    st.markdown(
        """
        **Upload → Extract → Clean → Chunk → Embed → Store (FAISS) → Retrieve → Generate Review → Download / History**

        At review time, the user may choose the chat model (for example GPT-4o or GPT-4o-mini)
        to balance quality and cost.
        """
    )

    st.subheader("Roles")
    st.markdown(
        """
        - **Admin**: Can manage a Knowledge Base of reference documents that can be optionally used during reviews.
        - **User**: Can upload files for review and optionally include the Knowledge Base.
        """
    )

    st.subheader("Use Case 1: Review Excel VBA")
    st.markdown(
        """
        1. User uploads one or more VBA files (`.txt`, `.xlsm`, `.xlsb`)
        2. System extracts VBA macros using **oletools**
        3. Code is cleaned and chunked by `Sub` / `Function` boundaries
        4. Chunks are converted into embeddings using OpenAI
        5. A FAISS vector index is built (reused from session cache when content is unchanged)
        6. User submits a review prompt and selects a language model
        7. Most relevant chunks are retrieved (RAG)
        8. The selected chat model performs a structured review
        9. Results are displayed, downloadable (with date-time), and saved to history
        """
    )

    st.subheader("Use Case 2: Review Excel Power Query")
    st.markdown(
        """
        1. User uploads one or more Power Query files (`.txt`, `.m`, `.pq`)
        2. System reads the M code
        3. Code is cleaned and chunked by step boundaries
        4. Chunks are converted into embeddings using OpenAI
        5. A FAISS vector index is built (reused from session cache when content is unchanged)
        6. User submits a review prompt and selects a language model
        7. Most relevant chunks are retrieved (RAG)
        8. The selected chat model performs a structured review
        9. Results are displayed, downloadable (with date-time), and saved to history
        """
    )

    st.subheader("Use Case 3: Review UiPath Code")
    st.markdown(
        """
        1. User uploads one or more UiPath XAML files (`.xaml`, `.txt`)
        2. System extracts the XAML content
        3. Code is cleaned and chunked by activity boundaries
        4. Chunks are converted into embeddings using OpenAI
        5. A FAISS vector index is built (reused from session cache when content is unchanged)
        6. User submits a review prompt and selects a language model
        7. Most relevant chunks are retrieved (RAG)
        8. The selected chat model performs a structured review
        9. Results are displayed, downloadable (with date-time), and saved to history
        """
    )

    st.subheader("Security Considerations")
    st.markdown(
        """
        - Application access is protected by role-based password authentication.
        - API keys and credentials are stored securely using Streamlit Secrets.
        - No uploaded files or analysis results are permanently stored on the server.
        - All processing occurs in-memory during the session.
        """
    )