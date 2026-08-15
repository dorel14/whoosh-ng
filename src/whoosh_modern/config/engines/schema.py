"""Engine for building a Whoosh ``Schema`` from ``WhooshNGConfig.fields``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.fields import (
    BOOLEAN,
    DATETIME,
    ID,
    KEYWORD,
    NUMERIC,
    TEXT,
    Schema,
)
from whoosh_modern.config.models import WhooshNGConfig


class SchemaEngine:
    """Build a Whoosh ``Schema`` from ``WhooshNGConfig.fields``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Schema:
        """Build a Whoosh ``Schema`` from the configured fields.

        Returns:
            A configured Whoosh ``Schema`` instance.
        """
        fields: dict[str, Any] = {}
        for name, field_config in self._config.fields.items():
            field_type = field_config.type.lower()
            if field_type == "text":
                fields[name] = TEXT(stored=field_config.stored)
            elif field_type == "keyword":
                fields[name] = KEYWORD(stored=field_config.stored)
            elif field_type == "numeric":
                fields[name] = NUMERIC(stored=field_config.stored)
            elif field_type == "datetime":
                fields[name] = DATETIME(stored=field_config.stored)
            elif field_type == "boolean":
                fields[name] = BOOLEAN(stored=field_config.stored)
            elif field_type == "id":
                fields[name] = ID(stored=field_config.stored)
            else:
                fields[name] = TEXT(stored=field_config.stored)
        return Schema(**fields)
