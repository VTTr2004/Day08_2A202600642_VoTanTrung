"""
Task 6 - Lexical Search Module (BM25).

This module uses BM25 for keyword retrieval. It prefers rank-bm25's BM25Okapi
when installed, and includes the same BM25 scoring formula as a local fallback
so the project can still run in offline/demo environments.
"""

from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


try:
    from src.task4_chunking_indexing import VECTOR_STORE_PATH, chunk_documents, load_documents
except ModuleNotFoundError:
    # Allows: python src\task6_lexical_search.py
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from src.task4_chunking_indexing import VECTOR_STORE_PATH, chunk_documents, load_documents


CORPUS: list[dict] = []
_BM25_INDEX = None


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def tokenize(text: str) -> list[str]:
    """
    Tokenize Vietnamese text for BM25.

    We keep both accented and accent-stripped forms so queries like "ma tuý"
    can still match chunks written as "ma túy".
    """
    lowered = text.lower()
    raw_tokens = re.findall(r"\w+", lowered, flags=re.UNICODE)
    plain_tokens = re.findall(r"\w+", _strip_accents(lowered), flags=re.UNICODE)
    return raw_tokens + [token for token in plain_tokens if token not in raw_tokens]


class LocalBM25Okapi:
    """Small BM25Okapi-compatible implementation used only if rank-bm25 is absent."""

    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.tokenized_corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_freqs = [Counter(doc) for doc in tokenized_corpus]
        self.doc_lengths = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0
        self.idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        doc_count = len(self.tokenized_corpus)
        document_frequency: Counter[str] = Counter()
        for doc in self.tokenized_corpus:
            document_frequency.update(set(doc))

        return {
            token: math.log(1 + (doc_count - freq + 0.5) / (freq + 0.5))
            for token, freq in document_frequency.items()
        }

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = []
        for freqs, doc_len in zip(self.doc_freqs, self.doc_lengths):
            score = 0.0
            for token in query_tokens:
                tf = freqs.get(token, 0)
                if tf == 0:
                    continue
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / (self.avgdl or 1.0))
                score += self.idf.get(token, 0.0) * (tf * (self.k1 + 1)) / denominator
            scores.append(score)
        return scores


def load_corpus() -> list[dict]:
    """Load chunks from Task 4 vector store, or create chunks from markdown files."""
    global CORPUS
    if CORPUS:
        return CORPUS

    if VECTOR_STORE_PATH.exists():
        try:
            data = json.loads(VECTOR_STORE_PATH.read_text(encoding="utf-8"))
            records = data.get("records", [])
            CORPUS = [
                {
                    "content": record.get("content", ""),
                    "metadata": record.get("metadata", {}),
                }
                for record in records
                if record.get("content")
            ]
            if CORPUS:
                return CORPUS
        except (OSError, json.JSONDecodeError):
            pass

    CORPUS = chunk_documents(load_documents())
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """
    Build a BM25 index from corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    tokenized_corpus = [tokenize(doc["content"]) for doc in corpus]
    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized_corpus)
    except ImportError:
        return LocalBM25Okapi(tokenized_corpus)


def _get_bm25_index():
    global _BM25_INDEX
    corpus = load_corpus()
    if _BM25_INDEX is None:
        _BM25_INDEX = build_bm25_index(corpus)
    return _BM25_INDEX


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search keywords using BM25.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}, sorted by
        BM25 score descending.
    """
    if not query or top_k <= 0:
        return []

    corpus = load_corpus()
    if not corpus:
        return []

    bm25 = _get_bm25_index()
    scores = bm25.get_scores(tokenize(query))
    ranked_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)

    results = []
    for index in ranked_indices:
        score = float(scores[index])
        if score <= 0:
            continue
        doc = corpus[index]
        results.append(
            {
                "content": doc["content"],
                "score": score,
                "metadata": {
                    **doc.get("metadata", {}),
                    "retrieval_method": "bm25",
                },
            }
        )
        if len(results) >= top_k:
            break

    return results


if __name__ == "__main__":
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma túy", top_k=5)
    for result in results:
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
