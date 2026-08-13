"""
Knowledge Base management page (Admin only).
"""

import streamlit as st
from config import KB_TYPES
from helpers import chunk_text, build_vector_store

def render_knowledge_base() -> None:
    if st.session_state.role != "admin":
        st.warning("This page is only available to Admin users.")
        st.stop()

    st.title("Knowledge Base Management")
    st.markdown(
        "Upload reference documents that can be used during reviews by all users."
    )
    st.markdown("---")

    kb_files = st.file_uploader(
        "Upload reference documents (.txt, .md, .vba, .m, .pq, .xaml)",
        type=KB_TYPES,
        accept_multiple_files=True,
        key="kb_uploader",
    )

    if kb_files and st.button("Add to Knowledge Base", type="primary"):
        new_chunks = []
        new_names = []
        for f in kb_files:
            content = f.getvalue().decode("utf-8", errors="replace")
            chunks = chunk_text(content, mode="generic")
            new_chunks.extend(chunks)
            new_names.append(f.name)

        if new_chunks:
            if st.session_state.kb_index is None:
                index, stored = build_vector_store(new_chunks)
                st.session_state.kb_index = index
                st.session_state.kb_chunks = stored
            else:
                all_kb_chunks = st.session_state.kb_chunks + new_chunks
                index, stored = build_vector_store(all_kb_chunks)
                st.session_state.kb_index = index
                st.session_state.kb_chunks = stored

            st.session_state.kb_files.extend(new_names)
            st.success(f"Added {len(new_names)} document(s).")
            st.rerun()

    st.markdown("---")
    st.subheader("Current Knowledge Base")
    if st.session_state.kb_files:
        for name in st.session_state.kb_files:
            st.markdown(f"- `{name}`")
        st.caption(f"Total chunks: {len(st.session_state.kb_chunks)}")
        if st.button("Clear Knowledge Base"):
            st.session_state.kb_index = None
            st.session_state.kb_chunks = []
            st.session_state.kb_files = []
            st.success("Cleared.")
            st.rerun()
    else:
        st.info("Knowledge Base is empty. Upload documents above.")