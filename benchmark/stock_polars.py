"""Benchmark PolarsSource on the large stock parquet file (705MB, 29M rows)."""

from __future__ import annotations

import os

import polars as pl

from benchmark import WhooshLikeSpec
from whoosh import fields
from whoosh_modern.data_sources.polars_ds import PolarsSource


class StockPolars(WhooshLikeSpec):
    name = "stock_polars"
    main_field = "denominationUsuelle1UniteLegale"
    headline_field = "denominationUsuelle1UniteLegale"
    default_query = "SNCF"

    def __init__(self, options, args):
        super().__init__(options, args)
        parquet_path = os.path.join(
            self.options.dir, "Datas", "stock-stockunitelegale-parquet.parquet"
        )
        df = pl.read_parquet(parquet_path)
        self._source = PolarsSource(
            dataframe=df,
            incremental_field=None,
            id_field="siren",
        )

    def whoosh_schema(self):
        return self._source.discover_schema()

    def documents(self):
        yield from self._source.iter_documents()

    def batches(self, batch_size: int = 1000):
        yield from self._source.stream_batches(batch_size=batch_size)
