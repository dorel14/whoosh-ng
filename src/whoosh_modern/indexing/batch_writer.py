"""Batch index writer for high-throughput indexing.

Provides a modern batch writing path that optimizes document ingestion
for large datasets without modifying the whoosh core library.

Key optimizations:
- Pre-filters document fields to only those in the schema
- Uses multisegment mode to avoid merge overhead during indexing
- Supports configurable batch commits to reduce I/O
- Caches schema field lookups for O(1) per-field validation
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import Any

from whoosh.index import Index
from whoosh.writing import SegmentWriter

logger = logging.getLogger(__name__)


class BatchIndexWriter:
    """Optimized batch writer for large-scale indexing.

    Wraps a core Whoosh writer with optimizations for batch
    processing of millions of documents. Does NOT modify the
    core whoosh writer.

    Optimizations:
    - Pre-computes schema field names for fast filtering
    - Skips fields not in the schema (avoiding per-doc overhead)
    - Uses multisegment=True to defer merging
    - Supports batch commits to reduce I/O pressure

    Example::

        writer = BatchIndexWriter(index, batch_size=5000)
        for batch in source.stream_batches(batch_size=5000):
            writer.add_batch(batch)
        writer.close()
    """

    def __init__(
        self,
        index: Index,
        batch_size: int = 5000,
        limitmb: int = 512,
        commit_every: int | None = None,
        multisegment: bool = True,
        callback: Callable[[str, int], None] | None = None,
        commit_profiler: Any = None,
        **writer_kwargs: Any,
    ) -> None:
        self._index = index
        self._batch_size = batch_size
        self._limitmb = limitmb
        self._commit_every = commit_every
        self._multisegment = multisegment
        self._callback = callback
        self._commit_profiler = commit_profiler
        self._writer_kwargs = writer_kwargs
        self._writer: SegmentWriter | None = None
        self._doc_count = 0
        self._batch_count = 0
        self._schema_fields: set[str] | None = None

    def _get_schema_fields(self) -> set[str]:
        """Return the set of field names in the index schema."""
        if self._schema_fields is None:
            self._schema_fields = set(self._index.schema.names())
        return self._schema_fields

    def _filter_doc(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Filter a document to only include fields in the schema."""
        schema_fields = self._get_schema_fields()
        return {k: v for k, v in doc.items() if k in schema_fields}

    def _ensure_writer(self) -> None:
        """Open a writer if one is not already open."""
        if self._writer is None:
            self._writer = self._index.writer(
                limitmb=self._limitmb,
                multisegment=self._multisegment,
                **self._writer_kwargs,
            )

    def add_batch(self, docs: list[dict[str, Any]]) -> int:
        """Add a batch of documents.

        Filters each document to only include fields present in the
        schema, then adds them to the index.

        :param docs: list of document dicts.
        :returns: number of documents added.
        """
        if not docs:
            return 0

        self._ensure_writer()
        writer = self._writer
        if writer is None:
            raise RuntimeError("Writer is not open")

        schema_fields = self._get_schema_fields()
        count = 0
        for doc in docs:
            if any(k not in schema_fields for k in doc):
                filtered = {k: v for k, v in doc.items() if k in schema_fields}
                writer.add_document(**filtered)
            else:
                writer.add_document(**doc)
            count += 1

        self._doc_count += count
        self._batch_count += 1

        if self._commit_every is not None and self._batch_count % self._commit_every == 0:
            if self._writer is not None:
                if self._commit_profiler is not None:
                    self._commit_profiler.profile(self._writer)
                else:
                    self._writer.commit(merge=False, callback=self._callback)
                self._writer = None
                self._schema_fields = None

        return count

    def add_batches(self, batches: Iterator[list[dict[str, Any]]]) -> int:
        """Add multiple batches of documents.

        :param batches: iterable of document lists.
        :returns: total number of documents added.
        """
        total = 0
        for batch in batches:
            total += self.add_batch(batch)
        return total

    def close(self) -> int:
        """Close the writer and return total documents added."""
        if self._writer is not None:
            if self._commit_profiler is not None:
                self._commit_profiler.profile(self._writer)
            else:
                self._writer.commit(merge=False, callback=self._callback)
            self._writer = None
        total = self._doc_count
        self._doc_count = 0
        self._batch_count = 0
        return total

    def __enter__(self) -> BatchIndexWriter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()

    @property
    def doc_count(self) -> int:
        """Return the total number of documents added so far."""
        return self._doc_count

    @property
    def batch_count(self) -> int:
        """Return the total number of batches added so far."""
        return self._batch_count
