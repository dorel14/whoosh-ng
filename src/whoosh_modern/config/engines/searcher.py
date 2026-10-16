"""Searcher engine for Whoosh-NG configuration.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from whoosh_modern.config.models import SearcherConfig, WhooshNGConfig


class SearcherEngine:
    """Builds searcher configuration from the global Whoosh-NG config.

    Attributes:
        _config: The top-level Whoosh-NG configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the searcher engine.

        Args:
            config: The validated Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> SearcherConfig:
        """Return the searcher configuration block.

        Returns:
            The ``SearcherConfig`` instance from ``config.search.searcher``.
        """
        return self._config.search.searcher


__all__ = ["SearcherEngine"]
