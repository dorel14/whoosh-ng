"""Modern optimized writer for large-scale indexing in Whoosh-NG.

This module provides batch-optimized writing that does NOT modify
the core whoosh writer. It wraps the core writer with optimizations
specifically designed for large datasets (millions of documents).

Key optimizations:
- Multisegment mode (no merging during indexing)
- Reduced Python overhead in batch loops
- Configurable batch sizes and memory limits
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
        if self._writer is not None:
            if exc_type is None:
                self._writer.commit(merge=False)
            else:
                self._writer.cancel()
            self._writer = None

    def add_batch(self, docs: list[dict[str, Any]]) -> int:
        """Add a batch of documents.

        :param docs: list of document dicts.
        :returns: number of documents added.
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
        """Add multiple batches of documents.

        :param batches: iterable of document lists.
        :returns: total number of documents added.
        """
        total = 0
        for batch in batches:
            total += self.add_batch(batch)
        return total

    @property
    def doc_count(self) -> int:
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
        """Create a new modern index."""
        from whoosh.index import create_in

        ix = create_in(path, schema, **kwargs)
        return cls(ix)

    @classmethod
    def open(cls, path: str) -> ModernIndex:
        """Open an existing modern index."""
        from whoosh.index import open_dir

        ix = open_dir(path)
        return cls(ix)

    def writer(
        self,
        batch_size: int = 5000,
        limitmb: int = 512,
        **kwargs: Any,
    ) -> ModernIndexWriter:
        """Return a ModernIndexWriter with optimized settings."""
        return ModernIndexWriter(
            self._index,
            batch_size=batch_size,
            limitmb=limitmb,
            multisegment=True,
            **kwargs,
        )

    def searcher(self, **kwargs: Any) -> Any:
        """Return a searcher from the underlying index."""
        return self._index.searcher(**kwargs)

    @property
    def schema(self) -> Any:
        return self._index.schema

    @property
    def doc_count(self) -> int:
        return int(self._index.doc_count())
