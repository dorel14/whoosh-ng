"""Tests for vector providers."""

from __future__ import annotations

import pytest

from whoosh_modern.vector.hnswlib_provider import HnswlibProvider
from whoosh_modern.vector.numpy_provider import NumpyProvider


def test_numpy_provider_search() -> None:
    provider = NumpyProvider()
    provider.add(
        [
            ("doc1", [1.0, 0.0, 0.0]),
            ("doc2", [0.0, 1.0, 0.0]),
            ("doc3", [0.0, 0.0, 1.0]),
        ]
    )
    results = provider.search([1.0, 0.0, 0.0], k=1)
    assert len(results) == 1
    assert results[0].doc_id == "doc1"
    assert results[0].score == pytest.approx(1.0, abs=1e-6)


def test_numpy_provider_empty() -> None:
    provider = NumpyProvider()
    assert provider.search([1.0, 0.0]) == []


@pytest.mark.skipif(
    pytest.importorskip("hnswlib", reason="hnswlib not installed") is None,
    reason="hnswlib not installed",
)
def test_hnswlib_provider_search() -> None:
    provider = HnswlibProvider(dimension=3, space="l2", max_elements=100)
    provider.add(
        [
            ("doc1", [1.0, 0.0, 0.0]),
            ("doc2", [0.0, 1.0, 0.0]),
            ("doc3", [0.0, 0.0, 1.0]),
        ]
    )
    results = provider.search([1.0, 0.0, 0.0], k=1)
    assert len(results) == 1
    assert results[0].doc_id == "doc1"
