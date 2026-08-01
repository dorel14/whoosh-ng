import os.path
import sqlite3
from typing import Any

from benchmark import WhooshLikeSpec
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.views import SearchView


class DictionaryModern(WhooshLikeSpec):
    name = "dictionary_modern"
    main_field = "body"
    headline_field = "head"
    default_query = "bawd"

    def __init__(self, options: Any, args: Any) -> None:
        super().__init__(options, args)
        self._conn: sqlite3.Connection | None = None
        self._source: SQLSource | None = None
        self._view: SearchView | None = None

    def _ensure_setup(self) -> None:
        if self._conn is None:
            bench_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(bench_dir, "benchmark_data.db")
            self._conn = sqlite3.connect(db_path)
            self._source = SQLSource(
                connection=self._conn,
                query="SELECT * FROM dictionary_entries",
                incremental_field=None,
                id_field="id",
            )
            self._view = SearchView(
                name="dictionary",
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
