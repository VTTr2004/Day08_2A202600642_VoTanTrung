"""
Task 9 - Complete Retrieval Pipeline.

Pipeline:
    1. Run semantic_search + lexical_search
    2. Merge results with RRF
    3. Rerank with MMR
    4. If top hybrid score is below threshold, fallback to PageIndex
    5. Return top_k results
"""

from __future__ import annotations

import sys
from pathlib import Path


try:
    from src.task5_semantic_search import semantic_search
    from src.task6_lexical_search import lexical_search
    from src.task7_reranking import rerank, rerank_rrf
    from src.task8_pageindex_vectorless import pageindex_search
except ModuleNotFoundError:
    # Allows: python src\task9_retrieval_pipeline.py
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from src.task5_semantic_search import semantic_search
    from src.task6_lexical_search import lexical_search
    from src.task7_reranking import rerank, rerank_rrf
    from src.task8_pageindex_vectorless import pageindex_search


SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "mmr"


def _safe_search(search_fn, query: str, top_k: int) -> list[dict]:
    try:
        return search_fn(query, top_k=top_k) or []
    except Exception:
        return []


def _dedupe_results(results: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for item in results:
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        key = item.get("metadata", {}).get("path") or content[:300]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _normalize_scores(results: list[dict]) -> list[dict]:
    if not results:
        return []

    scores = [float(item.get("score", 0.0)) for item in results]
    min_score = min(scores)
    max_score = max(scores)
    span = max_score - min_score

    normalized = []
    for item, raw_score in zip(results, scores):
        output = item.copy()
        metadata = output.get("metadata", {}).copy()
        metadata["raw_rerank_score"] = raw_score
        output["metadata"] = metadata
        output["score"] = 1.0 if span == 0 else (raw_score - min_score) / span
        normalized.append(output)
    return normalized


def _tag_source(results: list[dict], source: str) -> list[dict]:
    tagged = []
    for item in results:
        output = item.copy()
        output["source"] = source
        output.setdefault("metadata", {})
        tagged.append(output)
    return tagged


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Complete retrieval pipeline with PageIndex fallback.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict, 'source': str}
    """
    if not query or top_k <= 0:
        return []

    search_k = max(top_k * 2, top_k)

    dense_results = _safe_search(semantic_search, query, search_k)
    sparse_results = _safe_search(lexical_search, query, search_k)

    ranked_lists = [results for results in (dense_results, sparse_results) if results]
    if ranked_lists:
        merged = rerank_rrf(ranked_lists, top_k=search_k)
    else:
        merged = []

    merged = _dedupe_results(merged)
    merged = _tag_source(merged, "hybrid")

    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        final_results = _tag_source(final_results, "hybrid")
        final_results = _normalize_scores(final_results)
    else:
        final_results = merged[:top_k]

    best_score = float(final_results[0]["score"]) if final_results else 0.0
    if not final_results or best_score < score_threshold:
        fallback = pageindex_search(query, top_k=top_k)
        return _tag_source(fallback, "pageindex")[:top_k]

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma túy",
        "Nghệ sĩ nào bị bắt vì sử dụng ma túy năm 2024",
        "Luật phòng chống ma túy 2021 quy định gì về cai nghiện",
    ]

    for question in test_queries:
        print(f"\nQuery: {question}")
        print("-" * 60)
        for index, result in enumerate(retrieve(question, top_k=3), 1):
            print(f"  {index}. [{result['score']:.3f}] [{result['source']}] {result['content'][:80]}...")
