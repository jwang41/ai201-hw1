#!/usr/bin/env python3
"""
Retrieval module for household finance knowledge system.

Uses the Chroma vector store (created by ingest.py) to retrieve
the top-6 most relevant chunks for a given query, using the
all-MiniLM-L6-v2 embedding model as specified in planning.md.

Follows the Retrieval Approach from planning.md:
- Embedding model: all-MiniLM-L6-v2
- Top-k: 6 chunks per query
- Multilingual support for Chinese/English household finance documents
- Returns results with source attribution for generation stage
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple

import chromadb


def get_chroma_client():
    """
    Initialize Chroma client pointing to persistent vector store.
    
    Returns:
        chromadb.Client: Connected client with local persistent storage
    """
    chroma_dir = Path("./chroma_store")
    # Use the new Chroma PersistentClient API
    client = chromadb.PersistentClient(path=str(chroma_dir))
    return client


def retrieve_chunks(
    query: str,
    collection_name: str = "household_finance",
    top_k: int = 6,
) -> List[Dict]:
    """
    Retrieve top-k chunks from vector store using semantic similarity.
    
    Args:
        query (str): Natural language query (English or Chinese)
        collection_name (str): Name of Chroma collection (default: household_finance)
        top_k (int): Number of top results to retrieve (default: 6 per planning.md spec)
    
    Returns:
        List[Dict]: List of retrieved chunks with metadata and source attribution.
                   Each dict contains:
                   - id: chunk identifier (source_path#chunk_index)
                   - source: original document source path
                   - chunk_index: index within source document
                   - text: chunk content
                   - distance: embedding similarity distance (lower = more similar)
    """
    try:
        client = get_chroma_client()
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load Chroma collection '{collection_name}'. "
            f"Ensure ingest.py has been run to populate the vector store. Error: {e}"
        )

    # Query the collection using semantic search
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # Parse results into structured format with source attribution
    retrieved = []
    if results["documents"] and len(results["documents"]) > 0:
        for i, (doc, metadata, distance) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ):
            retrieved.append({
                "id": metadata.get("id", f"unknown_{i}"),
                "source": metadata.get("source", "unknown"),
                "chunk_index": metadata.get("chunk_index", i),
                "text": doc,
                "distance": distance,
            })

    return retrieved


def format_retrieval_context(
    retrieved_chunks: List[Dict],
    include_distances: bool = False,
) -> str:
    """
    Format retrieved chunks into a context string for the generation stage.
    
    Args:
        retrieved_chunks (List[Dict]): Output from retrieve_chunks()
        include_distances (bool): Whether to include similarity distances in output
    
    Returns:
        str: Formatted context with source attribution
    """
    if not retrieved_chunks:
        return "No relevant documents found."

    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        source = chunk.get("source", "unknown")
        text = chunk.get("text", "")
        distance = chunk.get("distance", 0)

        # Format: [Source: path] {similarity info if requested} Content...
        header = f"[Chunk {i} from {source}]"
        if include_distances:
            header += f" (similarity: {distance:.4f})"

        context_parts.append(f"{header}\n{text}")

    return "\n\n".join(context_parts)


def retrieve_and_format(
    query: str,
    top_k: int = 6,
    include_distances: bool = False,
) -> Tuple[str, List[Dict]]:
    """
    Convenience function combining retrieval and formatting.
    
    Args:
        query (str): User query
        top_k (int): Number of chunks to retrieve (default: 6)
        include_distances (bool): Include similarity scores in formatted output
    
    Returns:
        Tuple[str, List[Dict]]: (formatted_context_string, raw_retrieved_chunks)
    """
    chunks = retrieve_chunks(query, top_k=top_k)
    formatted = format_retrieval_context(chunks, include_distances=include_distances)
    return formatted, chunks


def evaluate_retrieval(
    test_questions: List[Dict],
    verbose: bool = True,
) -> Dict:
    """
    Evaluate retrieval quality on test questions from planning.md.
    
    Args:
        test_questions (List[Dict]): List of test question dicts with 'question' and 'expected_answer' keys
        verbose (bool): Print detailed retrieval results
    
    Returns:
        Dict: Evaluation metrics including number of queries, avg chunks retrieved, etc.
    """
    stats = {
        "total_queries": len(test_questions),
        "total_chunks_retrieved": 0,
        "queries": []
    }

    for q_num, q_dict in enumerate(test_questions, 1):
        question = q_dict.get("question", "")
        expected = q_dict.get("expected_answer", "")

        if not question:
            continue

        chunks = retrieve_chunks(question)
        stats["total_chunks_retrieved"] += len(chunks)

        query_result = {
            "question_number": q_num,
            "question": question,
            "expected_answer": expected,
            "retrieved_count": len(chunks),
            "sources": [c.get("source", "unknown") for c in chunks],
        }
        stats["queries"].append(query_result)

        if verbose:
            print(f"\n{'='*70}")
            print(f"Question {q_num}: {question}")
            print(f"Expected: {expected}")
            print(f"Retrieved {len(chunks)} chunks from:")
            for c in chunks:
                src = c.get("source", "unknown")
                print(f"  - {src}")

    if verbose:
        avg_chunks = stats["total_chunks_retrieved"] / max(stats["total_queries"], 1)
        print(f"\n{'='*70}")
        print(f"Retrieval Evaluation Summary")
        print(f"  Total queries: {stats['total_queries']}")
        print(f"  Total chunks retrieved: {stats['total_chunks_retrieved']}")
        print(f"  Avg chunks per query: {avg_chunks:.1f}")

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Retrieve and evaluate chunks from household finance knowledge base"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query string (Chinese or English)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=6,
        help="Number of chunks to retrieve (default: 6)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run evaluation on 5 test questions from planning.md",
    )
    parser.add_argument(
        "--distances",
        action="store_true",
        help="Include similarity distances in output",
    )

    args = parser.parse_args()

    if args.query:
        print(f"Query: {args.query}\n")
        formatted, chunks = retrieve_and_format(
            args.query,
            top_k=args.top_k,
            include_distances=args.distances,
        )
        print(formatted)
        print(f"\n[Retrieved {len(chunks)} chunks with top-k={args.top_k}]")

    elif args.evaluate:
        # Test questions from planning.md Evaluation Plan section
        test_questions = [
            {
                "question": "What emergency fund size does the household finance material recommend?",
                "expected_answer": "A reserve of about 3–6 months of living expenses.",
            },
            {
                "question": "Which account types are described as tax-efficient for retirement savings and what is a Backdoor Roth IRA?",
                "expected_answer": "Use tax-advantaged retirement accounts, Roth for tax-free growth, and a Backdoor Roth IRA is a strategy to contribute to Roth via nondeductible traditional IRA conversions when direct Roth contributions are limited.",
            },
            {
                "question": "How should families prioritize debt repayment and insurance planning?",
                "expected_answer": "Prioritize high-interest debt first and maintain adequate insurance coverage like term life, health, and property/casualty protection as part of household financial defense.",
            },
            {
                "question": "What asset location guidance is given for taxable, tax-deferred, and tax-free accounts?",
                "expected_answer": "Hold tax-inefficient assets like bonds in tax-deferred accounts, tax-efficient equities in taxable or Roth accounts, and use Roth for assets expected to grow most.",
            },
            {
                "question": "What is the 4% rule and what main caution is noted for retirement withdrawals?",
                "expected_answer": "Withdraw about 4% of the portfolio in the first year and adjust thereafter, while watching sequence-of-returns risk and longevity/inflation sensitivity.",
            },
        ]

        evaluate_retrieval(test_questions, verbose=True)

    else:
        print("Use --query to retrieve chunks or --evaluate to test retrieval quality")
        print("Example: python retrieval.py --query 'emergency fund size'")
        print("Example: python retrieval.py --evaluate")
