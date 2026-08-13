"""
AI Tools page – main review workflow.
"""

import streamlit as st
from datetime import datetime
from openai import OpenAI

from config import (
    CHAT_MODEL,
    CHAT_MODEL_OPTIONS,
    MAX_TOKENS,
    TEMPERATURE,
    RETRIEVE_K,
    VBA_TYPES,
    PQ_TYPES,
    UIPATH_TYPES,
)
from helpers import (
    extract_vba_code,
    extract_powerquery_m_code,
    chunk_text,
    detect_code_type,
    build_vector_store,
    retrieve_relevant_chunks,
    get_system_prompt,
    get_default_user_prompt,
)
from helpers.message_builder import build_user_message

import hashlib

def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]

def render_ai_tools() -> None:
    st.title("AI Automation Assistant")
    st.markdown("**Select a service, upload file(s), and provide your instructions.**")
    st.markdown("---")

    option = st.selectbox(
        "Choose an option:",
        ["Review Excel VBA", "Review Excel PowerQuery", "Review UiPath Code"],
    )

    selected_model = st.selectbox(
        "Language model",
        options=CHAT_MODEL_OPTIONS,
        index=CHAT_MODEL_OPTIONS.index(CHAT_MODEL) if CHAT_MODEL in CHAT_MODEL_OPTIONS else 0,
        help="Use a lighter model to reduce cost for routine reviews.",
    )

    uploaded_files = []
    user_prompt = ""
    file_content = ""
    all_chunks = []

    if option == "Review Excel VBA":
        st.subheader("Review Excel VBA")
        uploaded_files = st.file_uploader(
            "Upload VBA code files (.txt) or Excel macro-enabled workbooks (.xlsm, .xlsb)",
            type=VBA_TYPES,
            accept_multiple_files=True,
            key=f"vba_uploader_{st.session_state.uploader_key}",
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value=get_default_user_prompt(option),
            height=200,
        )

    elif option == "Review Excel PowerQuery":
        st.subheader("Review Excel PowerQuery")
        uploaded_files = st.file_uploader(
            "Upload PowerQuery M code files (.txt, .m, .pq)",
            type=PQ_TYPES,
            accept_multiple_files=True,
            key=f"pq_uploader_{st.session_state.uploader_key}",
        )
        st.info(
            "Excel files (.xlsx/.xlsm/.xlsb) often do **not** embed Power Query M code.\n\n"
            "Export via Power Query → Advanced Editor → save as `.txt` / `.m` / `.pq`."
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value=get_default_user_prompt(option),
            height=200,
        )

    else:
        st.subheader("Review UiPath Code")
        uploaded_files = st.file_uploader(
            "Upload UiPath XAML files (.xaml or .txt)",
            type=UIPATH_TYPES,
            accept_multiple_files=True,
            key=f"uipath_uploader_{st.session_state.uploader_key}",
        )
        user_prompt = st.text_area(
            "Custom Prompt / Instructions",
            value=get_default_user_prompt(option),
            height=200,
        )

    use_kb = False
    if st.session_state.kb_index is not None and st.session_state.kb_chunks:
        use_kb = st.checkbox("Also use Knowledge Base as reference", value=False)
        st.caption(
            f"{len(st.session_state.kb_files)} document(s) in Knowledge Base."
        )

    st.markdown("---")

    if uploaded_files:
        st.markdown("##### Uploaded Files")
        for f in uploaded_files:
            st.markdown(f"- `{f.name}` ({f.size / 1024:.1f} KB)")

        if st.button("Clear Uploaded Files"):
            st.session_state.uploader_key += 1
            for key in [
                "vba_index",
                "vba_chunks",
                "pq_index",
                "pq_chunks",
                "uipath_index",
                "uipath_chunks",
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Cleared.")
            st.rerun()

        detected_types = set()

        for uploaded_file in uploaded_files:
            if option == "Review Excel VBA":
                content = extract_vba_code(uploaded_file)
                chunks = chunk_text(content, mode="vba")
            elif option == "Review Excel PowerQuery":
                content = extract_powerquery_m_code(uploaded_file)
                chunks = chunk_text(content, mode="m")
            else:
                content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                chunks = chunk_text(content, mode="xaml")

            file_content += f"\n\n===== FILE: {uploaded_file.name} =====\n\n{content}"
            all_chunks.extend(chunks)
            detected_types.add(detect_code_type(content))

        if all_chunks:
            cache_key = f"{option}_{_content_hash(file_content)}"

            # Reuse embeddings if this exact content was already indexed in this session
            if (
                st.session_state.get("embed_cache_key") == cache_key
                and st.session_state.get("embed_cache_index") is not None
            ):
                index = st.session_state["embed_cache_index"]
                stored_chunks = st.session_state["embed_cache_chunks"]
                st.info("Using cached embeddings.")
            else:
                with st.spinner("Building vector index..."):
                    index, stored_chunks = build_vector_store(all_chunks)
                st.session_state["embed_cache_key"] = cache_key
                st.session_state["embed_cache_index"] = index
                st.session_state["embed_cache_chunks"] = stored_chunks

            # Keep existing tool-specific keys so retrieval code stays unchanged
            if option == "Review Excel VBA":
                st.session_state["vba_index"] = index
                st.session_state["vba_chunks"] = stored_chunks
            elif option == "Review Excel PowerQuery":
                st.session_state["pq_index"] = index
                st.session_state["pq_chunks"] = stored_chunks
            else:
                st.session_state["uipath_index"] = index
                st.session_state["uipath_chunks"] = stored_chunks

            st.success(
                f"Processed **{len(uploaded_files)}** file(s), **{len(all_chunks)}** chunks."
                    )

            with st.expander(
                "Extracted content (preview)", expanded=False
            ):
                st.code(
                    file_content[:3000] + ("..." if len(file_content) > 3000 else ""),
                    language="vb" if option == "Review Excel VBA" else "text",
                )

            expected_type = {
                "Review Excel VBA": "vba",
                "Review Excel PowerQuery": "powerquery",
                "Review UiPath Code": "uipath",
            }.get(option)

            if expected_type and expected_type not in detected_types:
                st.warning(
                    f"Content may not match **{option}**. "
                    f"Detected: {', '.join(t.upper() for t in detected_types if t != 'unknown') or 'Unknown'}."
                )
            elif "unknown" in detected_types and len(detected_types) == 1:
                st.info(
                    "Code type unclear; review will continue."
                )
        else:
            st.warning("No usable content found in the upload.")
    else:
        st.info("Upload a file to continue.")

    st.markdown("---")

    process_disabled = not uploaded_files

    if st.button(
        "Process Request",
        type="primary",
        use_container_width=True,
        disabled=process_disabled,
    ):
        if not user_prompt.strip():
            st.error("Please enter your instructions / prompt before processing.")
            st.stop()

        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Retrieving...")
        progress_bar.progress(20)

        retrieved_chunks = []
        retrieved_scores = []

        if option == "Review Excel VBA" and "vba_index" in st.session_state:
            results = retrieve_relevant_chunks(
                user_prompt,
                st.session_state["vba_index"],
                st.session_state["vba_chunks"],
                k=RETRIEVE_K,
            )
            retrieved_chunks.extend([c for c, s in results])
            retrieved_scores.extend([s for c, s in results])
        elif option == "Review Excel PowerQuery" and "pq_index" in st.session_state:
            results = retrieve_relevant_chunks(
                user_prompt,
                st.session_state["pq_index"],
                st.session_state["pq_chunks"],
                k=RETRIEVE_K,
            )
            retrieved_chunks.extend([c for c, s in results])
            retrieved_scores.extend([s for c, s in results])
        elif option == "Review UiPath Code" and "uipath_index" in st.session_state:
            results = retrieve_relevant_chunks(
                user_prompt,
                st.session_state["uipath_index"],
                st.session_state["uipath_chunks"],
                k=RETRIEVE_K,
            )
            retrieved_chunks.extend([c for c, s in results])
            retrieved_scores.extend([s for c, s in results])

        if use_kb and st.session_state.kb_index is not None:
            kb_results = retrieve_relevant_chunks(
                user_prompt,
                st.session_state.kb_index,
                st.session_state.kb_chunks,
                k=2,
            )
            retrieved_chunks.extend([c for c, s in kb_results])
            retrieved_scores.extend([s for c, s in kb_results])

        progress_bar.progress(40)

        if retrieved_chunks:
            st.info(f"**{len(retrieved_chunks)}** chunk(s) retrieved.")
            with st.expander("Retrieved chunks", expanded=False):
                for i, (chunk, score) in enumerate(
                    zip(retrieved_chunks, retrieved_scores)
                ):
                    st.markdown(f"**Chunk {i + 1}** — Confidence: **{score:.2f}**")
                    lang = (
                        "vb"
                        if option == "Review Excel VBA"
                        else "xml"
                        if option == "Review UiPath Code"
                        else "text"
                    )
                    st.code(chunk, language=lang)

        status_text.text("Generating...")
        progress_bar.progress(60)

        try:
            client = OpenAI(api_key=st.secrets["openai_api_key"])
            system_prompt = get_system_prompt(option)
            user_message, msg_stats = build_user_message(
                user_prompt, retrieved_chunks, retrieved_scores, file_content
            )

            st.caption(
                f"Estimated context size: ~{msg_stats['approx_tokens']:,} tokens "
                f"({msg_stats['total_chars']:,} characters)"
            )
            
            progress_bar.progress(80)

            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            ai_response = response.choices[0].message.content
            progress_bar.progress(100)
            status_text.text("Done.")

        except Exception as e:
            ai_response = (
                f"Error connecting to OpenAI: {str(e)}\n\n"
                "Please verify your API key in .streamlit/secrets.toml."
            )
            progress_bar.progress(100)
            status_text.text("Error occurred")

        st.markdown("---")
        st.subheader("AI Response")
        with st.expander("View Full Review", expanded=True):
            st.markdown(ai_response)

        safe_name = option.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download as Text (.txt)",
                data=ai_response,
                file_name=f"{safe_name}_Review_{timestamp}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "Download as Markdown (.md)",
                data=ai_response,
                file_name=f"{safe_name}_Review_{timestamp}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        st.caption(
            "Select text above to copy."
        )

        st.session_state.history.append(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "option": option,
                "prompt": user_prompt[:100]
                + ("..." if len(user_prompt) > 100 else ""),
                "response": ai_response,
                "num_files": len(uploaded_files) if uploaded_files else 0,
                "num_chunks": len(retrieved_chunks),
            }
        )