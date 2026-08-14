"""Engine for building per-field analyzers from ``WhooshNGConfig.fields``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.analysis import StandardAnalyzer
from whoosh_modern.config.models import WhooshNGConfig


class AnalyzerEngine:
    """Build per-field analyzers from ``WhooshNGConfig.fields``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> dict[str, Any]:
        """Build an analyzer mapping from the configured fields.

        Returns:
            A dictionary mapping field names to analyzer instances.
        """
        analyzers: dict[str, Any] = {}
        for name, field_config in self._config.fields.items():
            analyzers[name] = self._build_analyzer(field_config)
        return analyzers

    def _build_analyzer(self, field_config: Any) -> Any:
        """Build an analyzer for a single field configuration.

        Args:
            field_config: Field configuration model.

        Returns:
            An analyzer instance for the field.
        """
        if not field_config.stemming and not field_config.stopwords:
            return None
        if field_config.stopwords:
            return StandardAnalyzer()
        return StandardAnalyzer(stoplist=frozenset())
