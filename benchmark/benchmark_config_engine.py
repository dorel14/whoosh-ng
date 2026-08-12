"""Component benchmarks for the Whoosh-NG Configuration Engine.

Measures the overhead of ``ConfigEngine`` compared to equivalent manual
Whoosh-NG setup, so regressions in configuration loading/merging/building
can be detected early.

Run with::

    python -m pytest benchmark/benchmark_config_engine.py --benchmark-only
    --override-ini="norecursedirs="
    --override-ini="testpaths=benchmark"
    --override-ini="python_files=benchmark_*.py"
"""

from __future__ import annotations

import os
import tempfile

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.config import ConfigEngine
from whoosh_modern.config.engine import ConfigEngine as DirectConfigEngine
from whoosh_modern.config.loader import load_yaml
from whoosh_modern.config.models import WhooshNGConfig

BENCHMARK_DIR = pytest.importorskip("pathlib").Path(__file__).parent
YAML_PATH = BENCHMARK_DIR / "benchmark_data" / "whoosh-ng.yml"


def _ensure_benchmark_data() -> None:
    """Write a small YAML config file for benchmarks if it does not exist."""
    YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not YAML_PATH.exists():
        YAML_PATH.write_text(
            """\
index: benchmark
fields:
  title:
    type: text
    language: fr
    stemming: true
    stored: true
  price:
    type: numeric
    sortable: true
  published:
    type: datetime
    faceted: true
search:
  fuzzy:
    enabled: true
    distance: 2
data_source:
  type: csv
  path: products.csv
  delimiter: ","
  encoding: utf-8
storage:
  type: file
  path: ./index
""",
            encoding="utf-8",
        )


class BenchmarkConfigEngine:
    """Benchmark suite for ConfigEngine overhead."""

    def setup_method(self) -> None:
        _ensure_benchmark_data()
        self._raw_yaml = YAML_PATH.read_text(encoding="utf-8")

    def benchmark_load_yaml_direct(self, benchmark) -> None:
        """Baseline: load YAML without ConfigEngine."""
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8") as f:
            f.write(self._raw_yaml)
            path = f.name
        try:
            benchmark(load_yaml, path)
        finally:
            os.unlink(path)

    def benchmark_config_engine_load(self, benchmark) -> None:
        """ConfigEngine.load() from YAML file."""
        engine = DirectConfigEngine()
        benchmark(engine.load, YAML_PATH, priority="application")

    def benchmark_config_engine_merge(self, benchmark) -> None:
        """ConfigEngine.merge() from raw dict."""
        import yaml

        raw = yaml.safe_load(self._raw_yaml)
        engine = DirectConfigEngine()
        benchmark(engine.merge, raw, priority="runtime")

    def benchmark_config_engine_build(self, benchmark) -> None:
        """ConfigEngine.build() end-to-end."""
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
                path="products.csv",
                delimiter=",",
                encoding="utf-8",
            )
            storage = FileStorage("./index")
            app = SearchApplication(source=source, storage=storage)

        benchmark(_manual_build)
