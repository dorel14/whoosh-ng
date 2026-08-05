import os.path
import sqlite3
from typing import Any

from benchmark import WhooshLikeSpec
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.views import SearchView


class StockEtabModern(WhooshLikeSpec):
    name = "stock_etab_modern"
    main_field = "libelle_activite"
    headline_field = "libelle_activite"
    default_query = "SAINT-NAZAIRE"

    def __init__(self, options: Any, args: Any) -> None:
        super().__init__(options, args)
        self._conn: sqlite3.Connection | None = None
        self._source: SQLSource | None = None
        self._view: SearchView | None = None

    def _ensure_setup(self):
        if self._conn is None:
            bench_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(bench_dir, "benchmark_data.db")
            self._conn = sqlite3.connect(db_path)
            self._source = SQLSource(
                connection=self._conn,
                query="SELECT * FROM stock_etablissements",
                incremental_field=None,
                id_field="siret",
            )
            self._view = SearchView(
                name="stock_etab",
                source=self._source,
            )

    def whoosh_schema(self) -> Any:
        self._ensure_setup()
        assert self._source is not None
        return self._source.discover_schema()

    def documents(self) -> Any:
        self._ensure_setup()
        assert self._source is not None
        schema_fields = set(self._source.discover_schema().names())
        for doc in self._source.iter_documents():
            filtered = {
                k: str(v) if not isinstance(v, str) else v
                for k, v in doc.items()
                if k in schema_fields
            }
            yield filtered

    def batches(self, batch_size: int = 1000):
        self._ensure_setup()
        assert self._source is not None
        yield from self._source.stream_batches(batch_size=batch_size)
