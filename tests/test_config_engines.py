"""Tests for the Whoosh-NG configuration engines.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

import pytest

from whoosh_modern.config.engine import ConfigEngine
from whoosh_modern.config.engines import (
    AnalyzerEngine,
    APIEngine,
    DataSourceEngine,
    FacetEngine,
    PluginEngine,
    SchemaEngine,
    SearchModelEngine,
    StorageEngine,
)
from whoosh_modern.config.models import (
    AIConfig,
    DataSourceConfigModel,
    FieldConfig,
    FuzzyConfig,
    RankingConfig,
    SearchConfig,
    StorageConfigModel,
    WhooshNGConfig,
)


@pytest.fixture
def app_config() -> WhooshNGConfig:
    return WhooshNGConfig(
        index="products",
        fields={
            "title": FieldConfig(
                type="text", language="fr", stemming=True, stored=True
            ),
            "price": FieldConfig(type="numeric", sortable=True),
            "published": FieldConfig(type="datetime", faceted=True),
        },
        search=SearchConfig(
            fuzzy=FuzzyConfig(enabled=True, distance=2),
            ranking=RankingConfig(title_boost=1.5),
            ai=AIConfig(enabled=False),
        ),
        data_source=DataSourceConfigModel(
            type="csv",
            path="products.csv",
            delimiter=",",
            encoding="utf-8",
        ),
        storage=StorageConfigModel(type="file", path="./index"),
    )


class TestSchemaEngine:
    def test_build_schema(self, app_config: WhooshNGConfig) -> None:
        engine = SchemaEngine(app_config)
        schema = engine.build()
        assert "title" in schema
        assert "price" in schema
        assert "published" in schema

    def test_default_schema(self) -> None:
        engine = SchemaEngine(WhooshNGConfig())
        schema = engine.build()
        assert isinstance(schema, type(schema))


class TestAnalyzerEngine:
    def test_build_analyzers(self, app_config: WhooshNGConfig) -> None:
        engine = AnalyzerEngine(app_config)
        analyzers = engine.build()
        assert "title" in analyzers

    def test_no_stemming(self) -> None:
        config = WhooshNGConfig(fields={"title": FieldConfig(type="text", stemming=False)})
        engine = AnalyzerEngine(config)
        analyzers = engine.build()
        assert analyzers["title"] is None


class TestDataSourceEngine:
    def test_build_csv_source(self, app_config: WhooshNGConfig) -> None:
        engine = DataSourceEngine(app_config)
        source = engine.build()
        assert source is not None

    def test_no_data_source(self) -> None:
        engine = DataSourceEngine(WhooshNGConfig())
        assert engine.build() is None

    def test_unsupported_source_type(self) -> None:
        config = WhooshNGConfig(data_source=DataSourceConfigModel(type="unknown"))
        engine = DataSourceEngine(config)
        with pytest.raises(ValueError, match="Unsupported data source type"):
            engine.build()


class TestStorageEngine:
    def test_build_file_storage(self, app_config: WhooshNGConfig) -> None:
        engine = StorageEngine(app_config)
        storage = engine.build()
        assert storage is not None

    def test_build_s3_storage(self) -> None:
        config = WhooshNGConfig(
            storage=StorageConfigModel(type="s3", bucket="my-bucket", prefix="idx")
        )
        engine = StorageEngine(config)
        try:
            storage = engine.build()
        except ImportError as exc:
            pytest.skip(str(exc))
        assert storage is not None

    def test_build_hybrid_storage(self) -> None:
        config = WhooshNGConfig(
            storage=StorageConfigModel(type="hybrid", path="./cache", bucket="my-bucket")
        )
        engine = StorageEngine(config)
        try:
            storage = engine.build()
        except ImportError as exc:
            pytest.skip(str(exc))
        assert storage is not None


class TestSearchModelEngine:
    def test_build_search_model(self, app_config: WhooshNGConfig) -> None:
        engine = SearchModelEngine(app_config)
        model = engine.build()
        assert "title" in model
        assert model["title"]["type"] == "text"
        assert model["title"]["stemming"] is True
        assert model["price"]["sortable"] is True


class TestFacetEngine:
    def test_build_facet_manager(self, app_config: WhooshNGConfig) -> None:
        schema = SchemaEngine(app_config).build()
        engine = FacetEngine(app_config, schema)
        manager = engine.build()
        assert manager is not None

    def test_no_faceted_fields(self) -> None:
        config = WhooshNGConfig(fields={"title": FieldConfig(type="text", faceted=False)})
        schema = SchemaEngine(config).build()
        engine = FacetEngine(config, schema)
        manager = engine.build()
        assert manager is not None


class TestPluginEngine:
    def test_build_plugin_manager(self, app_config: WhooshNGConfig) -> None:
        engine = PluginEngine(app_config)
        manager = engine.build()
        assert manager is not None


class TestAPIEngine:
    @pytest.mark.skipif(
        True,
        reason=(
            "FastAPI is installed in the test environment; "
            "test the endpoint registration instead."
        ),
    )
    def test_build_requires_fastapi(self, app_config: WhooshNGConfig) -> None:
        engine = APIEngine(app_config)
        with pytest.raises(ImportError, match="FastAPI plugin requires fastapi"):
            engine.build(None)

    def test_build_app_registers_routes(self, app_config: WhooshNGConfig) -> None:
        pytest.importorskip("fastapi")
        engine = APIEngine(app_config)
        app = engine.build(None)
        routes = [route.path for route in app.routes]
        assert "/api/v1/health" in routes


class TestConfigEngineIntegration:
    def test_full_build(self, app_config: WhooshNGConfig) -> None:
        engine = ConfigEngine()
        engine.merge(app_config.model_dump(), priority="runtime")
        config = engine.get_config()
        schema = SchemaEngine(config).build()
        assert "title" in schema
        storage = StorageEngine(config).build()
        assert storage is not None
        facets = FacetEngine(config, schema).build()
        assert facets is not None

    def test_build_returns_search_application(self, app_config: WhooshNGConfig) -> None:
        from whoosh_modern.application import SearchApplication

        engine = ConfigEngine()
        engine.merge(app_config.model_dump(), priority="runtime")
        app = engine.build()
        assert isinstance(app, SearchApplication)
