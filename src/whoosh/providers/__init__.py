"""Whoosh provider architecture for pluggable backends."""

from whoosh.registry import VectorRegistry
from whoosh.vector.base import VectorProvider

HNSWProvider = None

try:
    from whoosh.providers.hnsw import HNSWProvider as _HNSWProvider

    HNSWProvider = _HNSWProvider
    VectorRegistry.register("hnsw", HNSWProvider, "whoosh")
except ImportError:
    pass

__all__ = ["VectorProvider"]
if HNSWProvider is not None:
    __all__.append("HNSWProvider")
