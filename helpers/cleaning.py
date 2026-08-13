"""
Code cleaning helpers for VBA, Power Query and UiPath.
"""

import re

def clean_vba_text(text: str) -> str:
    """Remove VBA Attribute lines and collapse excessive blank lines."""
    if not text:
        return ""

    cleaned_lines = []
    for line in text.splitlines():
        if line.strip().startswith("Attribute VB_"):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()

def clean_powerquery_text(text: str) -> str:
    """Light cleaning for Power Query M code."""
    if not text:
        return ""
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()

def clean_xaml_text(text: str) -> str:
    """Light cleaning for UiPath XAML."""
    if not text:
        return ""
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()

def clean_code(text: str, mode: str = "generic") -> str:
    """Dispatcher that applies the appropriate cleaner."""
    if mode == "vba":
        return clean_vba_text(text)
    if mode == "m":
        return clean_powerquery_text(text)
    if mode == "xaml":
        return clean_xaml_text(text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()