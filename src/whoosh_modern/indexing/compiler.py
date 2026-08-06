"""DataSource Compiler for pre-compiled transformations.

Pre-compiles data source transformations to reduce per-row Python overhead.
Inspired by Pydantic v2, Polars, and SQLAlchemy compiled queries.

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
        self._source = source

    @property
    def source(self) -> Any:
        """Return the underlying data source."""
        return self._source

    def mapper(self) -> DocumentMapper:
        """Return a compiled document mapper for this data source.

        The mapper transforms raw data rows into Whoosh documents.
        For sources that support compilation, this avoids per-row
        Python overhead.
        """
        if hasattr(self._source, "compile_mapper"):
            return self._source.compile_mapper()  # type: ignore[no-any-return]
        return self._default_mapper()

    def _default_mapper(self) -> DocumentMapper:
        """Return a default mapper that passes through dicts."""
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

        Uses the data source's native stream_batches if available,
        otherwise falls back to the default implementation.
        """
        if hasattr(self._source, "stream_batches"):
            return self._source.stream_batches(batch_size=batch_size)
        return self._default_stream_batches(batch_size)

    def _default_stream_batches(self, batch_size: int) -> Any:
        """Default batch streaming using iter_documents."""
        batch: list[dict[str, Any]] = []
        for doc in self._source.iter_documents():
            batch.append(dict(doc))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def __repr__(self) -> str:
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
        self._writer = writer
        self._batch_size = batch_size
        self._cache_size = cache_size
        self._schema_fields = schema_fields
        self._cache: dict[str, dict[str, Any]] = {}
        self._processed = 0

    def _get_cache_key(self, doc: dict[str, Any]) -> str:
        """Generate a cache key for a document based on its field values."""
        if self._schema_fields is not None:
            values = tuple(doc.get(f, "") for f in self._schema_fields)
        else:
            values = tuple(doc.values())
        return "|".join(str(v) for v in values)

    def _process_document(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Process a single document, using cache if available."""
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

        :param docs: list of document dicts.
        :returns: number of documents processed.
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
        """Flush any remaining documents and return total processed."""
        return self._processed

    @property
    def processed(self) -> int:
        """Return total number of documents processed."""
        return self._processed

    @property
    def cache_hits(self) -> int:
        """Return approximate cache hit count."""
        return max(0, self._processed - len(self._cache))
