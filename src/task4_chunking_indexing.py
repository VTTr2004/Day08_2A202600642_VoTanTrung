"""
Task 4 - Chunking and indexing.

Chosen chunking strategy:
    MarkdownHeaderTextSplitter. Legal documents and news articles converted in
    Task 3 contain markdown headings such as "# title" and "## Page N", so this
    splitter preserves section/page context in chunk metadata before we enforce
    a fixed max chunk length.

Chosen embedding model:
    sentence-transformers/all-MiniLM-L6-v2. It is lightweight, fast enough for
    local classroom demos, and produces 384-dimensional vectors.

Chosen vector store:
    ChromaDB persistent store at data/index/chroma. This keeps the assignment
    runnable locally without a Docker/Cloud Weaviate service while using a real
    vector database API for Task 5 semantic search.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
CHROMA_DB_DIR = INDEX_DIR / "chroma"
CHROMA_COLLECTION_NAME = "drug_law_rag_chunks"
VECTOR_STORE_PATH = CHROMA_DB_DIR


# MarkdownHeaderTextSplitter keeps legal article/page/news-title structure.
# A 500-character window keeps chunks small enough for retrieval and test limits;
# 80 characters overlap preserves continuity across split points.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
CHUNKING_METHOD = "markdown_header"

# all-MiniLM-L6-v2 is compact and produces 384-dimensional sentence embeddings.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# ChromaDB persistent store: local, inspectable, and works offline for demos/tests.
VECTOR_STORE = "chromadb"


def load_documents() -> list[dict]:
    """
    Read all markdown files from data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str, ...}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_file.name.startswith("."):
            continue
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_path = md_file.relative_to(STANDARDIZED_DIR)
        doc_type = relative_path.parts[0] if len(relative_path.parts) > 1 else "unknown"
        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "path": str(relative_path).replace("\\", "/"),
                    "type": doc_type,
                },
            }
        )
    return documents


def _metadata_to_prefix(metadata: dict) -> str:
    header_parts = []
    for key in ("Header 1", "Header 2", "Header 3"):
        value = metadata.get(key)
        if value:
            header_parts.append(str(value))
    return " > ".join(header_parts)


def _window_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split long header sections into bounded overlapping text windows."""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        end = min(start + chunk_size, len(text))
        window = text[start:end]

        # Prefer ending at a natural boundary when possible.
        if end < len(text):
            boundary = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("; "))
            if boundary >= int(chunk_size * 0.6):
                end = start + boundary + 1
                window = text[start:end]

        chunks.append(window.strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + step)

    return [chunk for chunk in chunks if chunk]


def _split_with_langchain_markdown(content: str) -> list[dict]:
    from langchain_text_splitters import MarkdownHeaderTextSplitter

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )
    docs = splitter.split_text(content)
    return [{"content": doc.page_content, "metadata": dict(doc.metadata)} for doc in docs]


def _split_with_local_markdown_headers(content: str) -> list[dict]:
    """
    Small compatibility fallback for environments missing langchain-text-splitters.
    It follows the same "#", "##", "###" header boundaries used above.
    """
    sections = []
    current_lines = []
    current_metadata: dict[str, str] = {}
    active_headers: dict[int, str] = {}

    def flush():
        if current_lines:
            sections.append(
                {
                    "content": "\n".join(current_lines).strip(),
                    "metadata": dict(current_metadata),
                }
            )

    for line in content.splitlines():
        match = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        if match:
            flush()
            current_lines = [line]
            level = len(match.group(1))
            active_headers[level] = match.group(2).strip()
            for deeper_level in range(level + 1, 4):
                active_headers.pop(deeper_level, None)
            current_metadata = {
                f"Header {header_level}": value
                for header_level, value in sorted(active_headers.items())
            }
        else:
            current_lines.append(line)

    flush()
    return [section for section in sections if section["content"]]


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents with MarkdownHeaderTextSplitter, then enforce CHUNK_SIZE.

    Returns:
        List of {'content': str, 'metadata': dict}
    """
    chunks = []
    used_langchain = True

    for doc in documents:
        try:
            sections = _split_with_langchain_markdown(doc["content"])
        except ImportError:
            used_langchain = False
            sections = _split_with_local_markdown_headers(doc["content"])

        if not sections:
            sections = [{"content": doc["content"], "metadata": {}}]

        chunk_index = 0
        for section in sections:
            section_metadata = section.get("metadata", {})
            prefix = _metadata_to_prefix(section_metadata)
            section_text = section["content"]
            if prefix and not section_text.lstrip().startswith("#"):
                section_text = f"{prefix}\n\n{section_text}"

            for part in _window_text(section_text):
                metadata = {
                    **doc["metadata"],
                    **section_metadata,
                    "chunk_index": chunk_index,
                    "chunking_method": CHUNKING_METHOD,
                    "chunk_size": CHUNK_SIZE,
                    "chunk_overlap": CHUNK_OVERLAP,
                    "used_langchain_splitter": used_langchain,
                }
                chunks.append({"content": part, "metadata": metadata})
                chunk_index += 1

    return chunks


