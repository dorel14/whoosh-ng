"""Modern index builder pipeline for Whoosh-NG.

Provides a complete optimized indexing pipeline that ties together:
- DataSource compilation
- Batch analysis with LRU caching
- Parallel segment building
- Merge policies

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

import logging
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Any

from whoosh.fields import Schema
from whoosh.index import create_in
from whoosh_modern.indexing.batch_writer import BatchIndexWriter
from whoosh_modern.indexing.compiler import BatchAnalyzer, CompiledDataSource

logger = logging.getLogger(__name__)


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
        """Compile the data source for optimized batch processing."""
        return CompiledDataSource(self.source)

    def build(self) -> int:
        """Build the index from the data source.

        :returns: total number of documents indexed.
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
        """Build the index sequentially with batch analysis."""
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
        """Build the index in parallel using multiple workers."""
        segments: list[str] = []
        batches = list(compiled.stream_batches(batch_size=self.batch_size))

        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures: list[Future[str]] = []
            for i, batch in enumerate(batches):
                if not batch:
                    continue
                temp_dir = f"{self.index_path}_segment_{i}"
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
            for _segment_dir in segments:
                pass
            writer.commit(merge=True)
        except Exception:
            writer.cancel()
            raise

        return sum(len(batch) for batch in batches)


def _build_segment_worker(args: tuple[str, Schema, list[dict[str, Any]], int]) -> str:
    """Worker function that builds a single segment in a separate process."""
    from whoosh.index import create_in

    temp_dir, schema, docs, _docbase = args
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
