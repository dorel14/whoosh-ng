"""Tests for FacetManager."""

import pytest

from whoosh.fields import BOOLEAN, DATETIME, KEYWORD, NUMERIC, TEXT, Schema
from whoosh_modern.facets import (
    DateRangeFacet,
    FacetManager,
    RangeFacet,
    TermsFacet,
)


class TestFacetManager:
    def test_auto_discover_terms_facet(self):
        schema = Schema(category=KEYWORD(), active=BOOLEAN())
        manager = FacetManager(schema)
        facets = manager.get_facets()
        assert "category" in facets
        assert isinstance(facets["category"], TermsFacet)

    def test_auto_discover_range_facet(self):
        schema = Schema(price=NUMERIC())
        manager = FacetManager(schema)
        facets = manager.get_facets()
        assert "price" in facets
        assert isinstance(facets["price"], RangeFacet)

    def test_auto_discover_date_range_facet(self):
        schema = Schema(release_date=DATETIME())
        manager = FacetManager(schema)
        facets = manager.get_facets()
        assert "release_date" in facets
        assert isinstance(facets["release_date"], DateRangeFacet)

    def test_auto_discover_text_as_terms(self):
        schema = Schema(title=TEXT())
        manager = FacetManager(schema)
        facets = manager.get_facets()
        assert "title" in facets
        assert isinstance(facets["title"], TermsFacet)

    def test_manual_override(self):
        schema = Schema(price=NUMERIC())
        manager = FacetManager(schema)
        manager.set_manual_override("price", {"type": "range", "buckets": ["0-10", "10-25"]})
        facets = manager.get_facets()
        assert "price" in facets
        assert isinstance(facets["price"], RangeFacet)

    def test_manual_override_takes_precedence(self):
        schema = Schema(price=NUMERIC())
        manager = FacetManager(schema)
        # Auto-discovered as RangeFacet
        assert isinstance(manager.get_facets()["price"], RangeFacet)
        # Manual override with custom buckets
        manager.set_manual_override(
            "price", {"type": "range", "buckets": ["0-10", "10-25", "25-100"]}
        )
        facets = manager.get_facets()
        assert "price" in facets

    def test_force_override(self):
        schema = Schema(title=TEXT())
        manager = FacetManager(schema)
        manager.set_manual_override("title", {"type": "terms", "limit": 50}, force=True)
        facets = manager.get_facets()
        assert "title" in facets

    def test_is_facetable(self, capsys):
        schema = Schema(category=KEYWORD(), price=NUMERIC())
        manager = FacetManager(schema)
        assert manager.is_facetable("category") is True
        assert manager.is_facetable("price") is True
        assert manager.is_facetable("nonexistent") is False

    def test_get_facet_config(self):
        schema = Schema(price=NUMERIC())
        manager = FacetManager(schema)
        assert manager.get_facet_config("price") is None
        manager.set_manual_override("price", {"type": "range", "buckets": ["0-10"]})
        config = manager.get_facet_config("price")
        assert config is not None
        assert config["type"] == "range"

    def test_get_all_facet_configs(self):
        schema = Schema(price=NUMERIC(), category=KEYWORD())
        manager = FacetManager(schema)
        manager.set_manual_override("price", {"type": "range", "buckets": ["0-10"]})
        configs = manager.get_all_facet_configs()
        assert "price" in configs

    def test_facet_stats(self):
        schema = Schema(
            title=TEXT(),
            price=NUMERIC(),
            category=KEYWORD(),
            created=DATETIME(),
        )
        manager = FacetManager(schema)
        stats = manager.get_facet_stats()
        assert stats["total_fields"] == 4
        assert stats["auto_discovered_facets"] > 0
        assert "facet_fields" in stats

    def test_empty_schema(self):
        schema = Schema()
        manager = FacetManager(schema)
        facets = manager.get_facets()
        assert facets == {}
        stats = manager.get_facet_stats()
        assert stats["total_fields"] == 0

    def test_set_manual_override_creates_terms(self):
        schema = Schema(category=TEXT())
        manager = FacetManager(schema)
        manager.set_manual_override("category", {"type": "terms", "limit": 50})
        facets = manager.get_facets()
        assert isinstance(facets["category"], TermsFacet)
        assert facets["category"].limit == 50

    def test_set_manual_override_creates_range(self):
        schema = Schema(price=NUMERIC())
        manager = FacetManager(schema)
        manager.set_manual_override("price", {"type": "range", "buckets": ["0-10", "10-25"]})
        facets = manager.get_facets()
        assert isinstance(facets["price"], RangeFacet)

    def test_set_manual_override_creates_date_range(self):
        schema = Schema(release_date=DATETIME())
        manager = FacetManager(schema)
        manager.set_manual_override("release_date", {"type": "date_range", "buckets": ["year"]})
        facets = manager.get_facets()
        assert isinstance(facets["release_date"], DateRangeFacet)
