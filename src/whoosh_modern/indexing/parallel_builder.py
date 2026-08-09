"""Parallel index builder for Whoosh.

Uses ``concurrent.futures`` to build multiple index segments concurrently,
then merges them into a single index. This provides near-linear speedups on
multi-core machines for CPU-bound indexing workloads.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import gc
import logging
import os
import shutil
import time
from collections.abc import Iterator
from concurrent.futures import Future, ProcessPoolExecutor
from typing import TYPE_CHECKING, Any

from whoosh.fields import Schema
from whoosh.index import create_in, open_dir
from whoosh_modern.data_sources import DataSource

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def _rmtree_retry(path: str, retries: int = 20, delay: float = 0.5) -> None:
    """Remove a directory tree, retrying on Windows permission errors.

    On Windows, files created by worker processes can remain briefly
    locked after the process pool shuts down. Retrying with small
    delays avoids spurious failures in tests and cleanup paths.

    Args:
        path: Path to the directory tree to remove.
        retries: Maximum number of retry attempts. Defaults to 20.
        delay: Delay in seconds between retries. Defaults to 0.5.
    """
    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)


def _build_segment_worker(args: tuple[str, Schema, list[dict[str, Any]], int]) -> str:
    """Worker function that builds a single segment in a separate process.

    Args:
        args: A tuple of ``(temp_dir, schema, docs, docbase)`` where
            ``temp_dir`` is the output directory, ``schema`` is the Whoosh
            schema, ``docs`` is the list of document dicts, and ``docbase``
            is the starting document ID (unused in this implementation).

    Returns:
        The path to the written segment directory.
    """
    import gc

    temp_dir, schema, docs, _docbase = args
    # ``create_in`` does not create the target directory itself, so it must
    # exist before the segment's on-disk index is created.
    os.makedirs(temp_dir, exist_ok=True)
    ix = create_in(temp_dir, schema)
    writer = ix.writer(limitmb=128, multisegment=True)
    try:
        for _doc in docs:
            writer.add_document(**_doc)
        writer.commit(merge=False)
    except Exception:
        writer.cancel()
        raise
    finally:
        # Break reference cycles before dropping references so the cyclic
        # GC can reclaim the writer and its open file handles on Windows.
        if writer._searcher is not None:
            writer._searcher._ix = None
            writer._searcher = None
        del writer
        del ix
        gc.collect()
    return temp_dir


class ParallelIndexBuilder:
    """Build a Whoosh index in parallel using multiple workers.

    Each worker builds an independent segment from a batch of documents.
    After all workers complete, the segments are merged into the final index.

    Example::

        builder = ParallelIndexBuilder(
            schema=my_schema,
            index_path="indexdir",
            workers=4,
            batch_size=10000,
        )
        builder.build(source.stream_batches(batch_size=10000))
    """

    def __init__(
        self,
        schema: Schema,
        index_path: str | Path,
        workers: int = 4,
        batch_size: int = 10000,
        limitmb: int = 128,
        merge_policy: Any | None = None,
    ) -> None:
        """Initialize the parallel index builder.

        Args:
            schema: The Whoosh schema defining the index structure.
            index_path: Filesystem path where the index will be created.
            workers: Number of worker processes for parallel segment building.
                Defaults to 4.
            batch_size: Number of documents per batch submitted to a worker.
                Defaults to 10000.
            limitmb: Memory limit in MB for each worker's writer buffer.
                Defaults to 128.
            merge_policy: Optional merge policy object. If ``None``, the
                Whoosh default is used. Defaults to None.
        """
        self.schema = schema
        self.index_path = str(index_path)
        self.workers = workers
        self.batch_size = batch_size
        self.limitmb = limitmb
        self.merge_policy = merge_policy

    def build(self, batches: Iterator[list[dict[str, Any]]]) -> int:
        """Build the index from an iterable of document batches.

        Each batch is handed off to a worker process that builds its own
        segment(s) in an isolated temporary index directory (see
        ``_build_segment_worker``). Once every worker has finished, each
        worker-built segment is merged into the main index: a reader is
        opened on the worker's temporary index and its documents are added
        to the main writer via :meth:`~whoosh.writing.IndexWriter.add_reader`.
        This re-indexes the already-tokenized documents into the main
        index's segment pool without re-running any user-supplied field
        analysis, which is what allows ``writer.commit(merge=True)`` to
        subsequently see and merge all the data produced by the workers.

        Without this merge step the segments built by the workers would
        remain isolated in their own temp directories and the main index
        would end up empty after commit.

        Args:
            batches: Iterable of document lists (e.g. from
                ``source.stream_batches()``).

        Returns:
            Total number of documents indexed.
        """
        segments: list[str] = []
        total = 0

        # ``create_in`` requires the target directory to already exist, and
        # worker segments are created underneath it so the directory must
        # exist before submitting tasks.
        os.makedirs(self.index_path, exist_ok=True)

        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures: list[Future[str]] = []
            for batch in batches:
                if not batch:
                    continue
                temp_dir = os.path.join(self.index_path, f"_segment_{len(futures)}")
                future = executor.submit(
                    _build_segment_worker,
                    (temp_dir, self.schema, batch, 0),
                )
                futures.append(future)
                total += len(batch)

            for future in futures:
                try:
                    temp_dir = future.result()
                    segments.append(temp_dir)
                except Exception as exc:
                    logger.error("Worker failed: %s", exc)
                    raise

        ix = create_in(self.index_path, self.schema)
        writer = ix.writer(limitmb=self.limitmb)
        try:
            for segment_dir in segments:
                # Open the worker's isolated index and merge its documents
                # into the main writer's segment pool. ``add_reader`` copies
                # the stored fields and postings for every document in the
                # reader into the current segment being built by ``writer``,
                # which is how independently-built segments get combined
                # into a single index.
                segment_ix = open_dir(segment_dir)
                try:
                    segment_reader = segment_ix.reader()
                    assert segment_reader is not None
                    try:
                        writer.add_reader(segment_reader)
                    finally:
                        segment_reader.close()
                finally:
                    segment_ix.close()
            writer.commit(merge=True)
        except Exception:
            writer.cancel()
            raise
        finally:
            # Explicitly drop references and collect garbage so Windows
            # can release file handles before we attempt cleanup.
            writer = None
            ix = None
            gc.collect()
            # Clean up the worker temp directories now that their segments
            # have been folded into the main index (or discarded on error).
            for segment_dir in segments:
                _rmtree_retry(segment_dir)

        return total

    def build_from_source(self, source: DataSource) -> int:
        """Build the index directly from a DataSource.

        Args:
            source: Any object implementing ``stream_batches(batch_size)``.

        Returns:
            Total number of documents indexed.
        """
        return self.build(source.stream_batches(self.batch_size))
