"""
Task 5 - Semantic Search Module.

Dense retrieval is performed over the ChromaDB vector store created by Task 4.
Query embeddings use the exact same model configured there:
sentence-transformers/all-MiniLM-L6-v2.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from src.task4_chunking_indexing import (
        CHROMA_COLLECTION_NAME,
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
        CHROMA_COLLECTION_NAME,
        EMBEDDING_DIM,
        EMBEDDING_MODEL,
        VECTOR_STORE_PATH,
        _hash_embedding,
        run_pipeline,
    )


def _get_collection():
    """Load Task 4 ChromaDB collection, building it once if it does not exist."""
    try:
        import chromadb
    except ImportError:
        return None

    if not VECTOR_STORE_PATH.exists():
        try:
            run_pipeline()
        except Exception:
            return None

    try:
        client = chromadb.PersistentClient(path=str(VECTOR_STORE_PATH))
        collection = client.get_collection(CHROMA_COLLECTION_NAME)
        if collection.count() == 0:
            run_pipeline()
            collection = client.get_collection(CHROMA_COLLECTION_NAME)
        return collection
    except Exception:
        try:
            run_pipeline()
            client = chromadb.PersistentClient(path=str(VECTOR_STORE_PATH))
            return client.get_collection(CHROMA_COLLECTION_NAME)
        except Exception:
            return None


def _embed_query(query: str) -> list[float] | None:
    """Embed query with the same model/vector format used for indexed chunks."""
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(EMBEDDING_MODEL)
        embedding = model.encode(query, normalize_embeddings=True)
        return embedding.tolist()
    except Exception:
        if os.getenv("ALLOW_HASH_EMBEDDING_FALLBACK") == "1":
            return _hash_embedding(query)
        return None


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

    collection = _get_collection()
    if collection is None:
        return []

    query_embedding = _embed_query(query)
    if query_embedding is None:
        return []

    if len(query_embedding) != EMBEDDING_DIM:
        return []

    query_result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    documents = query_result.get("documents", [[]])[0]
    metadatas = query_result.get("metadatas", [[]])[0]
    distances = query_result.get("distances", [[]])[0]
    for document, metadata, distance in zip(documents, metadatas, distances):
        score = 1.0 - float(distance)
        metadata = metadata or {}
        results.append(
            {
                "content": document or "",
                "score": float(score),
                "metadata": {
                    **metadata,
                    "embedding_model": metadata.get("embedding_model", EMBEDDING_MODEL),
                    "embedding_dim": metadata.get("embedding_dim", EMBEDDING_DIM),
                    "vector_store": "chromadb",
                },
            }
        )

    return results


if __name__ == "__main__":
    results = semantic_search("hình phạt cho tội tàng trữ ma túy", top_k=5)
    for result in results:
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
