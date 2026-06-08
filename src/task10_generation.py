"""
Task 10 - Generation with citations.

This module formats retrieved context, reorders it to reduce the
"lost in the middle" effect, and generates an answer with source citations.
OpenAI is used when OPENAI_API_KEY is configured. Without an API key, the
module returns a conservative extractive answer from retrieved evidence rather
than guessing.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

try:
    from src.task9_retrieval_pipeline import retrieve
except (ImportError, NotImplementedError):
    try:
        from .task9_retrieval_pipeline import retrieve
    except (ImportError, NotImplementedError):
        retrieve = None

try:
    from src.task6_lexical_search import lexical_search
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from src.task6_lexical_search import lexical_search


# top_k=5 is enough evidence for most legal/news questions while keeping the
# prompt compact; this reduces lost-in-the-middle risk.
TOP_K = 5

# top_p=0.9 keeps the answer fluent but constrained. Combined with low
# temperature, it avoids overly random factual claims in RAG.
TOP_P = 0.9

# Low temperature because legal/news RAG should prioritize factuality.
TEMPERATURE = 0.3

OPENAI_GENERATION_MODEL = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o-mini")
GEMINI_GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-3.1-flash-lite")


SYSTEM_PROMPT = """Answer the following question comprehensively in Vietnamese.
For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luật Phòng chống ma túy 2021, 2021]
or [VietNamNet, 2026]).

If the information is not explicitly stated in the provided context or knowledge
base, state 'I cannot verify this information' rather than guessing.

Rules:
- Only use information from the provided context.
- Every factual claim MUST have a citation.
- If context is insufficient, say 'I cannot verify this information'.
- Keep the answer clear and concise."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Reorder chunks to reduce lost-in-the-middle.

    Input sorted by score: [1, 2, 3, 4, 5]
    Output pattern:        [1, 3, 5, 4, 2]

    Best evidence remains first; second-best moves to the end, where LLMs also
    tend to attend well; lower-priority chunks sit closer to the middle.
    """
    if len(chunks) <= 2:
        return list(chunks)

    front = [chunks[index] for index in range(0, len(chunks), 2)]
    back = [chunks[index] for index in range(len(chunks) - 1, 0, -2)]
    return front + back


def _source_label(chunk: dict, fallback_index: int) -> str:
    metadata = chunk.get("metadata", {}) or {}
    source = metadata.get("source") or metadata.get("path") or f"Source {fallback_index}"
    year = metadata.get("year")
    if not year:
        match = re.search(r"(20\d{2}|19\d{2})", str(source))
        year = match.group(1) if match else "n.d."
    return f"{source}, {year}"


def _clean_text(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"about:blank\s*\d*/\d*", "", text)
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -*")


def format_context(chunks: list[dict]) -> str:
    """
    Format chunks into prompt context with citation-friendly source labels.
    """
    context_parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {}) or {}
        source_label = _source_label(chunk, index)
        doc_type = metadata.get("type", "unknown")
        score = float(chunk.get("score", 0.0))
        content = str(chunk.get("content", "")).strip()
        context_parts.append(
            f"[Document {index} | Citation: {source_label} | Type: {doc_type} | Score: {score:.3f}]\n"
            f"{content}\n"
        )
    return "\n---\n".join(context_parts)


def _retrieve_context(query: str, top_k: int) -> list[dict]:
    if retrieve is not None:
        try:
            results = retrieve(query, top_k=top_k)
            if results:
                return results
        except Exception:
            pass
    return lexical_search(query, top_k=top_k)


def _has_evidence(query: str, chunks: list[dict]) -> bool:
    if not chunks:
        return False
    query_terms = {term for term in re.findall(r"\w+", query.lower(), flags=re.UNICODE) if len(term) > 2}
    if not query_terms:
        return True
    context_text = " ".join(str(chunk.get("content", "")).lower() for chunk in chunks)
    return any(term in context_text for term in query_terms)


def _extractive_answer(query: str, chunks: list[dict]) -> str:
    if not _has_evidence(query, chunks):
        return "I cannot verify this information"

    sentences = []
    for index, chunk in enumerate(chunks, 1):
        citation = _source_label(chunk, index)
        content = _clean_text(str(chunk.get("content", "")))
        parts = [_clean_text(part) for part in re.split(r"(?<=[.!?])\s+", content)]
        useful = next((part for part in parts if 40 <= len(part) <= 320), content[:260])
        if useful:
            sentences.append(f"{useful.strip()} [{citation}]")
        if len(sentences) >= 3:
            break

    return " ".join(sentences) if sentences else "I cannot verify this information"


def _generate_with_openai(query: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"
    response = client.chat.completions.create(
        model=OPENAI_GENERATION_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )
    return response.choices[0].message.content or "I cannot verify this information"


def _generate_with_gemini(query: str, context: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_GENERATION_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            ),
        )
        return getattr(response, "text", None) or "I cannot verify this information"
    except ImportError:
        import google.generativeai as legacy_genai

        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel(
            GEMINI_GENERATION_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            user_message,
            generation_config={
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
            },
        )
        return getattr(response, "text", None) or "I cannot verify this information"


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation with citations.

    Returns:
        {
            'answer': str,
            'sources': list[dict],
            'retrieval_source': str
        }
    """
    chunks = _retrieve_context(query, top_k=top_k)
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)

    if not _has_evidence(query, reordered):
        answer = "I cannot verify this information"
    elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        try:
            answer = _generate_with_gemini(query, context)
        except Exception:
            answer = _extractive_answer(query, reordered)
    elif os.getenv("OPENAI_API_KEY"):
        try:
            answer = _generate_with_openai(query, context)
        except Exception:
            answer = _extractive_answer(query, reordered)
    else:
        answer = _extractive_answer(query, reordered)

    return {
        "answer": answer,
        "sources": reordered,
        "retrieval_source": reordered[0].get("source", "hybrid") if reordered else "none",
        "context": context,
        "top_k": top_k,
        "top_p": TOP_P,
        "temperature": TEMPERATURE,
        "model": GEMINI_GENERATION_MODEL
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        else OPENAI_GENERATION_MODEL
        if os.getenv("OPENAI_API_KEY")
        else "extractive_fallback",
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma túy theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma túy?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma túy 2021?",
    ]

    for question in test_queries:
        print(f"\n{'=' * 70}")
        print(f"Q: {question}")
        print("=" * 70)
        result = generate_with_citation(question)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
