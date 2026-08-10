"""Optimized writer module for large-scale indexing in Whoosh-NG.

This module exposes :class:`ModernIndex`, a thin wrapper around
:class:`whoosh.index.Index` that hands out batch-optimized writers
(:class:`whoosh_modern.indexing.batch_writer.BatchIndexWriter`) tuned for
ingesting millions of documents. The core whoosh writer is never modified.

Key optimizations:
- Multisegment mode (no merging during indexing)
- Reduced Python overhead in batch loops
- Configurable batch sizes and memory limits

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.index import Index
from whoosh_modern.indexing.batch_writer import BatchIndexWriter


class ModernIndex:
    """Modern index optimized for large-scale indexing.

    Wraps a core Whoosh index with optimized settings for
    batch processing of millions of documents.

    Example:
        >>> from whoosh_modern.writer import ModernIndex  # doctest: +SKIP
        >>> index = ModernIndex.create("indexdir", schema=my_schema)  # doctest: +SKIP
        >>> with index.writer() as writer:  # doctest: +SKIP
        ...     for batch in source.stream_batches(batch_size=5000):
        ...         writer.add_batch(batch)
    """

    def __init__(self, index: Index) -> None:
        """Initialize the wrapper.

        Args:
            index: The underlying core Whoosh index.
        """
        self._index = index

    @classmethod
    def create(cls, path: str, schema: Any, **kwargs: Any) -> ModernIndex:
        """Create a new modern index at the given path.

        Args:
            path: Directory path for the new index.
            schema: Whoosh Schema object for the index.
            **kwargs: Additional arguments passed to the index creator.

        Returns:
            A new ModernIndex instance wrapping the created index.
        """
        from whoosh.index import create_in

        ix = create_in(path, schema, **kwargs)
        return cls(ix)

    @classmethod
    def open(cls, path: str) -> ModernIndex:
        """Open an existing modern index from the given path.

        Args:
            path: Directory path of the existing index.

        Returns:
            A ModernIndex instance wrapping the opened index.
        """
        from whoosh.index import open_dir

        ix = open_dir(path)
        return cls(ix)

    def writer(
        self,
        batch_size: int = 5000,
        limitmb: int = 512,
        **kwargs: Any,
    ) -> BatchIndexWriter:
        """Return a batch writer with optimized settings.

        Args:
            batch_size: Number of documents per batch for indexing.
            limitmb: Memory limit in megabytes for the writer.
            **kwargs: Additional arguments passed to the writer.

        Returns:
            A configured :class:`BatchIndexWriter` instance.
        """
        return BatchIndexWriter(
            self._index,
            batch_size=batch_size,
            limitmb=limitmb,
            multisegment=True,
            **kwargs,
        )

    def searcher(self, **kwargs: Any) -> Any:
        """Return a searcher from the underlying index.

        Args:
            **kwargs: Additional arguments passed to the index searcher.

        Returns:
            A Whoosh Searcher instance.
        """
        return self._index.searcher(**kwargs)

    @property
    def schema(self) -> Any:
        """Return the schema of the underlying index."""
        return self._index.schema

    @property
    def doc_count(self) -> int:
        """Return the total number of documents in the index."""
        return int(self._index.doc_count())


__all__ = ["ModernIndex"]
