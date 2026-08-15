"""Engine for building a ``FacetManager`` from faceted ``WhooshNGConfig.fields``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh.fields import Schema
from whoosh_modern.config.models import WhooshNGConfig
from whoosh_modern.facets import FacetManager


class FacetEngine:
    """Build a ``FacetManager`` from faceted ``WhooshNGConfig.fields``.

    Attributes:
        _config: The merged application configuration.
        _schema: Whoosh Schema to build facets from.
    """

    def __init__(self, config: WhooshNGConfig, schema: Schema) -> None:
        """Initialize the engine with a merged configuration and schema.

        Args:
            config: Merged Whoosh-NG configuration.
            schema: Whoosh Schema to build facets from.
        """
        self._config = config
        self._schema = schema

    def build(self) -> FacetManager:
        """Build a FacetManager from the configured faceted fields.

        Returns:
            A FacetManager instance.
        """
        facet_config = {
            name: {"type": field_config.type, "faceted": field_config.faceted}
            for name, field_config in self._config.fields.items()
            if field_config.faceted
        }
        return FacetManager(self._schema, config=facet_config)
