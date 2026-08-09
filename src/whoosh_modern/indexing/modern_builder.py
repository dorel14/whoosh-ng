"""Modern index builder pipeline for Whoosh-NG.

Provides a complete optimized indexing pipeline that ties together:
- DataSource compilation
- Batch analysis with LRU caching
- Parallel segment building
- Merge policies

Author: dorel14
Version: 3.0.0

This is the recommended entry point for large-scale indexing.

Example::

    from whoosh_modern.indexing import ModernIndexBuilder

    builder = ModernIndexBuilder(
        schema=my_schema,
        index_path="indexdir",
        source=source,
        batch_size=5000,
        workers=4,
    )
    builder.build()
"""

from __future__ import annotations

import gc
import logging
import os
import shutil
import time
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Any

from whoosh.fields import Schema
from whoosh.index import create_in, open_dir
from whoosh_modern.indexing.batch_writer import BatchIndexWriter
from whoosh_modern.indexing.compiler import BatchAnalyzer, CompiledDataSource

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


class ModernIndexBuilder:
    """Complete optimized indexing pipeline for large datasets.

    Combines DataSource compilation, batch analysis with LRU caching,
    and parallel segment building for maximum throughput.

    Example::

        builder = ModernIndexBuilder(
            schema=my_schema,
            index_path="indexdir",
            source=csv_source,
            batch_size=5000,
            workers=4,
        )
        builder.build()
    """

    def __init__(
        self,
        schema: Schema,
        index_path: str,
        source: Any,
        batch_size: int = 5000,
        limitmb: int = 512,
        workers: int = 1,
        cache_size: int = 10000,
        multisegment: bool = True,
        merge_policy: Any | None = None,
    ) -> None:
        """Initialize the modern index builder.

        Args:
            schema: The Whoosh schema defining the index structure.
            index_path: Filesystem path where the index will be created.
            source: The data source to index (must support ``iter_documents``
                or ``stream_batches``).
            batch_size: Number of documents per batch. Defaults to 5000.
            limitmb: Memory limit in MB for the writer buffer. Defaults to 512.
            workers: Number of worker processes for parallel building.
                If 1, builds sequentially. Defaults to 1.
            cache_size: Maximum LRU cache size for the batch analyzer.
                Defaults to 10000.
            multisegment: If True, write each batch as a separate segment.
                Defaults to True.
            merge_policy: Optional merge policy object. If ``None``, the
                Whoosh default is used. Defaults to None.
        """
        self.schema = schema
        self.index_path = index_path
        self.source = source
        self.batch_size = batch_size
        self.limitmb = limitmb
        self.workers = workers
        self.cache_size = cache_size
        self.multisegment = multisegment
        self.merge_policy = merge_policy

    def _compile_source(self) -> CompiledDataSource:
        """Compile the data source for optimized batch processing.

        Returns:
            A ``CompiledDataSource`` wrapping the source.
        """
        return CompiledDataSource(self.source)

    def build(self) -> int:
        """Build the index from the data source.

        Delegates to parallel or sequential building depending on the
        configured number of workers.

        Returns:
            The total number of documents indexed.
        """
        compiled = self._compile_source()
        ix = create_in(self.index_path, self.schema)
        total = 0

        if self.workers > 1:
            total = self._build_parallel(ix, compiled)
        else:
            total = self._build_sequential(ix, compiled)

        return total

    def _build_sequential(self, ix: Any, compiled: CompiledDataSource) -> int:
        """Build the index sequentially with batch analysis.

        Args:
            ix: The open Whoosh index to write into.
            compiled: The compiled data source providing batch iteration.

        Returns:
            The total number of documents indexed.
        """
        with BatchIndexWriter(
            ix,
            batch_size=self.batch_size,
            limitmb=self.limitmb,
            multisegment=self.multisegment,
        ) as writer:
            schema_fields = set(ix.schema.names())
            analyzer = BatchAnalyzer(
                writer=writer,
                batch_size=self.batch_size,
                cache_size=self.cache_size,
                schema_fields=schema_fields,
            )

            for batch in compiled.stream_batches(batch_size=self.batch_size):
                analyzer.process_batch(batch)

            total = analyzer.flush()
        return total

    def _build_parallel(self, ix: Any, compiled: CompiledDataSource) -> int:
        """Build the index in parallel using multiple workers.

        Each batch is submitted to a separate worker process that builds
        its own segment. Segments are then merged into the main index.

        Args:
            ix: The open Whoosh index to write into.
            compiled: The compiled data source providing batch iteration.

        Returns:
            The total number of documents indexed.
        """
        segments: list[str] = []
        batches = list(compiled.stream_batches(batch_size=self.batch_size))

        # Worker segments are created underneath the index path, so the
        # directory must exist before submitting tasks.
        os.makedirs(self.index_path, exist_ok=True)

        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures: list[Future[str]] = []
            for i, batch in enumerate(batches):
                if not batch:
                    continue
                temp_dir = os.path.join(self.index_path, f"_segment_{i}")
                future = executor.submit(
                    _build_segment_worker,
                    (temp_dir, self.schema, batch, 0),
                )
                futures.append(future)

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
            for segment_dir in segments:
                _rmtree_retry(segment_dir)

        return sum(len(batch) for batch in batches)


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
    import os

    from whoosh.index import create_in

    temp_dir, schema, docs, _docbase = args
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
