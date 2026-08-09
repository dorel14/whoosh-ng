"""FacetManager with auto-discovery and manual override capabilities.

Author: dorel14
Version: 3.0.0
"""

from typing import Any

from whoosh.fields import Schema


class TermsFacet:
    """Facet for term-based field values.

    Attributes:
        limit: Maximum number of terms to return per facet.
    """

    def __init__(self, limit: int = 100) -> None:
        """Initialize a TermsFacet.

        Args:
            limit: Maximum number of terms to return (default: 100).
        """
        self.limit = limit


class RangeFacet:
    """Facet for numeric range values.

    Attributes:
        buckets: List of range bucket definitions.
    """

    def __init__(self, buckets: list[str] | None = None) -> None:
        """Initialize a RangeFacet.

        Args:
            buckets: Optional list of range bucket strings.
        """
        self.buckets = buckets or []


class DateRangeFacet:
    """Facet for date range values.

    Attributes:
        buckets: List of date range bucket definitions.
    """

    def __init__(self, buckets: list[str] | None = None) -> None:
        """Initialize a DateRangeFacet.

        Args:
            buckets: Optional list of date range bucket strings.
        """
        self.buckets = buckets or []


Facet = TermsFacet | RangeFacet | DateRangeFacet


class FacetManager:
    """Manages facet configuration for a Whoosh Schema.

    Auto-discovers facets from schema fields, then applies manual
    overrides. Manual overrides take precedence over auto-discovered
    facets when both exist for the same field.

    For TEXT fields, a TermsFacet with a configurable limit is used
    for auto-discovery instead of returning None.

    Attributes:
        _schema: The Whoosh Schema this manager is bound to.
        _config: Manual facet configuration overrides.
        _auto_discovered: Auto-discovered facets keyed by field name.
        _facets: Manually configured facets keyed by field name.
    """

    def __init__(
        self,
        schema: Schema,
        config: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the FacetManager and auto-discover facets.

        Args:
            schema: The Whoosh Schema to auto-discover facets from.
            config: Optional manual facet configuration overrides.
        """
        self._schema = schema
        self._config = config or {}
        self._auto_discovered: dict[str, Facet] = {}
        self._facets: dict[str, Facet] = {}
        self._auto_discover_facets()

    def _auto_discover_facets(self) -> None:
        """Auto-discover facets from schema fields."""
        for field_name, field_type in self._schema.items():
            facet = self._auto_discover_field(field_name, field_type)
            if facet is not None:
                self._auto_discovered[field_name] = facet

    def _auto_discover_field(self, field_name: str, field_type: Any) -> Facet | None:
        """Auto-discover facet type for a single field.

        Args:
            field_name: The name of the field.
            field_type: The Whoosh field type instance.

        Returns:
            A Facet instance appropriate for the field type, or None
            if the field type is not facetable.
        """
        field_type_name = type(field_type).__name__

        if field_type_name in ("KEYWORD", "BOOLEAN", "ID", "TEXT"):
            return TermsFacet(limit=100)
        if field_type_name == "NUMERIC":
            return RangeFacet()
        if field_type_name == "DATETIME":
            return DateRangeFacet()
        return None

    def set_manual_override(
        self, field_name: str, config: dict[str, Any], force: bool = False
    ) -> None:
        """Set manual configuration for a facet, overriding auto-discovery.

        Args:
            field_name: The name of the field to configure.
            config: Facet configuration dict.
            force: If True, override even auto-discovered facets
                that weren't explicitly configured before.
        """
        if field_name in self._auto_discovered and not force:
            if field_name not in self._config:
                self._config[field_name] = config
        else:
            self._config[field_name] = config
        facet = self._create_facet_from_config(config)
        if facet is not None:
            self._facets[field_name] = facet

    def get_facets(self) -> dict[str, Facet]:
        """Return merged auto + manual facets.

        Returns:
            A dict mapping field names to Facet instances, with manual
            overrides taking precedence over auto-discovered facets.
        """
        result: dict[str, Facet] = dict(self._auto_discovered)
        result.update(self._facets)
        return result

    def get_facet_config(self, field_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific field.

        Args:
            field_name: The name of the field to look up.

        Returns:
            The configuration dict for the field, or None if not configured.
        """
        return self._config.get(field_name)

    def get_all_facet_configs(self) -> dict[str, dict[str, Any]]:
        """Get configurations for all faceted fields.

        Returns:
            A dict mapping field names to their configuration dicts.
        """
        return dict(self._config)

    def is_facetable(self, field_name: str) -> bool:
        """Check if a field can be used for faceting.

        Args:
            field_name: The name of the field to check.

        Returns:
            True if the field has an auto-discovered or manually
            configured facet, False otherwise.
        """
        return field_name in self._auto_discovered or field_name in self._facets

    def get_facet_stats(self) -> dict[str, Any]:
        """Get statistics about facet configuration.

        Returns:
            A dict with keys: ``total_fields``, ``auto_discovered_facets``,
            ``manual_overrides``, ``total_facets_configured``, and
            ``facet_fields``.
        """
        return {
            "total_fields": len(self._schema),
            "auto_discovered_facets": len(self._auto_discovered),
            "manual_overrides": len(self._facets),
            "total_facets_configured": len(self._config),
            "facet_fields": list(self._config.keys()),
        }

    def _create_facet_from_config(self, config: dict[str, Any]) -> Facet | None:
        """Create a Facet instance from a config dict.

        Args:
            config: Configuration dict with a ``type`` key
                ("terms", "range", or "date_range") and type-specific
                parameters.

        Returns:
            A Facet instance, or None if the type is unrecognized.
        """
        facet_type = config.get("type", "terms")
        if facet_type == "terms":
            return TermsFacet(limit=config.get("limit", 100))
        if facet_type == "range":
            return RangeFacet(buckets=config.get("buckets"))
        if facet_type == "date_range":
            return DateRangeFacet(buckets=config.get("buckets"))
        return None
