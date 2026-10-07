"""Benchmark libembedding-ng vs FastEmbed on 3 corpora.

Uses TextEmbeddingPool for inter-session parallelism (3.6x speedup per
libembedding docs) when available, falling back to single TextEmbedding.

Measures throughput (docs/s) and latency (p95 ms) for LibEmbeddingProvider
and FastEmbedProvider on three corpora:
- stock-stockunitelegale-parquet (stock-entities)
- customers-2000000 (customers)
- all_latest (Wikipedia)

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np

from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.embeddings.libembedding_provider import LibEmbeddingProvider

CORPORA: list[dict[str, Any]] = [
    {
        "name": "stock-stockunitelegale-parquet",
        "path": "benchmark/Datas/stock-stockunitelegale-parquet.parquet",
        "text_field": "nom",
    },
    {
        "name": "customers-2000000",
        "path": "benchmark/Datas/customers-2000000.csv",
        "text_field": "name",
    },
    {
        "name": "all_latest",
        "path": "benchmark/Datas/all_latest",
        "text_field": "title",
    },
]


def _load_texts(corpora: list[str], max_texts: int = 2000) -> list[str]:
    """Load texts from the requested corpora."""
    texts: list[str] = []
    for corp in CORPORA:
        if corp["name"] not in corpora:
            continue
        path = Path(corp["path"])
        if not path.exists():
            continue
        if path.suffix == ".parquet":
            import pandas as pd

            df = pd.read_parquet(path)
            col = corp["text_field"]
            if col not in df.columns:
                col = df.columns[0]
            texts.extend(df[col].astype(str).tolist()[:max_texts])
        elif path.suffix == ".csv":
            import pandas as pd

            df = pd.read_csv(path)
            col = corp["text_field"]
            if col not in df.columns:
                col = df.columns[0]
            texts.extend(df[col].astype(str).tolist()[:max_texts])
        else:
            files = sorted(path.glob("*.txt"))[:max_texts]
            for f in files:
                texts.extend(f.read_text(encoding="utf-8", errors="ignore").splitlines()[:5])
    return texts[: max_texts * len(corpora)]


def _make_libembedding_pool(model_name: str = "balanced", workers: int = 4) -> Any:
    """Create a libembedding TextEmbeddingPool when available."""
    try:
        from libembedding import TextEmbeddingPool

        return TextEmbeddingPool(
            model_name,
            workers=workers,
            threads_per_worker=1,
            batch_size=64,
            offline=True,
        )
    except Exception:
        return LibEmbeddingProvider(model_name=model_name)


def _benchmark_provider(provider: Any, texts: list[str], batch_size: int = 32) -> dict[str, float]:
    """Benchmark a single provider on a list of texts."""
    single_times: list[float] = []
    for text in texts[:50]:
        t0 = time.perf_counter()
        provider.embed(text)
        single_times.append((time.perf_counter() - t0) * 1000)

    batch_times: list[float] = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        t0 = time.perf_counter()
        provider.embed_batch(chunk)
        batch_times.append((time.perf_counter() - t0) * 1000)

    total_ms = sum(batch_times)
    docs_per_sec = len(texts) / (total_ms / 1000)
    if len(single_times) >= 20:
        p95_single = statistics.quantiles(single_times, n=20)[18]
    else:
        p95_single = max(single_times)

    return {
        "docs_per_sec": docs_per_sec,
        "ms_per_doc": total_ms / len(texts),
        "p95_single_ms": p95_single,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark libembedding-ng vs FastEmbed")
    parser.add_argument(
        "--corpora",
        nargs="+",
        default=["stock-stockunitelegale-parquet", "customers-2000000", "all_latest"],
        choices=[c["name"] for c in CORPORA],
    )
    parser.add_argument("--max-texts", type=int, default=2000)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4, help="libembedding pool workers")
    args = parser.parse_args()

    texts = _load_texts(args.corpora, max_texts=args.max_texts)
    if not texts:
        print("No texts loaded. Check corpus paths.")
        return 1

    print(f"Loaded {len(texts)} texts from {args.corpora}")

    providers = {
        "libembedding": _make_libembedding_pool(workers=args.workers),
        "fastembed": FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5"),
    }

    for name, provider in providers.items():
        metrics = _benchmark_provider(provider, texts, batch_size=args.batch_size)
        print(
            f"{name:<15} | {metrics['docs_per_sec']:>8.1f} docs/s | "
            f"{metrics['ms_per_doc']:>6.2f} ms/doc | "
            f"p95={metrics['p95_single_ms']:>6.2f} ms"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())