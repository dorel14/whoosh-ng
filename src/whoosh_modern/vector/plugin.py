from __future__ import annotations

from typing import Any

from whoosh.plugins.manager import Plugin
from whoosh.registry import VectorRegistry
from whoosh_modern.vector.numpy_provider import NumpyProvider


class VectorPlugin(Plugin):
    name = "whoosh_vector"
    version = "4.2.1"

    def register(self, manager: Any) -> None:
        VectorRegistry.register("numpy", NumpyProvider(), self.name)


__all__ = ["VectorPlugin"]
