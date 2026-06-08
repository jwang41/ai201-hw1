"""Implement chunking strategy from planning.md.

Chunk size: 400 tokens
Overlap: 80 tokens
Reasoning: Short-to-medium household finance documents benefit from 400-token chunks
that keep each chunk focused on a single concept, with 80-token overlap to preserve
sentence continuity and prevent splitting key financial recommendations.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

DEFAULT_CLEANED_DIR = Path(__file__).resolve().parent / "data" / "cleaned_text"
DEFAULT_CHUNKS_DIR = Path(__file__).resolve().parent / "data" / "chunked_text"

# From planning.md
CHUNK_SIZE = 400  # tokens
OVERLAP = 80      # tokens


def tokenize_text(text: str) -> list[str]:
    """Tokenize text by splitting on whitespace.
    
    This approximates model tokenization without requiring a full tokenizer.
    Each token is roughly equivalent to a word or punctuation mark.
    """
    return re.findall(r"\S+", text)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Split text into overlapping chunks for retrieval.
    
    Uses token-based windows: each chunk contains ~chunk_size tokens,
    with overlap tokens carried over to the next chunk to preserve context.
    
    Args:
        text: The text to chunk.
        chunk_size: Target number of tokens per chunk.
        overlap: Number of tokens to overlap between adjacent chunks.
    
    Returns:
        List of chunk strings.
    """
    text = text.strip()
    tokens = tokenize_text(text)
    
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
        
        # Move start forward by (chunk_size - overlap)
        # This ensures overlap tokens carry over to next chunk
        start = end - overlap
        if start < 0:
            start = 0
    
    return chunks


def collect_cleaned_files(cleaned_dir: Path) -> Iterable[Path]:
    """Yield all .txt files under cleaned_dir, excluding manifests and hidden files."""
    cleaned_dir = cleaned_dir.resolve()
    if not cleaned_dir.exists():
        return []
    for path in sorted(cleaned_dir.rglob("*.txt")):
        if not path.name.startswith(".") and "manifest" not in path.name.lower():
            yield path


def create_chunk_id(source_path: str, chunk_index: int) -> str:
    """Create a stable ID for a chunk."""
    return f"{source_path}#{chunk_index}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Implement chunking strategy: 400-token chunks with 80-token overlap."
    )
    parser.add_argument(
        "--cleaned-dir",
        type=Path,
        default=DEFAULT_CLEANED_DIR,
        help="Directory containing cleaned text files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_CHUNKS_DIR,
        help="Directory to save chunked text files.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help="Number of tokens per chunk.",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=OVERLAP,
        help="Number of tokens to overlap between chunks.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Chunking documents from {args.cleaned_dir}")
    print(f"Strategy: chunk_size={args.chunk_size} tokens, overlap={args.overlap} tokens")

    chunking_manifest: list[dict] = []
    total_chunks = 0

    for cleaned_path in collect_cleaned_files(args.cleaned_dir):
        cleaned_text = cleaned_path.read_text(encoding="utf-8")
        chunks = chunk_text(cleaned_text, chunk_size=args.chunk_size, overlap=args.overlap)

        relative = cleaned_path.relative_to(args.cleaned_dir)
        source_id = str(relative.with_suffix("").as_posix())

        # Save chunks as JSONL (one chunk per line)
        chunks_dir = output_dir / relative.parent
        chunks_dir.mkdir(parents=True, exist_ok=True)
        chunks_file = chunks_dir / f"{relative.stem}.jsonl"

        with chunks_file.open("w", encoding="utf-8") as fh:
            for chunk_index, chunk_text_str in enumerate(chunks):
                chunk_id = create_chunk_id(source_id, chunk_index)
                chunk_obj = {
                    "id": chunk_id,
                    "source": source_id,
                    "chunk_index": chunk_index,
                    "text": chunk_text_str,
                    "tokens": len(tokenize_text(chunk_text_str)),
                }
                fh.write(json.dumps(chunk_obj, ensure_ascii=False) + "\n")

        chunking_manifest.append({
            "source": source_id,
            "chunks_file": str(chunks_file.relative_to(output_dir).as_posix()),
            "chunk_count": len(chunks),
            "input_tokens": len(tokenize_text(cleaned_text)),
        })

        total_chunks += len(chunks)
        print(f"Chunked {relative}: {len(chunks)} chunks")

    if chunking_manifest:
        manifest_path = output_dir / "chunking_manifest.jsonl"
        with manifest_path.open("w", encoding="utf-8") as fh:
            for entry in chunking_manifest:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Total: {total_chunks} chunks from {len(chunking_manifest)} documents")
        print(f"Chunking manifest saved to {manifest_path}")
    else:
        print("No cleaned documents found to chunk.")


if __name__ == "__main__":
    main()
