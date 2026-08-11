"""Specialized engines for the Whoosh-NG configuration system.

Each engine turns a merged :class:`WhooshNGConfig` into a concrete Whoosh-NG
component:

- :class:`SchemaEngine` — Whoosh ``Schema`` from ``fields``
- :class:`AnalyzerEngine` — analyzer mapping from ``fields``
- :class:`DataSourceEngine` — ``DataSource`` instance from ``data_source``
- :class:`StorageEngine` — ``SyncStorageProvider`` from ``storage``
- :class:`SearchModelEngine` — search-model mapping from ``fields``
- :class:`FacetEngine` — ``FacetManager`` from faceted fields
- :class:`PluginEngine` — ``PluginManager`` from plugin config
- :class:`APIEngine` — FastAPI app from search config

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.fields import Schema
from whoosh_modern.config.models import WhooshNGConfig
from whoosh_modern.facets import FacetManager
from whoosh_modern.storage import FileStorage, HybridStorage, S3Storage


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
        from whoosh.fields import (
            BOOLEAN,
            DATETIME,
            ID,
            KEYWORD,
            NUMERIC,
            TEXT,
            Schema,
        )

        fields: dict[str, Any] = {}
        for name, field_config in self._config.fields.items():
            field_type = field_config.type.lower()
            if field_type == "text":
                fields[name] = TEXT(stored=field_config.stored, sortable=field_config.sortable)
            elif field_type == "keyword":
                fields[name] = KEYWORD(stored=field_config.stored, sortable=field_config.sortable)
            elif field_type == "numeric":
                fields[name] = NUMERIC(stored=field_config.stored, sortable=field_config.sortable)
            elif field_type == "datetime":
                fields[name] = DATETIME(stored=field_config.stored, sortable=field_config.sortable)
            elif field_type == "boolean":
                fields[name] = BOOLEAN(stored=field_config.stored, sortable=field_config.sortable)
            elif field_type == "id":
                fields[name] = ID(stored=field_config.stored, sortable=field_config.sortable)
            else:
                fields[name] = TEXT(stored=field_config.stored, sortable=field_config.sortable)
        return Schema(**fields)


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
        try:
            from whoosh.analysis import StandardAnalyzer

            return StandardAnalyzer(stoplist=field_config.stopwords)  # type: ignore[no-untyped-call]
        except ImportError:
            return None


class DataSourceEngine:
    """Build a ``DataSource`` from ``WhooshNGConfig.data_source``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any | None:
        """Build a DataSource from the configured data source.

        Returns:
            A DataSource instance, or ``None`` if no data source is configured.
        """
        ds_config = self._config.data_source
        if ds_config is None:
            return None
        return self._build_data_source(ds_config)

    def _build_data_source(self, ds_config: Any) -> Any:
        """Build a concrete DataSource from a DataSourceConfigModel.

        Args:
            ds_config: Data source configuration model.

        Returns:
            A DataSource instance.
        """
        source_type = ds_config.type.lower()
        if source_type == "csv":
            from whoosh_modern.data_sources.fast_csv import FastCSVSource

            return FastCSVSource(
                path=ds_config.path or "",
                delimiter=ds_config.delimiter,
                encoding=ds_config.encoding,
            )
        if source_type == "json":
            from whoosh_modern.data_sources.json import JSONSource

            return JSONSource(path=ds_config.path or "")
        if source_type == "sql":
            from whoosh_modern.data_sources.sql import SQLSource

            return SQLSource(
                connection=ds_config.connection or "",
                query=ds_config.query or "",
            )
        if source_type == "rest":
            from whoosh_modern.data_sources.rest import RESTSource

            return RESTSource(
                url=ds_config.url or "",
                method=ds_config.method,
                headers=ds_config.headers or None,
            )
        if source_type == "pandas":
            from whoosh_modern.data_sources.pandas_ds import PandasSource

            return PandasSource(dataframe=None)
        if source_type == "parquet":
            from whoosh_modern.data_sources.parquet_ds import ParquetSource

            return ParquetSource(path=ds_config.path or "")
        raise ValueError(f"Unsupported data source type: {source_type}")


class StorageEngine:
    """Build a ``SyncStorageProvider`` from ``WhooshNGConfig.storage``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any:
        """Build a SyncStorageProvider from the configured storage backend.

        Returns:
            A SyncStorageProvider instance.
        """
        storage_config = self._config.storage
        storage_type = storage_config.type.lower()
        if storage_type == "file":
            path = storage_config.path or "./index"
            return FileStorage(path)
        if storage_type == "s3":
            from whoosh_modern.storage import S3Storage

            return S3Storage(
                bucket=storage_config.bucket or "",
                prefix=storage_config.prefix,
            )
        if storage_type == "hybrid":
            from whoosh_modern.storage import S3Storage

            local_cache = storage_config.path or "./cache"
            remote = S3Storage(
                bucket=storage_config.bucket or "",
                prefix=storage_config.prefix,
            )
            return HybridStorage(local_cache=local_cache, remote=remote)
        return FileStorage("./index")


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


class FacetEngine:
    """Build a ``FacetManager`` from faceted ``WhooshNGConfig.fields``.

    Attributes:
        _config: The merged application configuration.
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


class PluginEngine:
    """Build a ``PluginManager`` from plugin configuration.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any:
        """Build a PluginManager from the configured plugins.

        Returns:
            A PluginManager instance, or ``None`` if the plugin system is not available.
        """
        try:
            from whoosh.plugins.manager import PluginManager

            return PluginManager()
        except ImportError:
            return None


class APIEngine:
    """Build a FastAPI application from ``WhooshNGConfig``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self, index: Any) -> Any:
        """Build a FastAPI application from the configured search settings.

        Args:
            index: An open Whoosh Index instance.

        Returns:
            A FastAPI application instance.
        """
        try:
            from whoosh_fastapi import create_app
        except ImportError as exc:
            raise ImportError(
                "FastAPI plugin requires fastapi. Install with: pip install whoosh-ng[api]"
            ) from exc
        return create_app(index, prefix="/api/v1")


__all__ = [
    "AnalyzerEngine",
    "APIEngine",
    "DataSourceEngine",
    "FacetEngine",
    "PluginEngine",
    "SchemaEngine",
    "SearchModelEngine",
    "StorageEngine",
]