def _hash_embedding(text: str) -> list[float]:
    """
    Deterministic offline fallback for smoke tests only.

    Real indexing uses sentence-transformers/all-MiniLM-L6-v2. Set
    ALLOW_HASH_EMBEDDING_FALLBACK=1 if the model cannot be downloaded in class.
    """
    vector = [0.0] * EMBEDDING_DIM
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed all chunks with sentence-transformers/all-MiniLM-L6-v2.

    Returns:
        Each chunk dict gets an 'embedding': list[float] with 384 values.
    """
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(EMBEDDING_MODEL)
        texts = [chunk["content"] for chunk in chunks]
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding.tolist()
            chunk["metadata"]["embedding_model"] = EMBEDDING_MODEL
            chunk["metadata"]["embedding_dim"] = EMBEDDING_DIM
    except Exception as exc:
        if os.getenv("ALLOW_HASH_EMBEDDING_FALLBACK") != "1":
            raise RuntimeError(
                "Embedding requires sentence-transformers and the model "
                f"{EMBEDDING_MODEL}. Run `pip install -r requirements.txt`. "
                "If network/model download is unavailable for a classroom smoke "
                "test, set ALLOW_HASH_EMBEDDING_FALLBACK=1."
            ) from exc

        print(f"Embedding fallback enabled: {exc.__class__.__name__}")
        for chunk in chunks:
            chunk["embedding"] = _hash_embedding(chunk["content"])
            chunk["metadata"]["embedding_model"] = f"{EMBEDDING_MODEL} (hash fallback)"
            chunk["metadata"]["embedding_dim"] = EMBEDDING_DIM

    return chunks


def _sanitize_metadata(metadata: dict) -> dict:
    """Chroma metadata only accepts scalar values."""
    sanitized = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = str(value)
    return sanitized


def index_to_vectorstore(chunks: list[dict]) -> Path:
    """
    Save chunks and embeddings to the local ChromaDB vector store.

    Returns:
        Path to the ChromaDB persistence directory.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "ChromaDB is required for Task 4 indexing. "
            "Run `pip install chromadb` or `pip install -r requirements.txt`."
        ) from exc

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={
            "vector_store": VECTOR_STORE,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": EMBEDDING_DIM,
            "chunking_method": CHUNKING_METHOD,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        },
    )

    ids = []
    documents = []
    embeddings = []
    metadatas = []
    for chunk_id, chunk in enumerate(chunks):
        if "embedding" not in chunk:
            raise ValueError("Chunk is missing embedding. Run embed_chunks() before indexing.")
        ids.append(f"chunk-{chunk_id:06d}")
        documents.append(chunk["content"])
        embeddings.append(chunk["embedding"])
        metadatas.append(
            _sanitize_metadata(
                {
                    **chunk["metadata"],
                    "chunk_id": chunk_id,
                    "vector_store": VECTOR_STORE,
                    "embedding_model": chunk["metadata"].get("embedding_model", EMBEDDING_MODEL),
                    "embedding_dim": chunk["metadata"].get("embedding_dim", EMBEDDING_DIM),
                }
            )
        )

    batch_size = 500
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    return CHROMA_DB_DIR


def run_pipeline():
    """Run load -> chunk -> embed -> index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE} -> {VECTOR_STORE_PATH}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    index_path = index_to_vectorstore(chunks)
    print(f"Indexed to vector store: {index_path}")
    return index_path


if __name__ == "__main__":
    run_pipeline()
