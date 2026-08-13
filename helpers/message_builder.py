"""
Build the user message sent to the LLM (RAG + optional truncated file content).
"""

import streamlit as st
from config import MAX_RAG_CHARS, MAX_FILE_CHARS

def estimate_chars(text: str) -> int:
    return len(text or "")

def build_user_message(
    user_prompt: str,
    retrieved_chunks: list,
    retrieved_scores: list,
    file_content: str,
) -> tuple[str, dict]:
    """
    Returns (user_message, stats) where stats contains character counts.
    """
    rag_context = ""
    current_len = 0

    if retrieved_chunks:
        for i, (chunk, score) in enumerate(zip(retrieved_chunks, retrieved_scores)):
            piece = f"[Chunk {i + 1} | Confidence: {score:.2f}]\n{chunk}\n\n"
            if current_len + len(piece) > MAX_RAG_CHARS:
                break
            rag_context += piece
            current_len += len(piece)
    else:
        rag_context = "No relevant chunks were retrieved.\n"

    if len(file_content) > MAX_FILE_CHARS:
        truncated = (
            file_content[:MAX_FILE_CHARS]
            + "\n\n...[Content truncated due to length. "
            "Prioritise the retrieved RAG chunks above.]"
        )
        content_section = f"--- FILE CONTENT (TRUNCATED PREVIEW) ---\n{truncated}"
        st.warning(
            f"Uploaded content is large ({len(file_content):,} characters). "
            f"Only the first {MAX_FILE_CHARS:,} characters were sent with the retrieved chunks."
        )
        file_chars_sent = MAX_FILE_CHARS
    else:
        content_section = f"--- FULL FILE CONTENT ---\n{file_content}"
        file_chars_sent = len(file_content)

    user_message = (
        f"{user_prompt}\n\n"
        f"--- RELEVANT CODE CHUNKS (RAG) ---\n{rag_context}\n"
        f"{content_section}"
    )

    stats = {
        "prompt_chars": estimate_chars(user_prompt),
        "rag_chars": estimate_chars(rag_context),
        "file_chars_sent": file_chars_sent,
        "file_chars_original": len(file_content),
        "total_chars": estimate_chars(user_message),
        # Rough token estimate (~4 chars per token for English/code mix)
        "approx_tokens": max(1, estimate_chars(user_message) // 4),
    }
    return user_message, stats