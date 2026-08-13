"""
RAG helpers: embedding, vector store and retrieval (cosine similarity).
"""

import numpy as np
import faiss
from openai import OpenAI
import streamlit as st

from config import EMBEDDING_MODEL, RETRIEVE_K

def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Create embeddings for a list of text chunks."""
    client = OpenAI(api_key=st.secrets["openai_api_key"])
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=chunks,
    )
    return [item.embedding for item in response.data]

def build_vector_store(chunks: list[str]):
    """
    Build a FAISS index using cosine similarity.
    Vectors are L2-normalised so that Inner Product == Cosine Similarity.
    """
    if not chunks:
        return None, []

    embeddings = embed_chunks(chunks)
    embeddings_np = np.array(embeddings).astype("float32")
    faiss.normalize_L2(embeddings_np)

    dim = embeddings_np.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product = Cosine after normalisation
    index.add(embeddings_np)

    return index, chunks

def retrieve_relevant_chunks(query: str, index, chunks: list[str], k: int = RETRIEVE_K):
    """
    Retrieve top-k chunks using cosine similarity + light keyword boost.
    Returns list of (chunk, confidence) with confidence in [0, 1].
    """
    if index is None or not chunks:
        return []

    client = OpenAI(api_key=st.secrets["openai_api_key"])
    query_embedding = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    ).data[0].embedding

    query_np = np.array([query_embedding]).astype("float32")
    faiss.normalize_L2(query_np)

    search_k = min(max(k * 2, 8), len(chunks))
    scores, indices = index.search(query_np, search_k)

    query_lower = query.lower()
    keywords = [w for w in query_lower.split() if len(w) > 3]

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(chunks):
            continue

        chunk = chunks[idx]
        confidence = float(score)
        confidence = max(0.0, min(1.0, confidence))

        if keywords:
            chunk_lower = chunk.lower()
            keyword_hits = sum(1 for kw in keywords if kw in chunk_lower)
            boost = min(0.12, keyword_hits * 0.025)
            confidence = min(1.0, confidence + boost)

        results.append((chunk, confidence))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:k]