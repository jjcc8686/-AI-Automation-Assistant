"""
Configuration and constants for AI Automation Assistant.
"""

APP_VERSION_NO = "AI Automation Assistant v1.0"
APP_VERSION_DATE = "05 August 2026"

# OpenAI
EMBEDDING_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o"          # default
CHAT_MODEL_OPTIONS = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"]
MAX_TOKENS = 4000
TEMPERATURE = 0.3

# RAG / Chunking
MAX_CHUNK_SIZE = 1200
MIN_CHUNK_SIZE = 200
RETRIEVE_K = 5

# Token / size protection
MAX_RAG_CHARS = 25000
MAX_FILE_CHARS = 25000

# Supported upload types
VBA_TYPES = ["txt", "xlsm", "xlsb"]
PQ_TYPES = ["txt", "m", "pq"]
UIPATH_TYPES = ["xaml", "txt"]
KB_TYPES = ["txt", "md", "vba", "m", "pq", "xaml"]