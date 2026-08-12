"""WhooshLikeSpec benchmark comparing ConfigEngine-driven setup vs manual setup
on the real customers CSV, using the exact same indexing/searching path as
``customers_csv`` so the results are directly comparable.

Run with the same options as ``customers_csv``::

    python -m benchmark --spec customers_config_engine --index --search --report csv --upto 100000 --batch-size 500 --profile
"""

from __future__ import annotations

import os
from typing import Any

from benchmark import WhooshLikeSpec
from whoosh_modern.config.engine import ConfigEngine as DirectConfigEngine
from whoosh_modern.data_sources.fast_csv import FastCSVSource

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BENCHMARK_DIR, "Datas", "customers-2000000.csv")
YAML_PATH = os.path.join(BENCHMARK_DIR, "benchmark_data", "customers-whoosh-ng.yml")


def _ensure_yaml() -> None:
    os.makedirs(os.path.dirname(YAML_PATH), exist_ok=True)
    if not os.path.exists(YAML_PATH):
        with open(YAML_PATH, "w", encoding="utf-8") as f:
            f.write(
                f"""\
index: customers_config_engine
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
  path: {CSV_PATH}
  delimiter: ","
  encoding: utf-8
"""
            )


class CustomersConfigEngine(WhooshLikeSpec):
    """ConfigEngine-driven variant of ``customers_csv`` for fair comparison."""

    name = "customers_config_engine"
    main_field = "City"
    headline_field = "First_Name"
    default_query = "Bradleymouth"

    def __init__(self, options: Any, args: Any) -> None:
        super().__init__(options, args)
        _ensure_yaml()
        engine = DirectConfigEngine()
        engine.load(YAML_PATH, priority="application")
        config = engine.get_config()
        ds_config = config.data_source
        assert ds_config is not None
        self._source = FastCSVSource(
            path=ds_config.path or CSV_PATH,
            delimiter=ds_config.delimiter,
            encoding=ds_config.encoding,
            id_field="Customer Id",
        )

    def whoosh_schema(self) -> Any:
        return self._source.discover_schema()

    def documents(self) -> Any:
        yield from self._source.iter_documents()

    def batches(self, batch_size: int = 1000) -> Any:
        yield from self._source.stream_batches(batch_size=batch_size)
