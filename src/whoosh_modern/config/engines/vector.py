"""Engine for building a ``VectorProvider`` from ``WhooshNGConfig.vector``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.config.models import WhooshNGConfig


class VectorEngine:
    """Build a ``VectorProvider`` from ``WhooshNGConfig.vector``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any:
        """Build a VectorProvider from the configured vector settings.

        Returns:
            A VectorProvider instance, or ``None`` if no vector configuration
            is provided.
        """
        vector_config = self._config.vector
        if not vector_config:
            return None
        provider_type = vector_config.get("provider", "numpy").lower()
        if provider_type == "numpy":
            try:
                from whoosh_modern.vector.numpy_provider import NumpyProvider

                return NumpyProvider()
            except ImportError as exc:
                raise ImportError(
                    "NumpyProvider requires numpy. Install with: pip install numpy"
                ) from exc
        if provider_type == "hnswlib":
            try:
                from whoosh_modern.vector.hnswlib_provider import HnswlibProvider

                return HnswlibProvider(
                    dimension=int(vector_config.get("dimension", 384)),
                    space=vector_config.get("space", "l2"),
                    max_elements=int(vector_config.get("max_elements", 10000)),
                    ef_construction=int(vector_config.get("ef_construction", 200)),
                    m=int(vector_config.get("m", 16)),
                )
            except ImportError as exc:
                raise ImportError(
                    "HnswlibProvider requires hnswlib. "
                    "Install with: pip install whoosh-ng[hnsw]"
                ) from exc
        raise ValueError(f"Unsupported vector provider: {provider_type}")
