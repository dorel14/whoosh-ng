"""Vector search module for Whoosh-NG.

Provides VectorField, VectorHit, and VectorProvider from the core,
along with the optional NumpyProvider for cosine similarity.

Author: dorel14
Version: 2.0.0
"""

# mypy: ignore-errors
from __future__ import annotations

from whoosh.vector.base import VectorField, VectorHit, VectorProvider

try:
    from whoosh_modern.vector.numpy_provider import NumpyProvider
except ImportError:
    NumpyProvider = None

__all__ = ["VectorField", "VectorHit", "VectorProvider", "NumpyProvider"]
