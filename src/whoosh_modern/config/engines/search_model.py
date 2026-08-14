"""Engine for building search-model mappings from ``WhooshNGConfig.fields``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.config.models import WhooshNGConfig


class SearchModelEngine:
    """Build search-model mappings from ``WhooshNGConfig.fields``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> dict[str, dict[str, Any]]:
        """Build search-model mappings from the configured fields.

        Returns:
            A dictionary mapping field names to their search model configuration.
        """
        return {
            name: {
                "type": field_config.type,
                "language": field_config.language,
                "stemming": field_config.stemming,
                "stopwords": field_config.stopwords,
                "synonyms": field_config.synonyms,
                "stored": field_config.stored,
                "sortable": field_config.sortable,
                "faceted": field_config.faceted,
            }
            for name, field_config in self._config.fields.items()
        }
