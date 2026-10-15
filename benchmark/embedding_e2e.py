"""Quick end-to-end benchmark for EmbeddingBatchWriter configurations.

Supports both FastEmbedProvider and LibEmbeddingProvider.
"""

from __future__ import annotations

import tempfile
import time

from whoosh import index
from whoosh.fields import ID, TEXT, Schema
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.embeddings.libembedding_provider import LibEmbeddingProvider
from whoosh_modern.fields import VECTOR
from whoosh_modern.indexing import EmbeddingBatchWriter

TEXTS = [
    f"This is sample document number {i} about machine learning and search."
    for i in range(200)
]

FASTEMBED_CONFIGS = [
    {"model": "BAAI/bge-small-en-v1.5", "batch_size": 32, "workers": 0, "label": "bge-small bs=32"},
    {"model": "BAAI/bge-small-en-v1.5", "batch_size": 64, "workers": 0, "label": "bge-small bs=64"},
    {
        "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "batch_size": 32,
        "workers": 0,
        "label": "multilingual bs=32",
    },
    {
        "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "batch_size": 64,
        "workers": 0,
        "label": "multilingual bs=64",
    },
    {
        "model": "BAAI/bge-small-en-v1.5",
        "batch_size": 32,
        "workers": 2,
        "label": "bge-small bs=32 workers=2",
    },
]

LIBEMBEDDING_CONFIGS = [
    {"model": "fast", "batch_size": 32, "workers": 0, "label": "libembed fast bs=32"},
    {"model": "balanced", "batch_size": 32, "workers": 0, "label": "libembed balanced bs=32"},
    {"model": "quality", "batch_size": 32, "workers": 0, "label": "libembed quality bs=32"},
    {"model": "fast", "batch_size": 64, "workers": 0, "label": "libembed fast bs=64"},
    {"model": "balanced", "batch_size": 64, "workers": 0, "label": "libembed balanced bs=64"},
]


def run_configs(configs: list[dict], provider_type: str) -> None:
    """Run benchmark for a list of configurations."""
    for cfg in configs:
        if provider_type == "fastembed":
            provider = FastEmbedProvider(model_name=cfg["model"])
        else:
            provider = LibEmbeddingProvider(model_name=cfg["model"])
        dim = provider.dimension

        with tempfile.TemporaryDirectory() as tmpdir:
            schema = Schema(
                id=ID(stored=True, unique=True),
                body=TEXT,
                body_vector=VECTOR(dimension=dim),
            )
            ix = index.create_in(tmpdir, schema)

            writer = EmbeddingBatchWriter(
                ix,
                embedding_provider=provider,
                text_field="body",
                vector_field="body_vector",
                batch_size=500,
                embedding_batch_size=cfg["batch_size"],
                workers=cfg["workers"],
            )

            t0 = time.perf_counter()
            for i in range(0, len(TEXTS), 50):
                batch = [
                    {"id": str(j), "body": TEXTS[j]}
                    for j in range(i, min(i + 50, len(TEXTS)))
                ]
                writer.add_batch(batch)
            writer.close()
            elapsed = time.perf_counter() - t0

            print(
                f"{cfg['label']:<35} | {elapsed:.2f}s | {len(TEXTS)/elapsed:.1f} docs/s"
            )


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="EmbeddingBatchWriter E2E benchmark")
    parser.add_argument(
        "--provider",
        choices=["fastembed", "libembedding", "both"],
        default="both",
        help="Embedding provider to benchmark",
    )
    args = parser.parse_args()

    if args.provider in ("fastembed", "both"):
        print("=== FastEmbedProvider ===")
        run_configs(FASTEMBED_CONFIGS, "fastembed")

    if args.provider in ("libembedding", "both"):
        print("\n=== LibEmbeddingProvider ===")
        run_configs(LIBEMBEDDING_CONFIGS, "libembedding")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())