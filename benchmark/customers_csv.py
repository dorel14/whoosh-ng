"""Benchmark CSVSource on the large customers CSV file (2M rows)."""

from __future__ import annotations

import os

from benchmark import WhooshLikeSpec
from whoosh import fields

from whoosh_modern.data_sources.csv import CSVSource


class CustomersCSV(WhooshLikeSpec):
    name = "customers_csv"
    main_field = "city"
    headline_field = "first_name"
    default_query = "London"

    def __init__(self, options, args):
        super().__init__(options, args)
        csv_path = os.path.join(
            self.options.dir, "Datas", "customers-2000000.csv"
        )
        self._source = CSVSource(
            path=csv_path,
            incremental_field=None,
            id_field="Customer Id",
        )

    def whoosh_schema(self):
        return self._source.discover_schema()

    def documents(self):
        yield from self._source.iter_documents()
