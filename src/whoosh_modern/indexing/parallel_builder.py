"""Parallel index builder for Whoosh.

Uses ``concurrent.futures`` to build multiple index segments concurrently,
then merges them into a single index. This provides near-linear speedups on
multi-core machines for CPU-bound indexing workloads.
"""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Iterator
from concurrent.futures import Future, ProcessPoolExecutor
from typing import TYPE_CHECKING, Any

from whoosh.fields import Schema
from whoosh.index import create_in, open_dir
from whoosh_modern.data_sources import DataSource

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def _build_segment_worker(args: tuple[str, Schema, list[dict[str, Any]], int]) -> str:
    """Worker function that builds a single segment in a separate process.

    :param args: tuple of (temp_dir, schema, docs, docbase)
    :returns: path to the written segment directory
    """
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

        :param batches: iterable of document lists (e.g. from
            ``source.stream_batches()``).
        :returns: total number of documents indexed.
        """
        segments: list[str] = []
        total = 0

        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures: list[Future[str]] = []
            for batch in batches:
                if not batch:
                    continue
                temp_dir = f"{self.index_path}_segment_{len(futures)}"
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

        # ``create_in`` requires the target directory to already exist.
        os.makedirs(self.index_path, exist_ok=True)
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
            # Clean up the worker temp directories now that their segments
            # have been folded into the main index (or discarded on error).
            for segment_dir in segments:
                shutil.rmtree(segment_dir, ignore_errors=True)

        return total

    def build_from_source(self, source: DataSource) -> int:
        """Build the index directly from a DataSource.

        :param source: any object implementing ``stream_batches(batch_size)``.
        :returns: total number of documents indexed.
        """
        return self.build(source.stream_batches(self.batch_size))
