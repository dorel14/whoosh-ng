"""Tests for HybridSearcher."""

from __future__ import annotations

from typing import Any

import pytest

from whoosh import fields
from whoosh.fields import TEXT
from whoosh.index import create_in
from whoosh.searching import Searcher
from whoosh_modern.fields.vector import VECTOR
from whoosh_modern.searching.hybrid import HybridResult, HybridSearcher
from whoosh_modern.vector.numpy_provider import NumpyProvider


def _build_searcher(tmp_path: Any) -> tuple[Searcher, NumpyProvider]:
    idx_dir = tmp_path / "index"
    idx_dir.mkdir()
    schema = fields.Schema(id=TEXT(stored=True), title=TEXT(stored=True), content=TEXT)
    ix = create_in(str(idx_dir), schema)
    writer = ix.writer()
    writer.add_document(id="doc1", title="python search", content="python is great")
    writer.add_document(id="doc2", title="java search", content="java is verbose")
    writer.add_document(id="doc3", title="python java", content="both languages")
    writer.commit()
    searcher = ix.searcher()
    provider = NumpyProvider()
    provider.add(
        [
            ("doc1", [1.0, 0.0]),
            ("doc2", [0.0, 1.0]),
            ("doc3", [0.707, 0.707]),
        ]
    )
    return searcher, provider


def _build_native_searcher(tmp_path: Any) -> Searcher:
    idx_dir = tmp_path / "native_index"
    idx_dir.mkdir()
    schema = fields.Schema(
        id=fields.TEXT(stored=True),
        title=fields.TEXT(stored=True),
        content=fields.TEXT,
        embedding=VECTOR(dimension=4, dtype="float32", normalized=True),
    )
    ix = create_in(str(idx_dir), schema)
    writer = ix.writer()
    writer.add_document(
        id="doc1", title="python search", content="python is great",
        embedding=[1.0, 0.0, 0.0, 0.0],
    )
    writer.add_document(
        id="doc2", title="java search", content="java is verbose",
        embedding=[0.0, 1.0, 0.0, 0.0],
    )
    writer.add_document(
        id="doc3", title="python java", content="both languages",
        embedding=[0.707, 0.707, 0.0, 0.0],
    )
    writer.commit()
    return ix.searcher()


class TestHybridSearcher:
    def test_search_returns_results(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=[1.0, 0.0])
        assert len(results) > 0
        assert isinstance(results[0], HybridResult)

    def test_weighted_merge(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=[1.0, 0.0], method="weighted")
        assert len(results) > 0
        doc_ids = [r.doc_id for r in results]
        assert "doc1" in doc_ids

    def test_rrf_fusion(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=[1.0, 0.0], method="rrf")
        assert len(results) > 0
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_query_vector_none(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=None)
        assert len(results) > 0
        for r in results:
            assert r.vector_score == 0.0

    def test_bm25_only_fallback(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=None, method="weighted")
        assert len(results) > 0
        for r in results:
            assert r.bm25_score > 0.0

    def test_limit(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=[1.0, 0.0], limit=2)
        assert len(results) <= 2

    def test_alpha_extreme(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        bm25_only = hs.search("python", query_vector=[1.0, 0.0], alpha=1.0)
        vector_only = hs.search("python", query_vector=[1.0, 0.0], alpha=0.0)
        assert len(bm25_only) > 0
        assert len(vector_only) > 0

    def test_invalid_method(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        with pytest.raises(ValueError, match="Unknown fusion method"):
            hs.search("python", method="invalid")

    def test_invalid_alpha(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        with pytest.raises(ValueError, match="alpha must be in"):
            hs.search("python", alpha=1.5)

    def test_empty_results(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("nonexistent", query_vector=[1.0, 0.0])
        assert len(results) > 0
        assert all(r.bm25_score == 0.0 for r in results)

    def test_result_has_fields(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=[1.0, 0.0])
        assert results
        assert "title" in results[0].fields

    def test_result_ranks_are_sequential(self, tmp_path: Any) -> None:
        searcher, provider = _build_searcher(tmp_path)
        hs = HybridSearcher(searcher, provider, id_field="id")
        results = hs.search("python", query_vector=[1.0, 0.0], limit=3)
        ranks = [r.rank for r in results]
        assert ranks == list(range(len(results)))


class TestHybridSearcherNative:
    def test_native_search_returns_results(self, tmp_path: Any) -> None:
        searcher = _build_native_searcher(tmp_path)
        hs = HybridSearcher(searcher, vector_column="embedding")
        results = hs.search("python", query_vector=[1.0, 0.0, 0.0, 0.0])
        assert len(results) > 0
        assert isinstance(results[0], HybridResult)

    def test_native_weighted_merge(self, tmp_path: Any) -> None:
        searcher = _build_native_searcher(tmp_path)
        hs = HybridSearcher(searcher, vector_column="embedding")
        results = hs.search("python", query_vector=[1.0, 0.0, 0.0, 0.0], method="weighted")
        assert len(results) > 0
        doc_ids = [r.doc_id for r in results]
        assert "doc1" in doc_ids

    def test_native_rrf_fusion(self, tmp_path: Any) -> None:
        searcher = _build_native_searcher(tmp_path)
        hs = HybridSearcher(searcher, vector_column="embedding")
        results = hs.search("python", query_vector=[1.0, 0.0, 0.0, 0.0], method="rrf")
        assert len(results) > 0
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_native_bm25_only(self, tmp_path: Any) -> None:
        searcher = _build_native_searcher(tmp_path)
        hs = HybridSearcher(searcher, vector_column="embedding")
        results = hs.search("python", query_vector=None)
        assert len(results) > 0
        for r in results:
            assert r.vector_score == 0.0

    def test_native_result_has_fields(self, tmp_path: Any) -> None:
        searcher = _build_native_searcher(tmp_path)
        hs = HybridSearcher(searcher, vector_column="embedding")
        results = hs.search("python", query_vector=[1.0, 0.0, 0.0, 0.0])
        assert results
        assert "title" in results[0].fields

    def test_native_result_ranks_are_sequential(self, tmp_path: Any) -> None:
        searcher = _build_native_searcher(tmp_path)
        hs = HybridSearcher(searcher, vector_column="embedding")
        results = hs.search("python", query_vector=[1.0, 0.0, 0.0, 0.0], limit=3)
        ranks = [r.rank for r in results]
        assert ranks == list(range(len(results)))

    def test_native_invalid_column_raises(self, tmp_path: Any) -> None:
        searcher = _build_native_searcher(tmp_path)
        with pytest.raises(ValueError, match="not found in schema"):
            HybridSearcher(searcher, vector_column="nonexistent")
