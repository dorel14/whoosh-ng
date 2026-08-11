"""SearchApplication: unified entry point for Whoosh-NG.

Orchestrates DataSource -> SchemaDiscovery -> Index -> search/autocomplete/synonyms/plugins.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.index import Index
from whoosh.plugins.storage_base import SyncStorageProvider
from whoosh_modern.data_sources import DataSource
from whoosh_modern.middleware.storage import FileStorageProvider
from whoosh_modern.views import SearchView


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

    Attributes:
        _source: Optional DataSource providing documents.
        _storage: Optional storage provider for index files.
        _index: The built Whoosh Index (None until ``build`` is called).
        _schema: The Whoosh Schema discovered from the data source.
    """

    def __init__(
        self,
        source: DataSource | None = None,
        storage: SyncStorageProvider | None = None,
    ) -> None:
        """Initialize the SearchApplication.

        Args:
            source: Optional DataSource providing documents for indexing.
            storage: Optional storage provider for index files.
        """
        self._source = source
        self._storage = storage
        self._index: Index | None = None
        self._schema: Any = None

    @property
    def index(self) -> Index:
        """Return the built index.

        Returns:
            The Whoosh Index object.

        Raises:
            RuntimeError: If ``build()`` has not been called yet.
        """
        if self._index is None:
            raise RuntimeError("Call build() before accessing the index")
        return self._index

    def build(self) -> SearchApplication:
        """Build the index from the data source.

        Returns:
            self for chaining.

        Raises:
            ValueError: If no data source was provided.
        """
        if self._source is None:
            raise ValueError("A source is required to build the index")

        index_path = self._resolve_index_path()

        view = SearchView(name="search_application", source=self._source)
        self._index = view.build(index_path)
        self._schema = view._schema
        self._view = view

        return self

    def _resolve_index_path(self) -> str:
        """Resolve a filesystem path where the index will be built.

        The path is derived from the configured storage provider when it is
        filesystem-backed (exposing a public ``root``), otherwise a temporary
        directory is used. This avoids reaching into provider internals.

        Returns:
            An absolute directory path suitable for ``create_in``.
        """
        if self._storage is None:
            import tempfile

            return tempfile.mkdtemp()
        if isinstance(self._storage, FileStorageProvider):
            return self._storage.root
        import tempfile

        return tempfile.mkdtemp()

    def search(self, query: Any, **kwargs: Any) -> Any:
        """Search the index.

        Args:
            query: Query string or pre-parsed Query object.
            **kwargs: Additional keyword arguments forwarded to
                ``Searcher.search()``.

        Returns:
            Search results object from the Whoosh searcher.

        Raises:
            RuntimeError: If ``build()`` has not been called yet.
        """
        if self._index is None:
            raise RuntimeError("Call build() before searching")
        if isinstance(query, str):
            from whoosh.qparser import QueryParser

            default_field = self._schema.names()[0] if self._schema else "content"
            parser = QueryParser(default_field, self._schema)
            query = parser.parse(query)
        with self._index.searcher() as searcher:
            return searcher.search(query, **kwargs)


__all__ = ["SearchApplication"]
