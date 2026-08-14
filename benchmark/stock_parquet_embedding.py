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

from whoosh_modern.data_sources.parquet_ds import ParquetSource  # noqa: E402

BENCHMARK_DIR = ROOT / "benchmark"
PARQUET_PATH = BENCHMARK_DIR / "Datas" / "stock-stockunitelegale-parquet.parquet"

_TEXT_FIELDS = [
    "denominationUniteLegale",
    "denominationUsuelle1UniteLegale",
    "denominationUsuelle2UniteLegale",
    "denominationUsuelle3UniteLegale",
    "activitePrincipaleUniteLegale",
    "nomUniteLegale",
    "prenom1UniteLegale",
]


def _join_text(document: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for key, value in document.items()
        if key in _TEXT_FIELDS and isinstance(value, str) and value
    )


def run_embedding_benchmark(
    model_name: str = "all-MiniLM-L6-v2",
    max_docs: int | None = None,
) -> dict[str, Any]:
    try:
        from whoosh_modern.embeddings.sentence_transformers_provider import (
            SentenceTransformersProvider,
        )
    except ImportError as exc:
        raise ImportError(
            "SentenceTransformersProvider requires sentence-transformers. "
            "Install with: pip install whoosh-ng[embeddings]"
        ) from exc

    source = ParquetSource(
        path=str(PARQUET_PATH),
        incremental_field=None,
        id_field="siren",
    )

    provider = SentenceTransformersProvider(model_name=model_name)
    docs = 0
    total_ms = 0.0
    max_ms = 0.0
    min_ms = float("inf")
    empty = 0
    dims: int | None = None

    start = time.perf_counter()
    for document in source.iter_documents():
        if max_docs is not None and docs >= max_docs:
            break
        docs += 1
        text = _join_text(document)
        if not text:
            empty += 1
            continue
        t0 = time.perf_counter()
        vector = provider.embed(text)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        total_ms += elapsed_ms
        max_ms = max(max_ms, elapsed_ms)
        min_ms = min(min_ms, elapsed_ms)
        if dims is None:
            dims = len(vector)
    total_time_s = time.perf_counter() - start

    return {
        "dataset": str(PARQUET_PATH),
        "model": model_name,
        "docs": docs,
        "empty": empty,
        "embedded_docs": docs - empty,
        "dimension": dims,
        "total_embedding_ms": round(total_ms, 2),
        "per_doc_avg_ms": round(total_ms / docs, 3) if docs else 0.0,
        "per_doc_min_ms": round(min_ms, 3) if min_ms != float("inf") else 0.0,
        "per_doc_max_ms": round(max_ms, 3),
        "wall_clock_s": round(total_time_s, 3),
    }


if __name__ == "__main__":
    report = run_embedding_benchmark(max_docs=500)
    print("Embedding benchmark report")
    print(f"  dataset             : {report['dataset']}")
    print(f"  model               : {report['model']}")
    print(f"  docs                : {report['docs']}")
    print(f"  empty               : {report['empty']}")
    print(f"  embedded docs       : {report['embedded_docs']}")
    print(f"  dimension           : {report['dimension']}")
    print(f"  total embedding ms  : {report['total_embedding_ms']}")
    print(f"  per doc avg ms      : {report['per_doc_avg_ms']}")
    print(f"  per doc min/max ms  : {report['per_doc_min_ms']} / {report['per_doc_max_ms']}")
    print(f"  wall clock s        : {report['wall_clock_s']}")
