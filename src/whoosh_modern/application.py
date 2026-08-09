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


class FileStorage(SyncStorageProvider):
    """Local filesystem storage provider (alias for FileStorageProvider).

    Keys are interpreted as relative paths under ``root``.

    Attributes:
        _provider: The underlying ``FileStorageProvider`` instance.
    """

    def __init__(self, root: str) -> None:
        """Initialize file-based storage.

        Args:
            root: Root directory path for storing index files.
        """
        from whoosh_modern.middleware.storage import FileStorageProvider

        self._provider = FileStorageProvider(root)

    def write(self, key: str, data: bytes) -> None:
        """Write data to the file system.

        Args:
            key: Relative path key under the root directory.
            data: Byte payload to store.
        """
        self._provider.write(key, data)

    def read(self, key: str) -> bytes:
        """Read data from the file system.

        Args:
            key: Relative path key under the root directory.

        Returns:
            The stored byte payload.
        """
        return self._provider.read(key)

    def delete(self, key: str) -> None:
        """Delete a file from the file system.

        Args:
            key: Relative path key under the root directory.
        """
        self._provider.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists in the file system.

        Args:
            key: Relative path key under the root directory.

        Returns:
            True if the file exists, False otherwise.
        """
        return self._provider.exists(key)

    def list_keys(self) -> list[str]:
        """List all keys (file paths) in the root directory.

        Returns:
            A list of relative path key strings.
        """
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

        schema = self._source.discover_schema()
        self._schema = schema

        if self._storage is not None:
            storage_path = getattr(self._storage, "_provider", self._storage)
            root = getattr(storage_path, "_root", None)
            if root is not None:
                from whoosh.index import create_in

                self._index = create_in(root, schema)
            else:
                import tempfile

                from whoosh.index import create_in

                tmp = tempfile.mkdtemp()
                self._index = create_in(tmp, schema)
        else:
            import tempfile

            from whoosh.index import create_in

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


__all__ = ["SearchApplication", "FileStorage"]
