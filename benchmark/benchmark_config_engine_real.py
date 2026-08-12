"""Benchmark ConfigEngine on the real large customers CSV (2M rows).

Compares ``ConfigEngine`` overhead against equivalent manual Whoosh-NG setup
on a real-world dataset to ensure configuration loading/merging does not
introduce measurable regressions.

Run with::

    python -m benchmark --spec benchmark_config_engine_real --pytest-args="--benchmark-only"
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.config import ConfigEngine
from whoosh_modern.config.engine import ConfigEngine as DirectConfigEngine
from whoosh_modern.config.loader import load_yaml

BENCHMARK_DIR = pytest.importorskip("pathlib").Path(__file__).parent
CSV_PATH = BENCHMARK_DIR / "Datas" / "customers-2000000.csv"
YAML_PATH = BENCHMARK_DIR / "benchmark_data" / "customers-whoosh-ng.yml"


def _ensure_yaml() -> None:
    YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not YAML_PATH.exists():
        YAML_PATH.write_text(
            """\
index: customers_benchmark
fields:
  Customer_Id:
    type: numeric
    stored: true
    sortable: true
  First_Name:
    type: text
    language: en
    stemming: true
    stored: true
  Last_Name:
    type: text
    language: en
    stemming: true
    stored: true
  City:
    type: text
    language: en
    stemming: true
    stored: true
  State:
    type: text
    stored: true
  Country:
    type: text
    stored: true
  Phone_1:
    type: text
    stored: true
  Phone_2:
    type: text
    stored: true
  Email:
    type: text
    stored: true
  Gender:
    type: text
    stored: true
  Purchase:
    type: numeric
    sortable: true
search:
  fuzzy:
    enabled: true
    distance: 2
data_source:
  type: csv
  path: Datas/customers-2000000.csv
  delimiter: ","
  encoding: utf-8
storage:
  type: file
  path: ./benchmark_indexes/customers_config_engine
""",
            encoding="utf-8",
        )


class BenchmarkConfigEngineReal:
    """Benchmark suite for ConfigEngine on a real 2M-row CSV."""

    def setup_method(self) -> None:
        _ensure_yaml()
        assert CSV_PATH.exists(), f"Missing benchmark data: {CSV_PATH}"

    def benchmark_load_yaml_direct(self, benchmark) -> None:
        """Baseline: raw YAML load without ConfigEngine."""
        benchmark(load_yaml, YAML_PATH)

    def benchmark_config_engine_load(self, benchmark) -> None:
        """ConfigEngine.load() from real YAML config."""
        engine = DirectConfigEngine()
        benchmark(engine.load, YAML_PATH, priority="application")

    def benchmark_config_engine_build(self, benchmark) -> None:
        """ConfigEngine.build() end-to-end on real CSV config."""
        engine = DirectConfigEngine()
        engine.load(YAML_PATH, priority="application")
        benchmark(engine.build)

    def benchmark_manual_build(self, benchmark) -> None:
        """Baseline: manual SearchApplication setup without ConfigEngine."""

        def _manual_build() -> None:
            from whoosh_modern.application import SearchApplication
            from whoosh_modern.data_sources.fast_csv import FastCSVSource
            from whoosh_modern.storage import FileStorage

            source = FastCSVSource(
                path=str(CSV_PATH),
                delimiter=",",
                encoding="utf-8",
                id_field="Customer Id",
            )
            storage = FileStorage("./benchmark_indexes/customers_manual")
            app = SearchApplication(source=source, storage=storage)

        benchmark(_manual_build)
