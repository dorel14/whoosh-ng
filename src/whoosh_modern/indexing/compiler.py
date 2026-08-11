"""DataSource Compiler for pre-compiled transformations.

Pre-compiles data source transformations to reduce per-row Python overhead.
Inspired by Pydantic v2, Polars, and SQLAlchemy compiled queries.

Author: dorel14
Version: 3.0.0

Example::

    source = FastCSVSource("data.csv")
    mapper = source.compile()
    for row in csv_reader:
        doc = mapper(row)  # Zero per-row overhead after compilation
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

DocumentMapper = Callable[[Any], dict[str, Any]]


class CompiledDataSource:
    """Wrapper around a DataSource that provides a compiled mapper.

    The compiled mapper is a callable that transforms raw data rows
    into Whoosh documents with minimal Python overhead.

    Example::

        compiled = CompiledDataSource(source)
        mapper = compiled.mapper()
        for row in source.iter_rows():
            doc = mapper(row)
    """

    def __init__(self, source: Any) -> None:
        """Initialize the compiled data source wrapper.

        Args:
            source: The underlying data source object to wrap.
        """
        self._source = source

    @property
    def source(self) -> Any:
        """The underlying data source object."""
        return self._source

    def mapper(self) -> DocumentMapper:
        """Return a compiled document mapper for this data source.

        The mapper transforms raw data rows into Whoosh documents.
        For sources that support compilation, this avoids per-row
        Python overhead.

        Returns:
            A callable that maps a raw data row to a document dict.
        """
        if hasattr(self._source, "compile_mapper"):
            return self._source.compile_mapper()  # type: ignore[no-any-return]
        return self._default_mapper()

    def _default_mapper(self) -> DocumentMapper:
        """Return a default mapper that passes through dicts.

        Returns:
            A callable that converts a row to a dict, using ``to_dict``
            if available, or returning the dict directly.
        """
        _source = self._source

        def mapper(row: Any) -> dict[str, Any]:
            if hasattr(row, "to_dict"):
                return row.to_dict()  # type: ignore[no-any-return]
            if isinstance(row, dict):
                return row
            return dict(row) if row else {}

        return mapper

    def stream_batches(self, batch_size: int = 1000) -> Any:
        """Return an optimized batch iterator.

        Uses the data source's native ``stream_batches`` if available,
        otherwise falls back to the default implementation.

        Args:
            batch_size: Number of documents per batch. Defaults to 1000.

        Returns:
            An iterator yielding lists of document dicts.
        """
        if hasattr(self._source, "stream_batches"):
            return self._source.stream_batches(batch_size=batch_size)
        return self._default_stream_batches(batch_size)

    def _default_stream_batches(self, batch_size: int) -> Any:
        """Default batch streaming using iter_documents.

        Args:
            batch_size: Number of documents per batch.

        Yields:
            Lists of document dicts of up to ``batch_size`` documents.
        """
        batch: list[dict[str, Any]] = []
        for doc in self._source.iter_documents():
            batch.append(dict(doc))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def __repr__(self) -> str:
        """Return a string representation of this compiled data source.

        Returns:
            A string in the form ``CompiledDataSource(source=<source!r>)``.
        """
        return f"CompiledDataSource(source={self._source!r})"


class BatchAnalyzer:
    """Analyzes documents in batches with LRU caching.

    Processes documents in batches and caches analysis results
    for repeated field values to avoid redundant tokenization,
    lowercasing, and stemming.

    Example::

        analyzer = BatchAnalyzer(writer, batch_size=5000)
        for batch in source.stream_batches(batch_size=5000):
            analyzer.process_batch(batch)
        analyzer.flush()
    """

    def __init__(
        self,
        writer: Any,
        batch_size: int = 5000,
        cache_size: int = 10000,
        schema_fields: set[str] | None = None,
    ) -> None:
        """Initialize the batch analyzer.

        Args:
            writer: The index writer to add analyzed documents to.
            batch_size: Number of documents processed per batch. Defaults to 5000.
            cache_size: Maximum number of entries in the LRU cache.
                Defaults to 10000.
            schema_fields: Optional set of field names to include in the
                cache key and filtering. If ``None``, all fields are used.
        """
        self._writer = writer
        self._batch_size = batch_size
        self._cache_size = cache_size
        self._schema_fields = schema_fields
        self._cache: dict[str, dict[str, Any]] = {}
        self._processed = 0

    def _get_cache_key(self, doc: dict[str, Any]) -> str:
        """Generate a cache key for a document based on its field values.

        Args:
            doc: The document dict to generate a key for.

        Returns:
            A string key derived from the document's field values.
        """
        if self._schema_fields is not None:
            values = tuple(doc.get(f, "") for f in self._schema_fields)
        else:
            values = tuple(doc.values())
        return "|".join(str(v) for v in values)

    def _process_document(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Process a single document, using cache if available.

        Filters the document to schema fields and caches the result.
        If the cache key already exists, the cached result is returned.

        Args:
            doc: The document dict to process.

        Returns:
            The filtered document dict (from cache or freshly processed).
        """
        cache_key = self._get_cache_key(doc)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self._schema_fields is not None:
            filtered = {k: v for k, v in doc.items() if k in self._schema_fields}
        else:
            filtered = doc

        self._cache[cache_key] = filtered
        if len(self._cache) > self._cache_size:
            self._cache.pop(next(iter(self._cache)))
        return filtered

    def process_batch(self, docs: list[dict[str, Any]]) -> int:
        """Process a batch of documents.

        Each document is filtered and cached, then added to the writer.

        Args:
            docs: List of document dicts.

        Returns:
            The number of documents processed.
        """
        if not docs:
            return 0

        count = 0
        for doc in docs:
            filtered = self._process_document(doc)
            self._writer.add_document(**filtered)
            count += 1

        self._processed += count
        return count

    def flush(self) -> int:
        """Flush any remaining documents and return total processed.

        Returns:
            The total number of documents processed.
        """
        return self._processed

    @property
    def processed(self) -> int:
        """int: Total number of documents processed."""
        return self._processed

    @property
    def cache_hits(self) -> int:
        """int: Approximate cache hit count."""
        return max(0, self._processed - len(self._cache))
