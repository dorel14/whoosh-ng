from __future__ import annotations

from whoosh.vector.base import VectorField, VectorHit, VectorProvider

try:
    from whoosh_modern.vector.numpy_provider import NumpyProvider
except ImportError:
    NumpyProvider = None

__all__ = ["VectorField", "VectorHit", "VectorProvider", "NumpyProvider"]
