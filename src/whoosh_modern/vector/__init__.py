"""Vector search module for Whoosh-NG.

Provides VectorField, VectorHit, and VectorProvider from the core,
along with the optional NumpyProvider and HnswlibProvider for similarity
search.

Author: dorel14
Version: 2.1.0
"""

# mypy: ignore-errors
from __future__ import annotations

from whoosh.vector.base import VectorField, VectorHit, VectorProvider

try:
    from whoosh_modern.vector.hnswlib_provider import HnswlibProvider
except ImportError:
    HnswlibProvider = None

try:
    from whoosh_modern.vector.numpy_provider import NumpyProvider
except ImportError:
    NumpyProvider = None

__all__ = ["VectorField", "VectorHit", "VectorProvider", "NumpyProvider", "HnswlibProvider"]
