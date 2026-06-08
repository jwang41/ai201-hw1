#!/usr/bin/env python3
"""
Setup and cache the all-MiniLM-L6-v2 embedding model locally.

This script downloads and caches the sentence-transformers embedding model
specified in planning.md (all-MiniLM-L6-v2). Running this ensures the model
is available offline before the pipeline executes.

Model: all-MiniLM-L6-v2
- Compact multilingual model (22M parameters)
- Fast inference on CPU
- Good support for Chinese/English financial terminology
- ~80 MB download size
"""

import os
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer


def setup_embedding_model(
    model_name: str = "all-MiniLM-L6-v2",
    cache_dir: str = None,
):
    """
    Download and cache the embedding model locally.
    
    Args:
        model_name (str): HuggingFace model identifier (default: all-MiniLM-L6-v2)
        cache_dir (str): Optional cache directory (defaults to ~/.cache/huggingface)
    
    Returns:
        SentenceTransformer: Loaded model instance
    """
    print(f"Setting up embedding model: {model_name}")
    print("=" * 70)

    # Set cache directory if specified
    if cache_dir:
        os.environ["HF_HOME"] = cache_dir
        print(f"Cache directory: {cache_dir}")

    try:
        print(f"Downloading and caching {model_name}...")
        model = SentenceTransformer(model_name)
        
        print(f"✓ Model loaded successfully")
        print(f"  Model name: {model_name}")
        print(f"  Embedding dimension: {model.get_sentence_embedding_dimension()}")
        print(f"  Max sequence length: {model.max_seq_length}")
        
        # Test embedding on sample texts
        print("\nTesting embedding on sample texts...")
        sample_texts = [
            "Emergency fund reserves",
            "紧急基金",
            "Backdoor Roth IRA conversion strategy",
        ]
        embeddings = model.encode(sample_texts)
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"  Embedding shape: {embeddings[0].shape}")
        print(f"  Embedding type: {embeddings[0].dtype}")
        
        print("\n" + "=" * 70)
        print("✓ Embedding model setup complete!")
        print(f"  Ready for use in ingest.py and retrieval.py")
        
        return model

    except Exception as e:
        print(f"✗ Error downloading/loading model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup and cache the all-MiniLM-L6-v2 embedding model"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="HuggingFace model identifier (default: all-MiniLM-L6-v2)",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="Optional cache directory for model files",
    )

    args = parser.parse_args()
    setup_embedding_model(model_name=args.model, cache_dir=args.cache_dir)
