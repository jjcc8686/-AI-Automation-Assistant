"""
Sample Files page.
"""

import streamlit as st
from helpers.samples import get_sample_files

def render_sample_files() -> None:
    st.title("Sample Files")
    st.markdown("Download these sample files to test the three review tools.")
    st.markdown("---")

    samples = get_sample_files()
    cols = st.columns(len(samples))

    for col, sample in zip(cols, samples):
        with col:
            st.subheader(sample["title"])
            st.download_button(
                f"Download {sample['filename']}",
                data=sample["content"],
                file_name=sample["filename"],
                mime="text/plain",
                use_container_width=True,
            )
            st.caption(sample["caption"])