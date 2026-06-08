"""Ingestion and chunking pipeline for the home finance knowledge project.

This script follows the planning.md spec:
- Document ingestion from ./documents/raw_material
- Chunking with 400-token chunks and 80-token overlap
- Embeddings with all-MiniLM-L6-v2
- Vector storage using Chroma
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Iterable

CHUNK_SIZE = 400
OVERLAP = 80
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_SOURCE_DIR = Path(__file__).resolve().parent / "documents" / "raw_material"
DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent / "chroma_store"


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    """Tokenize text on whitespace for chunking.

    This is an approximation of model tokens; it is stable and avoids
    requiring a full tokenizer dependency.
    """
    return re.findall(r"\S+", text)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Split text into overlapping chunks for retrieval.

    Uses token-based windows so that each chunk is roughly the target size,
    with a small overlap to preserve continuity.
    """
    text = normalize_text(text)
    tokens = tokenize(text)
    if len(tokens) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))
        if end == len(tokens):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def list_markdown_files(root_dir: Path) -> Iterable[Path]:
    """Yield the markdown files under the source directory."""
    for path in sorted(root_dir.rglob("*.md")):
        if path.name.startswith("."):
            continue
        if path.is_file():
            yield path


def load_documents(root_dir: Path) -> list[dict]:
    """Load markdown document text and metadata for each source file."""
    root_dir = root_dir.resolve()
    documents: list[dict] = []
    for path in list_markdown_files(root_dir):
        if path.name == ".stignore":
            continue
        text = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(root_dir)
        documents.append({
            "source_path": str(relative_path.as_posix()),
            "text": text,
        })
    return documents


def build_chunks(documents: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    """Produce chunked documents with metadata for ingestion."""
    chunks: list[dict] = []
    for doc in documents:
        source_path = doc["source_path"]
        for index, chunk in enumerate(chunk_text(doc["text"], chunk_size=chunk_size, overlap=overlap)):
            chunks.append({
                "id": f"{source_path}#{index}",
                "text": chunk,
                "metadata": {
                    "source_path": source_path,
                    "chunk_index": index,
                },
            })
    return chunks


def create_chroma_collection(chunks: list[dict], collection_name: str, persist_dir: Path, model_name: str) -> None:
    """Ingest chunks into a local Chroma collection using SentenceTransformer embeddings."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError as exc:
        raise ImportError(
            "chromadb is required to run ingest.py. Install requirements with `pip install -r requirements.txt`."
        ) from exc

    persist_dir.mkdir(parents=True, exist_ok=True)

    # Use the new Chroma PersistentClient API (works with chromadb >= 0.4)
    client = chromadb.PersistentClient(path=str(persist_dir))

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name,
        device="cpu",
    )

    if collection_name in [c.name for c in client.list_collections()]:
        collection = client.get_collection(name=collection_name)
    else:
        collection = client.create_collection(name=collection_name, embedding_function=embedding_function)

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest and chunk markdown documents for retrieval.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="Root directory of raw markdown documents.")
    parser.add_argument("--persist-dir", type=Path, default=DEFAULT_PERSIST_DIR, help="Directory to persist the Chroma vector store.")
    parser.add_argument("--collection-name", default="home_finance", help="Name of the Chroma collection.")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Chunk size in tokens.")
    parser.add_argument("--overlap", type=int, default=OVERLAP, help="Overlap size in tokens.")
    parser.add_argument("--model", default=EMBEDDING_MODEL, help="SentenceTransformer model for embeddings.")
    args = parser.parse_args()

    if not args.source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {args.source_dir}")

    print(f"Loading markdown files from {args.source_dir}")
    documents = load_documents(args.source_dir)
    print(f"Loaded {len(documents)} documents")

    chunks = build_chunks(documents, chunk_size=args.chunk_size, overlap=args.overlap)
    print(f"Created {len(chunks)} chunks with size={args.chunk_size} overlap={args.overlap}")

    print(f"Ingesting chunks into Chroma at {args.persist_dir}")
    create_chroma_collection(chunks, collection_name=args.collection_name, persist_dir=args.persist_dir, model_name=args.model)
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
