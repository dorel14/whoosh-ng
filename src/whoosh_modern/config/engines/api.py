"""Engine for building a FastAPI application from ``WhooshNGConfig``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.config.models import WhooshNGConfig


class APIEngine:
    """Build a FastAPI application from ``WhooshNGConfig``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self, index: Any) -> Any:
        """Build a FastAPI application from the configured search settings.

        Args:
            index: An open Whoosh Index instance.

        Returns:
            A FastAPI application instance.
        """
        try:
            from whoosh_fastapi import create_app
        except ImportError as exc:
            raise ImportError(
                "FastAPI plugin requires fastapi. Install with: pip install whoosh-ng[api]"
            ) from exc
        return create_app(index, prefix="/api/v1")
