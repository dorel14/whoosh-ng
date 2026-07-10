"""Tests for vector providers."""

import pytest


def test_vector_registry_exists():
    """Test that VectorRegistry is available."""
    from whoosh.registry import VectorRegistry

    assert VectorRegistry is not None
    assert hasattr(VectorRegistry, "register")
    assert hasattr(VectorRegistry, "get")


def test_hnsw_provider_optional():
    """Test that HNSWProvider is available when hnswlib is installed."""
    try:
        import hnswlib  # noqa: F401
    except ImportError:
        pytest.skip("hnswlib not installed - HNSWProvider requires optional dependency")

    from whoosh.providers.hnsw import HNSWProvider

    assert HNSWProvider is not None


def test_vector_provider_base():
    """Test VectorProvider base class interface."""
    from whoosh.vector.base import VectorProvider

    assert hasattr(VectorProvider, "add")
    assert hasattr(VectorProvider, "search")
    assert hasattr(VectorProvider, "remove")
