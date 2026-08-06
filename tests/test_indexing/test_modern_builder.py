"""Tests for ModernIndexBuilder, in particular parallel segment building."""

from __future__ import annotations

import os

import pytest

from whoosh import fields
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh_modern.indexing.modern_builder import ModernIndexBuilder


def _check_multi() -> None:
    """Skip the test if multiprocessing is not available/usable."""
    try:
        import multiprocessing
        import multiprocessing.synchronize  # noqa: F401
    except ImportError:
        pytest.skip("multiprocessing not available")

    try:
        from multiprocessing import Queue

        Queue()
    except OSError:
        pytest.skip("multiprocessing synchronization primitives not available")


class ListSource:
    """Simple in-memory data source exposing iter_documents()."""

    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def iter_documents(self):
        return iter(self._docs)


def _make_schema() -> fields.Schema:
    return fields.Schema(
        id=fields.ID(stored=True),
        title=fields.TEXT(stored=True),
    )


def _make_docs(n: int) -> list[dict]:
    return [{"id": str(i), "title": f"doc {i} hello world"} for i in range(n)]


class TestModernIndexBuilderParallel:
    def test_build_parallel_merges_all_segments(self, tmp_path):
        """Regression test: parallel building must not discard worker segments.

        Previously the merge loop after collecting worker segment
        directories was a no-op, so ``writer.commit(merge=True)`` had
        nothing to merge and the resulting index was empty.
        """
        _check_multi()

        schema = _make_schema()
        index_path = str(tmp_path / "idx")
        os.makedirs(index_path)
        docs = _make_docs(40)

        builder = ModernIndexBuilder(
            schema=schema,
            index_path=index_path,
            source=ListSource(docs),
            batch_size=10,
            workers=3,
        )
        total = builder.build()

        assert total == len(docs)

        ix = open_dir(index_path)
        assert ix.doc_count() == len(docs)

        with ix.searcher() as searcher:
            query = QueryParser("title", schema).parse("hello")
            results = searcher.search(query, limit=None)
            assert len(results) == len(docs)

            stored_ids = {hit["id"] for hit in results}
            assert stored_ids == {str(i) for i in range(len(docs))}

    def test_build_parallel_cleans_up_segment_directories(self, tmp_path):
        _check_multi()

        schema = _make_schema()
        index_path = str(tmp_path / "idx")
        os.makedirs(index_path)
        docs = _make_docs(20)

        builder = ModernIndexBuilder(
            schema=schema,
            index_path=index_path,
            source=ListSource(docs),
            batch_size=5,
            workers=2,
        )
        builder.build()

        leftover = [
            name
            for name in os.listdir(tmp_path)
            if name != "idx" and name.startswith("idx_segment_")
        ]
        assert leftover == []
