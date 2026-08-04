"""Benchmark FastCSVSource on the large customers CSV file (2M rows)."""

from __future__ import annotations

import os

from benchmark import WhooshLikeSpec
from whoosh import fields
from whoosh_modern.data_sources.fast_csv import FastCSVSource


class CustomersCSV(WhooshLikeSpec):
    name = "customers_csv"
    main_field = "City"
    headline_field = "First_Name"
    default_query = "Bradleymouth"

    def __init__(self, options, args):
        super().__init__(options, args)
        csv_path = os.path.join(
            self.options.dir, "Datas", "customers-2000000.csv"
        )
        self._source = FastCSVSource(
            path=csv_path,
            incremental_field=None,
            id_field="Customer Id",
        )

    def whoosh_schema(self):
        return self._source.discover_schema()

    def documents(self):
        yield from self._source.iter_documents()

    def batches(self, batch_size: int = 1000):
        yield from self._source.stream_batches(batch_size=batch_size)
