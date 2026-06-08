from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


GROUP_PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = GROUP_PROJECT_ROOT.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(GROUP_PROJECT_ROOT / ".env")

from src.task9_retrieval_pipeline import retrieve  # noqa: E402
from src.task10_generation import (  # noqa: E402
    TOP_K,
    TOP_P,
    TEMPERATURE,
    _extractive_answer,
    _generate_with_gemini,
    _generate_with_openai,
    _has_evidence,
    format_context,
    reorder_for_llm,
)


@dataclass(frozen=True)
class RagConfig:
    name: str
    label: str
    top_k: int = TOP_K
    score_threshold: float = 0.3
    use_reranking: bool = True


RAG_CONFIGS = {
    "hybrid_rerank": RagConfig(
        name="hybrid_rerank",
        label="Hybrid retrieval + MMR reranking",
        use_reranking=True,
    ),
    "hybrid_no_rerank": RagConfig(
        name="hybrid_no_rerank",
        label="Hybrid retrieval without reranking",
        use_reranking=False,
    ),
}


def get_config(name: str | None) -> RagConfig:
    return RAG_CONFIGS.get(name or "", RAG_CONFIGS["hybrid_rerank"])


def build_standalone_question(question: str, history: Iterable[dict] | None = None) -> str:
    """Add recent chat context so short follow-up questions remain retrievable."""
    clean_question = question.strip()
    turns = list(history or [])[-6:]
    if not turns:
        return clean_question

    compact_turns = []
    for turn in turns:
        role = str(turn.get("role", "user")).strip()
        content = str(turn.get("content", "")).strip()
        if role and content:
            compact_turns.append(f"{role}: {content[:500]}")

    if not compact_turns:
        return clean_question

    return (
        "Recent conversation:\n"
        + "\n".join(compact_turns)
        + "\n\nCurrent question:\n"
        + clean_question
    )


def _source_label(source: dict, index: int) -> str:
    metadata = source.get("metadata", {}) or {}
    return (
        metadata.get("source")
        or metadata.get("path")
        or metadata.get("title")
        or f"Source {index}"
    )


def normalize_sources(sources: list[dict]) -> list[dict]:
    normalized = []
    for index, source in enumerate(sources, 1):
        metadata = source.get("metadata", {}) or {}
        normalized.append(
            {
                "rank": index,
                "label": _source_label(source, index),
                "content": str(source.get("content", "")),
                "score": float(source.get("score", 0.0)),
                "retrieval_source": source.get("source", metadata.get("retrieval_method", "unknown")),
                "metadata": metadata,
            }
        )
    return normalized


def _generate_answer_text(question: str, chunks: list[dict], context: str) -> str:
    if not _has_evidence(question, chunks):
        return "I cannot verify this information"

    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        try:
            return _generate_with_gemini(question, context)
        except Exception:
            return _extractive_answer(question, chunks)

    if os.getenv("OPENAI_API_KEY"):
        try:
            return _generate_with_openai(question, context)
        except Exception:
            return _extractive_answer(question, chunks)

    return _extractive_answer(question, chunks)


def answer_question(
    question: str,
    history: Iterable[dict] | None = None,
    config_name: str = "hybrid_rerank",
    top_k: int | None = None,
) -> dict:
    config = get_config(config_name)
    effective_top_k = top_k or config.top_k
    standalone_question = build_standalone_question(question, history)
    chunks = retrieve(
        standalone_question,
        top_k=effective_top_k,
        score_threshold=config.score_threshold,
        use_reranking=config.use_reranking,
    )
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    answer = _generate_answer_text(standalone_question, reordered, context)
    sources = normalize_sources(reordered)

    return {
        "question": question,
        "standalone_question": standalone_question,
        "answer": answer,
        "sources": sources,
        "context": context,
        "config": config.name,
        "config_label": config.label,
        "top_k": effective_top_k,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "model": os.getenv("GEMINI_GENERATION_MODEL", "gemini-3.1-flash-lite")
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        else os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o-mini")
        if os.getenv("OPENAI_API_KEY")
        else "extractive_fallback",
    }
