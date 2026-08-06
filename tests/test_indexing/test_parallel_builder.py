"""Tests for ParallelIndexBuilder.

These tests exercise the full multi-process build path (real worker
processes via ``ProcessPoolExecutor``) to make sure segments built in
worker temp directories actually get merged into the final index rather
than silently discarded, which was the cause of a critical bug where
parallel indexing produced an empty index.
"""

import os
import tempfile

import pytest

from whoosh import fields
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh_modern.indexing import ParallelIndexBuilder


def _require_multiprocessing():
    """Skip the test if the sandbox does not support real subprocesses.

    Some restricted/sandboxed environments (e.g. containers without a
    working ``/dev/shm``) cannot create the synchronization primitives
    needed by ``multiprocessing``/``ProcessPoolExecutor``. These tests need
    real worker processes to exercise the bug they guard against, so skip
    them there instead of failing for environmental reasons.
    """
    try:
        from multiprocessing import Queue

        Queue()
    except OSError:
        pytest.skip("multiprocessing is not available in this environment")


def _schema():
    return fields.Schema(
        id=fields.ID(stored=True, unique=True),
        title=fields.TEXT(stored=True),
        body=fields.TEXT(),
    )


class TestParallelIndexBuilder:
    def test_build_indexes_all_documents(self):
        _require_multiprocessing()
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "idx")
            schema = _schema()
            builder = ParallelIndexBuilder(
                schema=schema,
                index_path=index_path,
                workers=2,
                batch_size=5,
            )
            batches = [
                [
                    {"id": "1", "title": "Hello world", "body": "First document body"},
                    {"id": "2", "title": "Python rocks", "body": "Second document body"},
                    {"id": "3", "title": "Whoosh search", "body": "Third document body"},
                ],
                [
                    {"id": "4", "title": "Parallel builder", "body": "Fourth document body"},
                    {"id": "5", "title": "Segment merge", "body": "Fifth document body"},
                ],
            ]

            total = builder.build(iter(batches))

            assert total == 5

            ix = open_dir(index_path)
            try:
                assert ix.doc_count() == 5

                with ix.searcher() as searcher:
                    parser = QueryParser("title", schema=schema)
                    results = searcher.search(parser.parse("Python"))
                    assert len(results) == 1
                    assert results[0]["id"] == "2"

                    results_all = searcher.search(parser.parse("title:*"))
                    assert len(results_all) >= 1
            finally:
                ix.close()

    def test_build_cleans_up_worker_temp_dirs(self):
        _require_multiprocessing()
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "idx")
            schema = _schema()
            builder = ParallelIndexBuilder(
                schema=schema,
                index_path=index_path,
                workers=2,
                batch_size=5,
            )
            batches = [
                [{"id": "1", "title": "Hello", "body": "World"}],
                [{"id": "2", "title": "Foo", "body": "Bar"}],
            ]

            builder.build(iter(batches))

            # Worker temp directories should have been removed after their
            # segments were merged into the main index.
            for name in os.listdir(tmpdir):
                assert "segment" not in name

    def test_build_from_source(self):
        _require_multiprocessing()
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "idx")
            schema = _schema()
            builder = ParallelIndexBuilder(
                schema=schema,
                index_path=index_path,
                workers=2,
                batch_size=2,
            )

            class _Source:
                def stream_batches(self, batch_size):
                    docs = [{"id": str(i), "title": f"doc {i}", "body": "text"} for i in range(6)]
                    for i in range(0, len(docs), batch_size):
                        yield docs[i : i + batch_size]

            total = builder.build_from_source(_Source())
            assert total == 6

            ix = open_dir(index_path)
            try:
                assert ix.doc_count() == 6
            finally:
                ix.close()
