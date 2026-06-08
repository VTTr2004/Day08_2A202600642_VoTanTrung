"""
Task 8 - PageIndex Vectorless RAG.

PageIndex is used as the intended vectorless fallback: documents are uploaded
to PageIndex, then queried by doc_id without a vector store. For local grading
or classroom runs without a PageIndex API key, this module provides a small
structure-aware fallback over markdown headings. The fallback is deliberately
vectorless: it scores title/header/text keyword overlap and never uses
embeddings or a vector database.
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv


load_dotenv()

PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
LANDING_LEGAL_DIR = PROJECT_DIR / "data" / "landing" / "legal"
PAGEINDEX_DIR = PROJECT_DIR / "data" / "pageindex"
PAGEINDEX_MANIFEST_PATH = PAGEINDEX_DIR / "pageindex_manifest.json"

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PAGEINDEX_DOC_IDS = [doc_id.strip() for doc_id in os.getenv("PAGEINDEX_DOC_IDS", "").split(",") if doc_id.strip()]
PAGEINDEX_API_BASE = os.getenv("PAGEINDEX_API_BASE", "https://api.vectify.ai").rstrip("/")


def _headers() -> dict[str, str]:
    return {"api_key": PAGEINDEX_API_KEY}


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    accented = re.findall(r"\w+", lowered, flags=re.UNICODE)
    plain = re.findall(r"\w+", _strip_accents(lowered), flags=re.UNICODE)
    return accented + [token for token in plain if token not in accented]


def _load_manifest() -> list[dict]:
    if not PAGEINDEX_MANIFEST_PATH.exists():
        return []
    try:
        data = json.loads(PAGEINDEX_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("documents", []) if isinstance(data, dict) else []


def _save_manifest(documents: list[dict]) -> None:
    PAGEINDEX_DIR.mkdir(parents=True, exist_ok=True)
    PAGEINDEX_MANIFEST_PATH.write_text(
        json.dumps({"documents": documents}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extract_doc_id(response_json: dict) -> str | None:
    for key in ("doc_id", "id", "document_id"):
        if response_json.get(key):
            return str(response_json[key])
    data = response_json.get("data")
    if isinstance(data, dict):
        for key in ("doc_id", "id", "document_id"):
            if data.get(key):
                return str(data[key])
    return None


def _extract_retrieval_id(response_json: dict) -> str | None:
    for key in ("retrieval_id", "id"):
        if response_json.get(key):
            return str(response_json[key])
    data = response_json.get("data")
    if isinstance(data, dict):
        for key in ("retrieval_id", "id"):
            if data.get(key):
                return str(data[key])
    return None


def _completed(status_json: dict) -> bool:
    status = str(status_json.get("status", "")).lower()
    return status in {"completed", "complete", "success", "succeeded", "done"}


def upload_documents(poll: bool = True, timeout_seconds: int = 180) -> list[dict]:
    """
    Upload legal PDFs to PageIndex and save their doc_ids locally.

    PageIndex cloud API is PDF-oriented, so Task 1 legal PDFs are uploaded.
    The returned manifest can be copied into PAGEINDEX_DOC_IDS if preferred.
    """
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Missing PAGEINDEX_API_KEY. Add it to .env before uploading to PageIndex.")

    pdf_files = sorted(LANDING_LEGAL_DIR.glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError(f"No PDF files found in {LANDING_LEGAL_DIR}")

    uploaded = []
    for pdf_file in pdf_files:
        with pdf_file.open("rb") as file_handle:
            response = requests.post(
                f"{PAGEINDEX_API_BASE}/pageindex/",
                headers=_headers(),
                files={"file": (pdf_file.name, file_handle, "application/pdf")},
                timeout=60,
            )
        response.raise_for_status()
        payload = response.json()
        doc_id = _extract_doc_id(payload)
        if not doc_id:
            raise RuntimeError(f"PageIndex upload response missing doc_id for {pdf_file.name}: {payload}")

        item = {
            "doc_id": doc_id,
            "filename": pdf_file.name,
            "type": "legal",
            "status": payload.get("status", "submitted"),
        }

        if poll:
            deadline = time.time() + timeout_seconds
            while time.time() < deadline:
                status_response = requests.get(
                    f"{PAGEINDEX_API_BASE}/pageindex/{doc_id}/",
                    headers=_headers(),
                    timeout=30,
                )
                status_response.raise_for_status()
                status_payload = status_response.json()
                item["status"] = status_payload.get("status", item["status"])
                if _completed(status_payload):
                    break
                time.sleep(5)

        uploaded.append(item)
        print(f"Uploaded to PageIndex: {pdf_file.name} -> {doc_id}")

    _save_manifest(uploaded)
    return uploaded


def _iter_doc_ids() -> list[str]:
    ids = list(PAGEINDEX_DOC_IDS)
    ids.extend(item["doc_id"] for item in _load_manifest() if item.get("doc_id"))
    return list(dict.fromkeys(ids))


def _submit_pageindex_query(doc_id: str, query: str) -> str | None:
    response = requests.get(
        f"{PAGEINDEX_API_BASE}/pageindex/{doc_id}/?query={quote(query)}",
        headers=_headers(),
        timeout=60,
    )
    response.raise_for_status()
    return _extract_retrieval_id(response.json())


def _poll_retrieval(retrieval_id: str, timeout_seconds: int = 120) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        response = requests.get(
            f"{PAGEINDEX_API_BASE}/pageindex/retrieval/{retrieval_id}/",
            headers=_headers(),
            timeout=30,
        )
        response.raise_for_status()
        last_payload = response.json()
        if _completed(last_payload):
            return last_payload
        time.sleep(3)
    return last_payload


def _normalize_pageindex_nodes(payload: dict, doc_id: str) -> list[dict]:
    nodes = (
        payload.get("retrieved_nodes")
        or payload.get("nodes")
        or payload.get("result")
        or payload.get("results")
        or []
    )
    if isinstance(nodes, dict):
        nodes = [nodes]

    results = []
    for rank, node in enumerate(nodes, 1):
        if isinstance(node, str):
            content = node
            metadata = {}
            score = 1.0 / rank
        else:
            content = (
                node.get("text")
                or node.get("content")
                or node.get("node_text")
                or node.get("paragraph")
                or json.dumps(node, ensure_ascii=False)
            )
            metadata = node.get("metadata", {}) if isinstance(node.get("metadata", {}), dict) else {}
            score = float(node.get("score") or node.get("relevance_score") or 1.0 / rank)

        results.append(
            {
                "content": content,
                "score": score,
                "metadata": {**metadata, "doc_id": doc_id, "retrieval_mode": "pageindex_cloud"},
                "source": "pageindex",
            }
        )
    return results


def _local_markdown_sections() -> list[dict]:
    sections = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        current_heading = md_file.stem
        current_lines: list[str] = []

        def flush() -> None:
            if current_lines:
                relative_path = md_file.relative_to(STANDARDIZED_DIR)
                sections.append(
                    {
                        "heading": current_heading,
                        "content": "\n".join(current_lines).strip(),
                        "metadata": {
                            "source": md_file.name,
                            "path": str(relative_path).replace("\\", "/"),
                            "type": relative_path.parts[0] if len(relative_path.parts) > 1 else "unknown",
                            "retrieval_mode": "local_pageindex_vectorless",
                        },
                    }
                )

        for line in content.splitlines():
            if re.match(r"^#{1,3}\s+", line):
                flush()
                current_heading = line.lstrip("#").strip()
                current_lines = [line]
            else:
                current_lines.append(line)
        flush()

    return sections


def _local_pageindex_search(query: str, top_k: int) -> list[dict]:
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return []

    scored = []
    for section in _local_markdown_sections():
        heading_tokens = set(_tokens(section["heading"]))
        content_tokens = set(_tokens(section["content"]))
        heading_overlap = len(query_tokens & heading_tokens)
        content_overlap = len(query_tokens & content_tokens)
        if heading_overlap == 0 and content_overlap == 0:
            continue

        score = (2.0 * heading_overlap + content_overlap) / max(len(query_tokens), 1)
        scored.append(
            {
                "content": section["content"][:2500],
                "score": float(score),
                "metadata": section["metadata"],
                "source": "pageindex",
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval using PageIndex.

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'
        }
    """
    if not query or top_k <= 0:
        return []

    doc_ids = _iter_doc_ids()
    if PAGEINDEX_API_KEY and doc_ids:
        results = []
        for doc_id in doc_ids:
            retrieval_id = _submit_pageindex_query(doc_id, query)
            if not retrieval_id:
                continue
            payload = _poll_retrieval(retrieval_id)
            results.extend(_normalize_pageindex_nodes(payload, doc_id))

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    return _local_pageindex_search(query, top_k)


if __name__ == "__main__":
    if PAGEINDEX_API_KEY and not _iter_doc_ids():
        print("Uploading documents to PageIndex...")
        upload_documents()

    print("\nTest query:")
    for result in pageindex_search("hình phạt sử dụng ma túy", top_k=3):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
