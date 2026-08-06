"""SearchApplication: unified entry point for Whoosh-NG.

Orchestrates DataSource → SchemaDiscovery → Index → search/autocomplete/synonyms/plugins.
"""

from __future__ import annotations

from typing import Any

from whoosh.index import Index
from whoosh.plugins.storage_base import SyncStorageProvider

from whoosh_modern.data_sources import DataSource
from whoosh_modern.schema_discovery import SchemaDiscovery


class FileStorage(SyncStorageProvider):
    """Local filesystem storage provider (alias for FileStorageProvider).

    Keys are interpreted as relative paths under ``root``.
    """

    def __init__(self, root: str) -> None:
        from whoosh_modern.middleware.storage import FileStorageProvider

        self._provider = FileStorageProvider(root)

    def write(self, key: str, data: bytes) -> None:
        self._provider.write(key, data)

    def read(self, key: str) -> bytes:
        return self._provider.read(key)

    def delete(self, key: str) -> None:
        self._provider.delete(key)

    def exists(self, key: str) -> bool:
        return self._provider.exists(key)

    def list_keys(self) -> list[str]:
        return self._provider.list_keys()


class SearchApplication:
    """Unified search application entry point.

    Example::

        from whoosh_modern import SearchApplication, SQLSource
        from whoosh_modern.storage import FileStorage

        app = SearchApplication(
            source=SQLSource(query="SELECT * FROM products", connection=engine),
            storage=FileStorage("indexdir"),
        )
        app.build()
        results = app.index.search("laptop")
    """

    def __init__(
        self,
        source: DataSource | None = None,
        storage: SyncStorageProvider | None = None,
    ) -> None:
        self._source = source
        self._storage = storage
        self._index: Index | None = None
        self._schema: Any = None

    @property
    def index(self) -> Index:
        """Return the built index."""
        if self._index is None:
            raise RuntimeError("Call build() before accessing the index")
        return self._index

    def build(self) -> SearchApplication:
        """Build the index from the data source.

        :returns: self for chaining
        """
        if self._source is None:
            raise ValueError("A source is required to build the index")

        schema = self._source.discover_schema()
        self._schema = schema

        if self._storage is not None:
            storage_path = getattr(self._storage, "_provider", self._storage)
            if hasattr(storage_path, "_root"):
                from whoosh.index import create_in

                self._index = create_in(storage_path._root, schema)
            else:
                from whoosh.index import create_in

                import tempfile

                tmp = tempfile.mkdtemp()
                self._index = create_in(tmp, schema)
        else:
            from whoosh.index import create_in

            import tempfile

            tmp = tempfile.mkdtemp()
            self._index = create_in(tmp, schema)

        writer = self._index.writer()
        for batch in self._source.stream_batches():
            for doc in batch:
                writer.add_document(**doc)
        writer.commit()

        return self

    def search(self, query: Any, **kwargs: Any) -> Any:
        """Search the index.

        :param query: query string or Query object
        :returns: search results
        """
        if isinstance(query, str):
            from whoosh.qparser import QueryParser

            default_field = self._schema.names()[0] if self._schema else "content"
            parser = QueryParser(default_field, self._schema)
            query = parser.parse(query)
        with self._index.searcher() as searcher:
            return searcher.search(query, **kwargs)


__all__ = ["SearchApplication", "FileStorage"]
