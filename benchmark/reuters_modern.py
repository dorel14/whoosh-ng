import os.path
import sqlite3

from benchmark import WhooshLikeSpec
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.views import SearchView


class ReutersModern(WhooshLikeSpec):
    name = "reuters_modern"
    main_field = "body"
    headline_field = "headline"
    default_query = "trade"

    def __init__(self, options, args):
        super().__init__(options, args)
        self._conn = None
        self._source = None
        self._view = None

    def _ensure_setup(self):
        if self._conn is None:
            bench_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(bench_dir, "benchmark_data.db")
            self._conn = sqlite3.connect(db_path)
            self._source = SQLSource(
                connection=self._conn,
                query="SELECT * FROM reuters_articles",
                incremental_field="article_date",
                id_field="id",
            )
            self._view = SearchView(
                name="reuters",
                source=self._source,
            )

    def whoosh_schema(self):
        self._ensure_setup()
        return self._source.discover_schema()

    def documents(self):
        self._ensure_setup()
        schema_fields = set(self._source.discover_schema().names())
        for doc in self._source.iter_documents():
            filtered = {
                k: str(v) if not isinstance(v, str) else v
                for k, v in doc.items()
                if k in schema_fields
            }
            yield filtered
