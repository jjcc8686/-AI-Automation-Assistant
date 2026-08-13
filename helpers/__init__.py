"""
Helper package for AI Automation Assistant.
"""

from .extraction import extract_vba_code, extract_powerquery_m_code
from .cleaning import clean_vba_text, clean_powerquery_text, clean_xaml_text, clean_code
from .chunking import chunk_text
from .detection import detect_code_type
from .rag import embed_chunks, build_vector_store, retrieve_relevant_chunks
from .prompts import get_system_prompt, get_default_user_prompt
from .samples import get_sample_files
from .ui_theme import apply_theme
from .message_builder import build_user_message

__all__ = [
    "extract_vba_code",
    "extract_powerquery_m_code",
    "clean_vba_text",
    "clean_powerquery_text",
    "clean_xaml_text",
    "clean_code",
    "chunk_text",
    "detect_code_type",
    "embed_chunks",
    "build_vector_store",
    "retrieve_relevant_chunks",
    "get_system_prompt",
    "get_default_user_prompt",
    "get_sample_files",
    "apply_theme",
    "build_user_message",
]