"""Optimized writer module for large-scale indexing in Whoosh-NG.

This module provides batch-optimized writing that does NOT modify
the core whoosh writer. It wraps the core writer with optimizations
specifically designed for large datasets (millions of documents).

Key optimizations:
- Multisegment mode (no merging during indexing)
- Reduced Python overhead in batch loops
- Configurable batch sizes and memory limits

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from whoosh.index import Index
from whoosh.writing import SegmentWriter


class ModernIndexWriter:
    """Optimized writer for large-scale indexing.

    Wraps a core Whoosh writer with optimizations for batch
    processing of millions of documents. Does NOT modify the
    core whoosh writer.

    Example::

        from whoosh_modern.writer import ModernIndexWriter

        with ModernIndexWriter(index, batch_size=5000) as writer:
            for batch in source.stream_batches(batch_size=5000):
                writer.add_batch(batch)
    """

    def __init__(
        self,
        index: Index,
        batch_size: int = 5000,
        limitmb: int = 512,
        multisegment: bool = True,
        **writer_kwargs: Any,
    ) -> None:
        self._index = index
        self._batch_size = batch_size
        self._limitmb = limitmb
        self._multisegment = multisegment
        self._writer_kwargs = writer_kwargs
        self._writer: SegmentWriter | None = None
        self._doc_count = 0

    def __enter__(self) -> ModernIndexWriter:
        """Open the underlying writer and return self for context management.

        Returns:
            The ModernIndexWriter instance (self).
        """
        self._writer = self._index.writer(
            limitmb=self._limitmb,
            multisegment=self._multisegment,
            **self._writer_kwargs,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Commit or cancel the writer on context exit.

        Args:
            exc_type: Exception type if an error occurred, None otherwise.
            exc_val: Exception value if an error occurred, None otherwise.
            exc_tb: Exception traceback if an error occurred, None otherwise.
        """
        if self._writer is not None:
            if exc_type is None:
                self._writer.commit(merge=False)
            else:
                self._writer.cancel()
            self._writer = None

    def add_batch(self, docs: list[dict[str, Any]]) -> int:
        """Add a batch of documents to the index.

        Args:
            docs: List of document dictionaries to index.

        Returns:
            Number of documents added.

        Raises:
            RuntimeError: If the writer is not open (not inside a context manager).
        """
        if not docs:
            return 0

        writer = self._writer
        if writer is None:
            raise RuntimeError("Writer is not open")

        count = 0
        for doc in docs:
            writer.add_document(**doc)
            count += 1

        self._doc_count += count
        return count

    def add_batches(self, batches: Iterator[list[dict[str, Any]]]) -> int:
        """Add multiple batches of documents to the index.

        Args:
            batches: Iterable of document batch lists.

        Returns:
            Total number of documents added across all batches.
        """
        total = 0
        for batch in batches:
            total += self.add_batch(batch)
        return total

    @property
    def doc_count(self) -> int:
        """Return the total number of documents indexed so far."""
        return self._doc_count


class ModernIndex:
    """Modern index optimized for large-scale indexing.

    Wraps a core Whoosh index with optimized settings for
    batch processing of millions of documents.

    Example::

        from whoosh_modern.writer import ModernIndex

        index = ModernIndex.create("indexdir", schema=my_schema)
        with index.writer() as writer:
            for batch in source.stream_batches(batch_size=5000):
                writer.add_batch(batch)
    """

    def __init__(self, index: Index) -> None:
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
    ) -> ModernIndexWriter:
        """Return a ModernIndexWriter with optimized settings.

        Args:
            batch_size: Number of documents per batch for indexing.
            limitmb: Memory limit in megabytes for the writer.
            **kwargs: Additional arguments passed to the writer.

        Returns:
            A configured ModernIndexWriter instance.
        """
        return ModernIndexWriter(
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


__all__ = ["ModernIndex", "ModernIndexWriter"]
