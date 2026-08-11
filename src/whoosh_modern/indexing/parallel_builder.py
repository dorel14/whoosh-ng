"""Parallel index builder for Whoosh.

Thin wrapper around the core multiprocessing writer
(:class:`whoosh.multiproc.MpWriter`, obtained via
``Index.writer(procs=N, multisegment=...)``) that consumes batches of
documents from a :class:`~whoosh_modern.data_sources.DataSource` or any
iterable of document lists.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from whoosh.index import create_in

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from whoosh.fields import Schema
    from whoosh_modern.data_sources import DataSource

logger = logging.getLogger(__name__)


class ParallelIndexBuilder:
    """Build a Whoosh index in parallel using the core multiprocess writer.

    Documents are streamed to ``Index.writer(procs=N, multisegment=True)``,
    which distributes the analysis/indexing work across ``N`` subprocesses
    and merges the resulting segments on commit.

    Example:
        >>> builder = ParallelIndexBuilder(  # doctest: +SKIP
        ...     schema=my_schema,
        ...     index_path="indexdir",
        ...     workers=4,
        ...     batch_size=10000,
        ... )
        >>> builder.build(source.stream_batches(batch_size=10000))  # doctest: +SKIP
    """

    def __init__(
        self,
        schema: Schema,
        index_path: str | Path,
        workers: int = 4,
        batch_size: int = 10000,
        limitmb: int = 128,
        multisegment: bool = True,
    ) -> None:
        """Initialize the parallel index builder.

        Args:
            schema: The Whoosh schema defining the index structure.
            index_path: Filesystem path where the index will be created.
            workers: Number of worker processes (``procs``) used by the core
                multiprocess writer. Defaults to 4.
            batch_size: Number of documents per batch requested from a data
                source. Defaults to 10000.
            limitmb: Memory limit in MB for each writer buffer. Defaults to 128.
            multisegment: If True, each subprocess writes its own segment
                instead of merging into a single one. Defaults to True.
        """
        self.schema = schema
        self.index_path = str(index_path)
        self.workers = workers
        self.batch_size = batch_size
        self.limitmb = limitmb
        self.multisegment = multisegment

    def build(self, batches: Iterator[list[dict[str, Any]]]) -> int:
        """Build the index from an iterable of document batches.

        Args:
            batches: Iterable of document lists (e.g. from
                ``source.stream_batches()``).

        Returns:
            Total number of documents indexed.

        Raises:
            Exception: Any error raised while adding documents or committing;
                the writer is cancelled before the error propagates.
        """
        # ``create_in`` requires the target directory to already exist.
        os.makedirs(self.index_path, exist_ok=True)
        ix = create_in(self.index_path, self.schema)

        total = 0
        writer = None
        try:
            writer = ix.writer(
                procs=max(1, self.workers),
                limitmb=self.limitmb,
                multisegment=self.multisegment,
            )
            for batch in batches:
                if not batch:
                    continue
                for doc in batch:
                    writer.add_document(**doc)
                total += len(batch)
            writer.commit()
        except Exception as exc:
            logger.error("Parallel indexing failed: %s", exc)
            if writer is not None:
                writer.cancel()
            raise
        finally:
            ix.close()

        return total

    def build_from_source(self, source: DataSource) -> int:
        """Build the index directly from a DataSource.

        Args:
            source: Any object implementing ``stream_batches(batch_size)``.

        Returns:
            Total number of documents indexed.
        """
        return self.build(source.stream_batches(self.batch_size))
