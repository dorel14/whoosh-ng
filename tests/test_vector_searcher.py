"""Tests for native VectorSearcher."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from whoosh import fields
from whoosh.index import create_in
from whoosh_modern.fields.vector import VECTOR
from whoosh_modern.searching.vector_searcher import VectorSearcher

pytest.importorskip("numpy")


def _build_index(tmp_path: Any) -> Any:
    idx_dir = tmp_path / "index"
    idx_dir.mkdir()
    schema = fields.Schema(
        id=fields.TEXT(stored=True),
        embedding=VECTOR(dimension=4, dtype="float32", normalized=True),
    )
    ix = create_in(str(idx_dir), schema)
    writer = ix.writer()
    writer.add_document(id="doc1", embedding=[1.0, 0.0, 0.0, 0.0])
    writer.add_document(id="doc2", embedding=[0.0, 1.0, 0.0, 0.0])
    writer.add_document(id="doc3", embedding=[0.707, 0.707, 0.0, 0.0])
    writer.commit()
    return ix


class TestVectorSearcher:
    def test_search_returns_results(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            vs = VectorSearcher(r, "embedding")
            hits = vs.search([1.0, 0.0, 0.0, 0.0], k=3)
            assert len(hits) == 3
            assert all(isinstance(h, tuple) and len(h) == 2 for h in hits)

    def test_top1_is_identical(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            vs = VectorSearcher(r, "embedding")
            hits = vs.search([1.0, 0.0, 0.0, 0.0], k=1)
            assert len(hits) == 1
            docnum, score = hits[0]
            assert pytest.approx(score, abs=1e-6) == 1.0

    def test_scores_descending(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            vs = VectorSearcher(r, "embedding")
            hits = vs.search([1.0, 0.0, 0.0, 0.0], k=3)
            scores = [s for _, s in hits]
            assert scores == sorted(scores, reverse=True)

    def test_empty_query_returns_empty(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            vs = VectorSearcher(r, "embedding")
            hits = vs.search([0.0, 0.0, 0.0, 0.0], k=3)
            assert hits == []

    def test_k_larger_than_index(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            vs = VectorSearcher(r, "embedding")
            hits = vs.search([1.0, 0.0, 0.0, 0.0], k=100)
            assert len(hits) == 3

    def test_no_vectors_returns_empty(self, tmp_path: Any) -> None:
        idx_dir = tmp_path / "empty"
        idx_dir.mkdir()
        schema = fields.Schema(
            id=fields.TEXT(stored=True),
            embedding=VECTOR(dimension=4, dtype="float32"),
        )
        ix = create_in(str(idx_dir), schema)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            vs = VectorSearcher(r, "embedding")
            hits = vs.search([1.0, 0.0, 0.0, 0.0], k=3)
            assert hits == []
