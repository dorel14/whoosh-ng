"""Benchmark language detection on the stock Parquet dataset.

Run with::

    python benchmark/stock_parquet_langauto.py
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark import WhooshLikeSpec
from benchmark.utils import BENCHMARK_DIR, PARQUET_PATH, join_text_fields  # noqa: E402
from whoosh_modern.config.engine import ConfigEngine as DirectConfigEngine  # noqa: E402
from whoosh_modern.config.engines import LanguageEngine  # noqa: E402
from whoosh_modern.data_sources.parquet_ds import ParquetSource  # noqa: E402

BENCHMARK_DIR = ROOT / "benchmark"
YAML_PATH = BENCHMARK_DIR / "benchmark_data" / "stock-parquet-langauto.yml"


def _ensure_yaml() -> None:
    YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    if YAML_PATH.exists():
        return
    YAML_PATH.write_text(
        f"""\
index: stock_parquet_langauto
fields:
  siren:
    type: id
    stored: true
  denominationUniteLegale:
    type: text
    language: auto
    stemming: true
    stored: true
  denominationUsuelle1UniteLegale:
    type: text
    language: auto
    stemming: true
    stored: true
  denominationUsuelle2UniteLegale:
    type: text
    language: auto
    stemming: true
    stored: true
  denominationUsuelle3UniteLegale:
    type: text
    language: auto
    stemming: true
    stored: true
  activitePrincipaleUniteLegale:
    type: text
    language: auto
    stemming: true
    stored: true
  nomUniteLegale:
    type: text
    language: auto
    stored: true
  prenom1UniteLegale:
    type: text
    language: auto
    stored: true
language_detection:
  provider: stopword
  supported_languages:
    - fr
    - en
    - de
    - es
    - it
search:
  fuzzy:
    enabled: true
    distance: 2
data_source:
  type: parquet
  path: {PARQUET_PATH}
storage:
  type: file
  path: {BENCHMARK_DIR / "indexes" / "stock_parquet_langauto_index"}
"""
    )


class StockParquetLangAuto(WhooshLikeSpec):
    name = "stock_parquet_langauto"
    main_field = "denominationUsuelle1UniteLegale"
    headline_field = "denominationUsuelle1UniteLegale"
    default_query = "SNCF"

    def __init__(self, options: Any, args: Any) -> None:
        super().__init__(options, args)
        _ensure_yaml()
        engine = DirectConfigEngine()
        engine.load(YAML_PATH, priority="application")
        config = engine.get_config()
        ds_config = config.data_source
        assert ds_config is not None
        self._source = ParquetSource(
            path=ds_config.path or str(PARQUET_PATH),
            incremental_field=None,
            id_field="siren",
        )

    def whoosh_schema(self) -> Any:
        return self._source.discover_schema()

    def documents(self) -> Any:
        yield from self._source.iter_documents()

    def batches(self, batch_size: int = 1000) -> Any:
        yield from self._source.stream_batches(batch_size=batch_size)


def run_language_detection_benchmark(max_docs: int | None = None) -> dict[str, Any]:
    _ensure_yaml()
    engine = DirectConfigEngine()
    engine.load(YAML_PATH, priority="application")
    config = engine.get_config()
    ds_config = config.data_source
    assert ds_config is not None

    detector = LanguageEngine(config).build()
    if detector is None:
        raise RuntimeError("No language detector built from config")

    source = ParquetSource(
        path=ds_config.path or str(PARQUET_PATH),
        incremental_field=None,
        id_field="siren",
    )

    docs = 0
    detected: Counter[str] = Counter()
    failures = 0
    empty_texts = 0
    detection_failures = 0
    total_ms = 0.0
    max_ms = 0.0
    min_ms = float("inf")
    processed_texts_count = 0

    start = time.perf_counter()
    for document in source.iter_documents():
        if max_docs is not None and docs >= max_docs:
            break
        docs += 1
        text = join_text_fields(document)
        if not text:
            failures += 1
            empty_texts += 1
            continue
        processed_texts_count += 1
        t0 = time.perf_counter()
        try:
            lang = detector.detect(text)
        except Exception as exc:
            print(
                f"Warning: Language detection failed for doc {docs} "
                f"(ID: {document.get(source.id_field or '')}): {exc}",
                file=sys.stderr,
            )
            detection_failures += 1
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            total_ms += elapsed_ms
            max_ms = max(max_ms, elapsed_ms)
            min_ms = min(min_ms, elapsed_ms)
            continue
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        total_ms += elapsed_ms
        max_ms = max(max_ms, elapsed_ms)
        min_ms = min(min_ms, elapsed_ms)
        if lang:
            detected[lang] += 1
        else:
            failures += 1
            detection_failures += 1
    total_time_s = time.perf_counter() - start

    accuracy = (detected.get("fr", 0) / docs * 100.0) if docs else 0.0
    fr_accuracy_pct = (
        (detected.get("fr", 0) / processed_texts_count * 100.0)
        if processed_texts_count
        else 0.0
    )
    avg_ms = total_ms / processed_texts_count if processed_texts_count else 0.0
    min_ms_report = min_ms if min_ms != float("inf") else 0.0
    return {
        "dataset": str(PARQUET_PATH),
        "docs": docs,
        "detected_languages": dict(detected.most_common()),
        "fr_accuracy_pct": round(accuracy, 2),
        "failures": failures,
        "fr_accuracy_pct_processed": round(fr_accuracy_pct, 2),
        "empty_texts": empty_texts,
        "detection_failures": detection_failures,
        "successfully_processed_texts": processed_texts_count - detection_failures,
        "total_detection_ms": round(total_ms, 2),
        "per_doc_avg_ms": round(avg_ms, 3),
        "per_doc_min_ms": round(min_ms_report, 3),
        "per_doc_max_ms": round(max_ms, 3),
        "wall_clock_s": round(total_time_s, 3),
    }


if __name__ == "__main__":
    report = run_language_detection_benchmark()
    print("Language detection benchmark report")
    print(f"  dataset                    : {report['dataset']}")
    print(f"  docs                       : {report['docs']}")
    print(f"  detected languages         : {report['detected_languages']}")
    print(f"  fr accuracy                : {report['fr_accuracy_pct']}%")
    print(f"  failures                   : {report['failures']}")
    print(
        f"  fr accuracy (processed)    : {report['fr_accuracy_pct_processed']}% "
        "(of successfully processed)"
    )
    print(f"  empty texts                : {report['empty_texts']}")
    print(f"  detection failures         : {report['detection_failures']}")
    print(f"  total detection ms         : {report['total_detection_ms']}")
    print(f"  per doc avg ms             : {report['per_doc_avg_ms']}")
    print(f"  per doc min/max ms         : {report['per_doc_min_ms']} / {report['per_doc_max_ms']}")
    print(f"  wall clock s               : {report['wall_clock_s']}")
