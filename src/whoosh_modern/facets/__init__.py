"""FacetManager with auto-discovery and manual override capabilities."""

from typing import Any

from whoosh.fields import Schema


class TermsFacet:
    """Facet for term-based field values."""

    def __init__(self, limit: int = 100) -> None:
        self.limit = limit


class RangeFacet:
    """Facet for numeric range values."""

    def __init__(self, buckets: list[str] | None = None) -> None:
        self.buckets = buckets or []


class DateRangeFacet:
    """Facet for date range values."""

    def __init__(self, buckets: list[str] | None = None) -> None:
        self.buckets = buckets or []


Facet = TermsFacet | RangeFacet | DateRangeFacet


class FacetManager:
    """Manages facet configuration for a Whoosh Schema.

    Auto-discovers facets from schema fields, then applies manual
    overrides. Manual overrides take precedence over auto-discovered
    facets when both exist for the same field.

    For TEXT fields, a TermsFacet with a configurable limit is used
    for auto-discovery instead of returning None.
    """

    def __init__(
        self,
        schema: Schema,
        config: dict[str, dict[str, Any]] | None = None,
    ) -> None:
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
        """Auto-discover facet type for a single field."""
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
        """Return merged auto + manual facets."""
        result: dict[str, Facet] = dict(self._auto_discovered)
        result.update(self._facets)
        return result

    def get_facet_config(self, field_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific field."""
        return self._config.get(field_name)

    def get_all_facet_configs(self) -> dict[str, dict[str, Any]]:
        """Get configurations for all faceted fields."""
        return dict(self._config)

    def is_facetable(self, field_name: str) -> bool:
        """Check if a field can be used for faceting."""
        return field_name in self._auto_discovered or field_name in self._facets

    def get_facet_stats(self) -> dict[str, Any]:
        """Get statistics about facet configuration."""
        return {
            "total_fields": len(self._schema),
            "auto_discovered_facets": len(self._auto_discovered),
            "manual_overrides": len(self._facets),
            "total_facets_configured": len(self._config),
            "facet_fields": list(self._config.keys()),
        }

    def _create_facet_from_config(self, config: dict[str, Any]) -> Facet | None:
        """Create a Facet instance from a config dict."""
        facet_type = config.get("type", "terms")
        if facet_type == "terms":
            return TermsFacet(limit=config.get("limit", 100))
        if facet_type == "range":
            return RangeFacet(buckets=config.get("buckets"))
        if facet_type == "date_range":
            return DateRangeFacet(buckets=config.get("buckets"))
        return None
