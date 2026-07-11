from __future__ import annotations

import math

import pytest

pytest.importorskip("numpy")

from whoosh_modern.vector import VectorField, VectorHit
from whoosh_modern.vector.numpy_provider import NumpyProvider


@pytest.fixture
def provider() -> NumpyProvider:
    return NumpyProvider()


def test_add_and_search_sorted(provider: NumpyProvider) -> None:
    provider.add(
        [
            ("a", [1.0, 0.0]),
            ("b", [0.0, 1.0]),
            ("c", [1.0, 1.0]),
        ]
    )
    hits = provider.search([1.0, 0.0], k=3)
    assert [hit.doc_id for hit in hits] == ["a", "c", "b"]
    assert pytest.approx(hits[0].score, abs=1e-6) == 1.0


def test_filter_ids(provider: NumpyProvider) -> None:
    provider.add(
        [
            ("a", [1.0, 0.0]),
            ("b", [0.0, 1.0]),
            ("c", [1.0, 1.0]),
        ]
    )
    hits = provider.search([1.0, 0.0], filter_ids=["a", "b"])
    assert [hit.doc_id for hit in hits] == ["a", "b"]


def test_remove(provider: NumpyProvider) -> None:
    provider.add([("a", [1.0, 0.0])])
    provider.remove(["a"])
    assert provider.search([1.0, 0.0]) == []


def test_empty_search_when_no_docs(provider: NumpyProvider) -> None:
    assert provider.search([1.0, 0.0]) == []


def test_search_with_zero_norm_query(provider: NumpyProvider) -> None:
    provider.add([("a", [1.0, 0.0])])
    assert provider.search([0.0, 0.0]) == []


def test_score_is_zero_for_orthogonal(provider: NumpyProvider) -> None:
    provider.add([("a", [0.0, 1.0])])
    hit = provider.search([1.0, 0.0], k=1)[0]
    assert pytest.approx(hit.score, abs=1e-6) == 0.0


def test_vector_field_contract() -> None:
    field = VectorField(dimension=4, name="embedding")
    assert field.dimension == 4
    values = [0.1, 0.2, 0.3, 0.4]
    raw = field.vector_to_bytes(values)
    assert isinstance(raw, bytes)
    restored = field.bytes_to_vector(raw)
    assert restored == tuple(values)
