"""Embedding benchmark on the stock Parquet dataset.

Run with::

    python benchmark/stock_parquet_embedding.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark.utils import PARQUET_PATH, join_text_fields  # noqa: E402
from whoosh_modern.data_sources.parquet_ds import ParquetSource  # noqa: E402


def run_embedding_benchmark(
    model_name: str = "BAAI/bge-small-en-v1.5",
    provider: str = "fastembed",
    max_docs: int | None = None,
) -> dict[str, Any]:
    try:
        if provider == "fastembed":
            from whoosh_modern.embeddings.fastembed_provider import (
                FastEmbedProvider,
            )

            provider_cls = FastEmbedProvider
            provider_kwargs: dict[str, Any] = {"model_name": model_name}
        elif provider == "sentence-transformers":
            from whoosh_modern.embeddings.sentence_transformers_provider import (
                SentenceTransformersProvider,
            )

            provider_cls = SentenceTransformersProvider
            provider_kwargs = {"model_name": model_name}
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    except ImportError as exc:
        raise ImportError(
            f"Embedding provider '{provider}' requires additional dependencies. "
            f"Install with: pip install whoosh-ng[embeddings] or whoosh-ng[embeddings-onnx]"
        ) from exc

    source = ParquetSource(
        path=str(PARQUET_PATH),
        incremental_field=None,
        id_field="siren",
    )

    embedding_provider = provider_cls(**provider_kwargs)
    docs = 0
    total_ms = 0.0
    max_ms = 0.0
    min_ms = float("inf")
    empty = 0
    failures = 0
    embedded_docs = 0
    dims: int | None = None

    start = time.perf_counter()
    for document in source.iter_documents():
        if max_docs is not None and docs >= max_docs:
            break
        docs += 1
        text = join_text_fields(document)
        if not text:
            empty += 1
            continue
        t0 = time.perf_counter()
        try:
            vector = embedding_provider.embed(text)
        except Exception as exc:
            print(
                f"Warning: Embedding failed for doc {docs} "
                f"(ID: {document.get(source.id_field or '')}): {exc}",
                file=sys.stderr,
            )
            failures += 1
            continue
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        total_ms += elapsed_ms
        max_ms = max(max_ms, elapsed_ms)
        min_ms = min(min_ms, elapsed_ms)
        if dims is None:
            dims = len(vector)
        embedded_docs += 1
    total_time_s = time.perf_counter() - start

    actual_embedded_count = embedded_docs
    if actual_embedded_count == 0:
        avg_ms = 0.0
        min_ms_report = 0.0
    else:
        avg_ms = total_ms / actual_embedded_count
        min_ms_report = min_ms if min_ms != float("inf") else 0.0

    return {
        "dataset": str(PARQUET_PATH),
        "provider": provider,
        "model": model_name,
        "docs": docs,
        "empty": empty,
        "embedded_docs": actual_embedded_count,
        "dimension": dims,
        "total_embedding_ms": round(total_ms, 2),
        "per_doc_avg_ms": round(avg_ms, 3),
        "per_doc_min_ms": round(min_ms_report, 3),
        "per_doc_max_ms": round(max_ms, 3),
        "wall_clock_s": round(total_time_s, 3),
        "failures": failures,
    }


if __name__ == "__main__":
    report = run_embedding_benchmark(max_docs=500)
    print("Embedding benchmark report")
    print(f"  dataset             : {report['dataset']}")
    print(f"  provider            : {report.get('provider', 'fastembed')}")
    print(f"  model               : {report['model']}")
    print(f"  docs                : {report['docs']}")
    print(f"  empty               : {report['empty']}")
    print(f"  embedded docs       : {report['embedded_docs']}")
    print(f"  dimension           : {report['dimension']}")
    print(f"  total embedding ms  : {report['total_embedding_ms']}")
    print(f"  per doc avg ms      : {report['per_doc_avg_ms']}")
    print(f"  per doc min/max ms  : {report['per_doc_min_ms']} / {report['per_doc_max_ms']}")
    print(f"  wall clock s        : {report['wall_clock_s']}")
    print(f"  failures            : {report['failures']}")
