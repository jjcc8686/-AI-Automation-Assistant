"""
Review History page.
"""

import streamlit as st

def render_review_history() -> None:
    st.title("Review History")
    st.markdown("Previous reviews from this session are shown below.")
    st.markdown("---")

    if not st.session_state.history:
        st.info(
            "No reviews in this session yet."
        )
        return

    for i, item in enumerate(reversed(st.session_state.history)):
        with st.expander(
            f"**{item['option']}** — {item['timestamp']} • "
            f"{item['num_files']} file(s) • {item['num_chunks']} chunks"
        ):
            st.markdown(f"**Prompt preview:** {item['prompt']}")
            st.markdown("---")
            st.markdown(item["response"])

            safe_name = item["option"].replace(" ", "_")
            ts_clean = item["timestamp"].replace(":", "-").replace(" ", "_")

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "Download .txt",
                    item["response"],
                    f"{safe_name}_Review_{ts_clean}.txt",
                    mime="text/plain",
                    key=f"hist_txt_{i}",
                )
            with c2:
                st.download_button(
                    "Download .md",
                    item["response"],
                    f"{safe_name}_Review_{ts_clean}.md",
                    mime="text/markdown",
                    key=f"hist_md_{i}",
                )

    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()