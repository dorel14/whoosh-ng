"""Benchmark PandasSource on the large customers CSV (2M rows)."""

from __future__ import annotations

import os
import re

import pandas as pd

from benchmark import WhooshLikeSpec
from whoosh import fields
from whoosh_modern.data_sources.pandas_ds import PandasSource


def _sanitize(name: str) -> str:
    return re.sub(r"[^\w]", "_", name)


class CustomersPandas(WhooshLikeSpec):
    name = "customers_pandas"
    main_field = "City"
    headline_field = "First_Name"
    default_query = "Bradleymouth"

    def __init__(self, options, args):
        super().__init__(options, args)
        csv_path = os.path.join(
            self.options.dir, "Datas", "customers-2000000.csv"
        )
        df = pd.read_csv(csv_path)
        df.columns = [_sanitize(col) for col in df.columns]
        self._source = PandasSource(
            dataframe=df,
            incremental_field=None,
            id_field="Customer_Id",
        )

    def whoosh_schema(self):
        return self._source.discover_schema()

    def documents(self):
        yield from self._source.iter_documents()
