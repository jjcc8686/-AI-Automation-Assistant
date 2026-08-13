"""
Chunking helpers for VBA, Power Query and UiPath.
"""

import re
from .cleaning import clean_vba_text, clean_powerquery_text, clean_xaml_text
from config import MAX_CHUNK_SIZE, MIN_CHUNK_SIZE

def chunk_text(
    text: str,
    max_chunk_size: int = MAX_CHUNK_SIZE,
    min_chunk_size: int = MIN_CHUNK_SIZE,
    mode: str = "generic",
) -> list[str]:
    """
    Clean + chunk code for VBA, Power Query, or UiPath.
    Cleaning is applied automatically based on mode.
    """
    if not text or not text.strip():
        return []

    # Automatic cleaning
    if mode == "vba":
        text = clean_vba_text(text)
    elif mode == "m":
        text = clean_powerquery_text(text)
    elif mode == "xaml":
        text = clean_xaml_text(text)
    else:
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()

    if not text:
        return []

    chunks = []
    current = ""

    for line in text.split("\n"):
        stripped = line.strip()
        lower = stripped.lower()
        should_split = False

        if mode == "vba":
            if (
                lower.startswith(
                    (
                        "sub ",
                        "function ",
                        "private sub ",
                        "public sub ",
                        "private function ",
                        "public function ",
                    )
                )
                and len(current) >= min_chunk_size
            ):
                should_split = True

        elif mode == "m":
            if stripped.startswith('#"') and "=" in stripped and len(current) >= min_chunk_size:
                should_split = True
            elif lower.startswith("let") and len(current) >= min_chunk_size:
                should_split = True

        elif mode == "xaml":
            if any(
                tag in line
                for tag in ["<ui:", "<Sequence", "<Flowchart", "<StateMachine", "<TryCatch"]
            ) and len(current) >= min_chunk_size:
                should_split = True

        if should_split and current.strip():
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

        if len(current) >= max_chunk_size:
            if current.strip():
                chunks.append(current.strip())
            current = ""

    if current.strip():
        if chunks and len(current.strip()) < min_chunk_size:
            chunks[-1] = chunks[-1] + "\n" + current.strip()
        else:
            chunks.append(current.strip())

    final_chunks = [c for c in chunks if len(c.strip()) >= 80]
    return final_chunks if final_chunks else ([text] if text else [])