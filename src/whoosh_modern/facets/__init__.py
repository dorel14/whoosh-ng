"""FacetManager with auto-discovery and manual override capabilities.

This module re-exports the *real* core facet types from :mod:`whoosh.sorting`
(``FieldFacet``, ``RangeFacet``, ``DateRangeFacet``) instead of redefining
incompatible stubs. ``TermsFacet`` is a thin :class:`whoosh.sorting.FieldFacet`
subclass that additionally accepts a ``limit`` keyword for backward
compatibility. Consequently, every facet produced by :class:`FacetManager` is a
genuine core ``FacetType`` and can be passed directly to
``searcher.search(query, groupedby=...)``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from whoosh.fields import Schema
from whoosh.sorting import DateRangeFacet, FieldFacet, RangeFacet

__all__ = (
    "DateRangeFacet",
    "Facet",
    "FacetManager",
    "FieldFacet",
    "RangeFacet",
    "TermsFacet",
)

#: Default numeric range used when auto-discovering a NUMERIC field.
DEFAULT_NUMERIC_START: int = 0
DEFAULT_NUMERIC_END: int = 1000
DEFAULT_NUMERIC_GAP: int = 100

#: Default date range used when auto-discovering a DATETIME field.
DEFAULT_DATE_START: datetime = datetime(1970, 1, 1)  # noqa: DTZ001
DEFAULT_DATE_END: datetime = datetime(2100, 1, 1)  # noqa: DTZ001
DEFAULT_DATE_GAP: timedelta = timedelta(days=365)

#: Default maximum number of terms reported for a terms facet.
DEFAULT_TERMS_LIMIT: int = 100


class TermsFacet(FieldFacet):
    """Term-based facet, a thin wrapper around :class:`whoosh.sorting.FieldFacet`.

    It behaves exactly like a core ``FieldFacet`` (and therefore works as a
    ``groupedby=`` argument) while accepting the legacy ``limit`` and ``name``
    keyword arguments.

    Attributes:
        limit: Maximum number of terms to report for this facet.
        name: Optional display name for the facet.
    """

    def __init__(
        self,
        fieldname: str = "",
        limit: int = DEFAULT_TERMS_LIMIT,
        name: str | None = None,
        *,
        reverse: bool = False,
        allow_overlap: bool = False,
        maptype: Any = None,
    ) -> None:
        """Initialize a TermsFacet.

        Args:
            fieldname: Name of the field to facet on.
            limit: Maximum number of terms to report (default: 100).
            name: Optional display name for the facet.
            reverse: Reverse the sort order of this facet.
            allow_overlap: Allow documents to appear in multiple groups.
            maptype: Optional core ``FacetMap`` type.
        """
        super().__init__(
            fieldname,
            reverse=reverse,
            allow_overlap=allow_overlap,
            maptype=maptype,
        )
        self.limit = limit
        self.name = name or fieldname


Facet = TermsFacet | RangeFacet | DateRangeFacet


class FacetManager:
    """Manages facet configuration for a Whoosh Schema.

    Auto-discovers facets from schema fields, then applies manual
    overrides. Manual overrides take precedence over auto-discovered
    facets when both exist for the same field.

    All facets returned by :meth:`get_facets` are real core facet instances
    usable as ``searcher.search(query, groupedby=...)`` arguments.

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

        Text-like fields map to :class:`TermsFacet` (a ``FieldFacet``),
        numeric fields to a core :class:`whoosh.sorting.RangeFacet` with a
        default bucket layout, and datetime fields to a core
        :class:`whoosh.sorting.DateRangeFacet` with yearly buckets.

        Args:
            field_name: The name of the field.
            field_type: The Whoosh field type instance.

        Returns:
            A core facet instance appropriate for the field type, or None
            if the field type is not facetable.
        """
        field_type_name = type(field_type).__name__

        if field_type_name in ("KEYWORD", "BOOLEAN", "ID", "TEXT"):
            return TermsFacet(field_name, limit=DEFAULT_TERMS_LIMIT)
        if field_type_name == "NUMERIC":
            return RangeFacet(
                field_name,
                DEFAULT_NUMERIC_START,
                DEFAULT_NUMERIC_END,
                DEFAULT_NUMERIC_GAP,
            )
        if field_type_name == "DATETIME":
            return DateRangeFacet(
                field_name,
                DEFAULT_DATE_START,
                DEFAULT_DATE_END,
                DEFAULT_DATE_GAP,
            )
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
        facet = self._create_facet_from_config(config, field_name)
        if facet is not None:
            self._facets[field_name] = facet

    def get_facets(self) -> dict[str, Facet]:
        """Return merged auto + manual facets.

        Returns:
            A dict mapping field names to core facet instances, with manual
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

    def _resolve_field_name(self, config: dict[str, Any], field_name: str | None) -> str:
        """Resolve the field name a facet config applies to.

        Args:
            config: Configuration dict, possibly containing a ``field`` key.
            field_name: Explicit field name, if known by the caller.

        Returns:
            The resolved field name; falls back to the first schema field,
            or an empty string for an empty schema.
        """
        candidate = field_name or config.get("field")
        if candidate:
            return str(candidate)
        names = list(self._schema.names())
        return names[0] if names else ""

    def _create_facet_from_config(
        self, config: dict[str, Any], field_name: str | None = None
    ) -> Facet | None:
        """Create a core facet instance from a config dict.

        Args:
            config: Configuration dict with a ``type`` key
                ("terms", "range", or "date_range") and type-specific
                parameters (``limit``, ``start``, ``end``, ``gap``, ``field``).
            field_name: Optional field name the facet applies to. When omitted,
                it is taken from ``config["field"]`` or the schema.

        Returns:
            A core facet instance, or None if the type is unrecognized.
        """
        facet_type = config.get("type", "terms")
        resolved = self._resolve_field_name(config, field_name)

        if facet_type == "terms":
            return TermsFacet(resolved, limit=config.get("limit", DEFAULT_TERMS_LIMIT))
        if facet_type == "range":
            return RangeFacet(
                resolved,
                config.get("start", DEFAULT_NUMERIC_START),
                config.get("end", DEFAULT_NUMERIC_END),
                config.get("gap", DEFAULT_NUMERIC_GAP),
            )
        if facet_type == "date_range":
            return DateRangeFacet(
                resolved,
                config.get("start", DEFAULT_DATE_START),
                config.get("end", DEFAULT_DATE_END),
                config.get("gap", DEFAULT_DATE_GAP),
            )
        return None
