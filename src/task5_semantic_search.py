"""
Task 5 - Semantic Search Module.

Dense retrieval is performed over the local JSON vector store created by
Task 4. Query embeddings use the exact same model configured there:
sentence-transformers/all-MiniLM-L6-v2.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

try:
    from src.task4_chunking_indexing import (
        EMBEDDING_DIM,
        EMBEDDING_MODEL,
        VECTOR_STORE_PATH,
        _hash_embedding,
        run_pipeline,
    )
except ModuleNotFoundError:
    # Allows: python src\task5_semantic_search.py
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from src.task4_chunking_indexing import (
        EMBEDDING_DIM,
        EMBEDDING_MODEL,
        VECTOR_STORE_PATH,
        _hash_embedding,
        run_pipeline,
    )


def _load_vector_store() -> dict:
    """Load Task 4 vector store, building it once if it does not exist."""
    if not VECTOR_STORE_PATH.exists():
        try:
            run_pipeline()
        except Exception:
            return {"records": []}

    try:
        return json.loads(VECTOR_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"records": []}


def _embed_query(query: str, store: dict) -> list[float] | None:
    """Embed query with the same model/vector format used for indexed chunks."""
    records = store.get("records", [])
    uses_hash_fallback = any(
        "hash fallback" in str(record.get("metadata", {}).get("embedding_model", ""))
        for record in records
    )

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(EMBEDDING_MODEL)
        embedding = model.encode(query, normalize_embeddings=True)
        return embedding.tolist()
    except Exception:
        # Only use the deterministic fallback when the index itself was built
        # with that fallback, or when explicitly requested for offline smoke tests.
        if uses_hash_fallback or os.getenv("ALLOW_HASH_EMBEDDING_FALLBACK") == "1":
            return _hash_embedding(query)
        return None


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for two vectors."""
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search semantically with dense vector similarity.

    Args:
        query: User query.
        top_k: Maximum number of chunks to return.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}, sorted by
        score descending.
    """
    if not query or top_k <= 0:
        return []

    store = _load_vector_store()
    records = store.get("records", [])
    if not records:
        return []

    query_embedding = _embed_query(query, store)
    if query_embedding is None:
        return []

    if len(query_embedding) != EMBEDDING_DIM:
        return []

    results = []
    for record in records:
        embedding = record.get("embedding") or []
        score = _cosine_similarity(query_embedding, embedding)
        results.append(
            {
                "content": record.get("content", ""),
                "score": float(score),
                "metadata": {
                    **record.get("metadata", {}),
                    "embedding_model": record.get("metadata", {}).get("embedding_model", EMBEDDING_MODEL),
                    "embedding_dim": record.get("metadata", {}).get("embedding_dim", EMBEDDING_DIM),
                    "vector_store": store.get("vector_store", "local_json"),
                },
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    results = semantic_search("hình phạt cho tội tàng trữ ma túy", top_k=5)
    for result in results:
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
