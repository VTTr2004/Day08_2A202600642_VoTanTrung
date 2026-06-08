"""
Task 7 - Reranking Module.

Chosen method: MMR (Maximal Marginal Relevance).

MMR re-orders candidates by balancing relevance to the query and diversity
against already selected documents:

    MMR = lambda * relevance(query, doc)
          - (1 - lambda) * max_similarity(doc, selected_doc)

This is implemented locally, so it does not require a Jina/Qwen API key. When
candidates include dense embeddings from Task 4/5, those vectors are used. For
plain candidates from tests or lexical search, the module falls back to a
token-frequency cosine vector built from query/content text.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    accented = re.findall(r"\w+", lowered, flags=re.UNICODE)
    plain = re.findall(r"\w+", _strip_accents(lowered), flags=re.UNICODE)
    return accented + [token for token in plain if token not in accented]


def _tf_vector(text: str) -> Counter[str]:
    return Counter(_tokens(text))


def _cosine_sparse(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0

    common_terms = set(left) & set(right)
    dot = sum(left[term] * right[term] for term in common_terms)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _cosine_dense(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def rerank_mmr(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Re-rank candidates with Maximal Marginal Relevance.

    Args:
        query: User query.
        candidates: List of {'content': str, 'score': float, 'metadata': dict}.
        top_k: Number of results after reranking.
        lambda_param: 0.7 keeps relevance dominant while penalizing duplicates.

    Returns:
        Top candidates with updated 'score' and metadata['rerank_method'].
    """
    if not query or not candidates or top_k <= 0:
        return []

    top_k = min(top_k, len(candidates))
    lambda_param = max(0.0, min(1.0, lambda_param))

    query_vector = _tf_vector(query)
    text_vectors = [_tf_vector(candidate.get("content", "")) for candidate in candidates]

    max_original_score = max(float(candidate.get("score", 0.0)) for candidate in candidates) or 1.0
    relevance_scores = []
    for candidate, text_vector in zip(candidates, text_vectors):
        text_relevance = _cosine_sparse(query_vector, text_vector)
        normalized_original = max(float(candidate.get("score", 0.0)), 0.0) / max_original_score
        relevance_scores.append(0.75 * text_relevance + 0.25 * normalized_original)

    selected: list[int] = []
    remaining = set(range(len(candidates)))
    mmr_scores_by_index: dict[int, float] = {}

    while remaining and len(selected) < top_k:
        best_index = None
        best_score = float("-inf")

        for index in remaining:
            diversity_penalty = 0.0
            for selected_index in selected:
                candidate_embedding = candidates[index].get("embedding")
                selected_embedding = candidates[selected_index].get("embedding")
                if candidate_embedding and selected_embedding:
                    similarity = _cosine_dense(candidate_embedding, selected_embedding)
                else:
                    similarity = _cosine_sparse(text_vectors[index], text_vectors[selected_index])
                diversity_penalty = max(diversity_penalty, similarity)

            mmr_score = lambda_param * relevance_scores[index] - (1 - lambda_param) * diversity_penalty
            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index

        if best_index is None:
            break

        selected.append(best_index)
        remaining.remove(best_index)
        mmr_scores_by_index[best_index] = best_score

    results = []
    for rank, index in enumerate(selected, 1):
        item = candidates[index].copy()
        metadata = item.get("metadata", {}).copy()
        metadata.update(
            {
                "rerank_method": "mmr",
                "rerank_rank": rank,
                "original_score": float(candidates[index].get("score", 0.0)),
                "mmr_lambda": lambda_param,
            }
        )
        item["metadata"] = metadata
        item["score"] = float(mmr_scores_by_index[index])
        results.append(item)

    return results


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion helper for later hybrid retrieval.

    RRF(d) = sum(1 / (k + rank_r(d))) across rankers.
    """
    if not ranked_lists or top_k <= 0:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item.get("metadata", {}).get("path") or item.get("content", "")
            if not key:
                continue
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            items[key] = item

    ordered_keys = sorted(scores, key=lambda key: scores[key], reverse=True)
    results = []
    for rank, key in enumerate(ordered_keys[:top_k], 1):
        item = items[key].copy()
        metadata = item.get("metadata", {}).copy()
        metadata.update({"rerank_method": "rrf", "rerank_rank": rank})
        item["metadata"] = metadata
        item["score"] = float(scores[key])
        results.append(item)
    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "mmr",
) -> list[dict]:
    """
    Re-score and re-order candidates based on relevance to query.

    Default method is MMR because it is local, deterministic, and reduces
    duplicate chunks in the final context.
    """
    if method == "mmr":
        return rerank_mmr(query, candidates, top_k=top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma túy", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ bị bắt vì sử dụng ma túy", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    for result in rerank("hình phạt tàng trữ ma túy", dummy_candidates, top_k=2):
        print(f"[{result['score']:.3f}] {result['content']}")
