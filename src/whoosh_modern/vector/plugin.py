from __future__ import annotations

from whoosh.plugins.manager import Plugin
from whoosh.registry import VectorRegistry
from whoosh_modern.vector.numpy_provider import NumpyProvider


class VectorPlugin(Plugin):
    name = "whoosh_vector"
    version = "4.0.0"

    def register(self, manager) -> None:
        VectorRegistry.register("numpy", NumpyProvider(), self.name)


__all__ = ["VectorPlugin"]
