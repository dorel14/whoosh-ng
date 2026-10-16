"""Example: Embeddings with LibEmbeddingProvider (libembedding-ng).

Install:
    pip install whoosh-ng[libembedding]

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from whoosh_modern.embeddings import LibEmbeddingProvider


def main() -> None:
    provider = LibEmbeddingProvider()
    vector = provider.embed("hello world")
    print(f"Dimension: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")

    batch = provider.embed_batch(["hello", "world"])
    print(f"Batch size: {len(batch)}")


if __name__ == "__main__":
    main()
