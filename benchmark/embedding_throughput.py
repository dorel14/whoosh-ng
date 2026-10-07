"""Quick embedding throughput benchmark for FastEmbedProvider and LibEmbeddingProvider.

Measures docs/sec and ms/doc for single and batch embedding,
across multiple models if requested.
"""

from __future__ import annotations

import argparse
import statistics
import time
from typing import Any

from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.embeddings.libembedding_provider import LibEmbeddingProvider

FASTEMBED_MODELS = [
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-base-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "Xenova/e5-small-v2",
    "Xenova/e5-base-v2",
    "nomic-ai/nomic-embed-text-v1.5",
    "BAAI/bge-m3",
    "snowflake/snowflake-arctic-embed-s",
    "snowflake/snowflake-arctic-embed-m",
]

LIBEMBEDDING_PRESETS = ["fast", "balanced", "quality"]


def create_provider(provider_type: str, model_name: str) -> Any:
    """Create an embedding provider instance.

    Args:
        provider_type: "fastembed" or "libembedding"
        model_name: Model name or preset for the provider type
    """
    if provider_type == "fastembed":
        return FastEmbedProvider(model_name=model_name)
    elif provider_type == "libembedding":
        return LibEmbeddingProvider(model_name=model_name)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def benchmark_model(
    provider: Any,
    num_texts: int = 500,
    batch_size: int = 32,
) -> dict[str, str | int | float]:
    """Measure single and batch embedding throughput for one provider.

    Args:
        provider: Embedding provider instance (FastEmbedProvider or LibEmbeddingProvider)
        num_texts: Total number of sample texts to generate.
        batch_size: Batch size passed to ``embed_batch``.

    Returns:
        Dictionary with the model name, embedding dimension, and the
        computed throughput metrics.
    """

    texts = [
        f"This is sample document number {i} about machine learning and search."
        for i in range(num_texts)
    ]

    single_times: list[float] = []
    for text in texts[:50]:
        start = time.perf_counter()
        vec = provider.embed(text)
        elapsed = time.perf_counter() - start
        single_times.append(elapsed * 1000)

    batch_times: list[float] = []
    dimension = None
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        start = time.perf_counter()
        vecs = provider.embed_batch(chunk)
        elapsed = time.perf_counter() - start
        batch_times.append(elapsed * 1000)
        assert len(vecs) == len(chunk)
        if dimension is None:
            dimension = len(vecs[0]) if vecs else None

    single_mean = statistics.mean(single_times)
    batch_total_ms = sum(batch_times)
    batch_docs = len(texts)
    batch_ms_per_doc = batch_total_ms / batch_docs
    batch_docs_per_sec = batch_docs / (batch_total_ms / 1000)

    return {
        "model": getattr(provider, "_model_name", str(provider)),
        "dimension": dimension,
        "single_ms_mean": single_mean,
        "batch_ms_per_doc": batch_ms_per_doc,
        "batch_docs_per_sec": batch_docs_per_sec,
    }


def main() -> int:
    """Run the throughput benchmark across the requested models."""
    parser = argparse.ArgumentParser(description="Embedding throughput benchmark")
    parser.add_argument(
        "--provider",
        choices=["fastembed", "libembedding", "both"],
        default="both",
        help="Embedding provider to benchmark",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Models/presets to benchmark (default: all for provider)",
    )
    parser.add_argument(
        "--num-texts",
        type=int,
        default=500,
        help="Number of texts for batch benchmark",
    )
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size for embed_batch"
    )
    args = parser.parse_args()

    results = []

    if args.provider in ("fastembed", "both"):
        models = args.models or FASTEMBED_MODELS
        for model in models:
            print(f"Benchmarking FastEmbed {model}...", flush=True)
            try:
                provider = FastEmbedProvider(model_name=model)
                result = benchmark_model(
                    provider, num_texts=args.num_texts, batch_size=args.batch_size
                )
                result["provider"] = "fastembed"
                results.append(result)
            except Exception as exc:  # noqa: BLE001
                print(f"  ERROR: {exc}")
                continue

    if args.provider in ("libembedding", "both"):
        presets = args.models or LIBEMBEDDING_PRESETS
        for preset in presets:
            print(f"Benchmarking libembedding '{preset}'...", flush=True)
            try:
                provider = LibEmbeddingProvider(model_name=preset)
                result = benchmark_model(
                    provider, num_texts=args.num_texts, batch_size=args.batch_size
                )
                result["provider"] = "libembedding"
                results.append(result)
            except Exception as exc:  # noqa: BLE001
                print(f"  ERROR: {exc}")
                continue

    print("\nEmbedding CPU Throughput")
    print("=" * 85)
    print(f"{'Provider':<12} {'Model/Preset':<30} {'docs/s':>10} {'ms/doc':>10} {'dim':>5}")
    print("-" * 85)
    for r in results:
        print(
            f"{r['provider']:<12} {r['model']:<30} {r['batch_docs_per_sec']:>10.1f} "
            f"{r['batch_ms_per_doc']:>10.2f} {r['dimension']:>5}"
        )
    print("=" * 85)

    print("\nSingle-request latency (mean over 50 calls)")
    print("-" * 85)
    print(f"{'Provider':<12} {'Model/Preset':<30} {'ms/call':>10}")
    print("-" * 85)
    for r in results:
        print(f"{r['provider']:<12} {r['model']:<30} {r['single_ms_mean']:>10.2f}")
    print("=" * 85)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())