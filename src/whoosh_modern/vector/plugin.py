"""Vector plugin for Whoosh-NG.

Registers the NumpyProvider in the vector registry upon plugin load.

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.plugins.manager import Plugin
from whoosh.registry import VectorRegistry
from whoosh_modern.vector.numpy_provider import NumpyProvider


class VectorPlugin(Plugin):
    """Vector search plugin for Whoosh-NG.

    Registers a NumpyProvider with the VectorRegistry when
    :meth:`register` is called.
    """

    name = "whoosh_vector"
    version = "5.0.0"

    def register(self, manager: Any) -> None:
        """Register the NumPy vector provider in the registry.

        Args:
            manager: The Whoosh plugin manager.
        """
        VectorRegistry.register("numpy", NumpyProvider(), self.name)


__all__ = ["VectorPlugin"]
