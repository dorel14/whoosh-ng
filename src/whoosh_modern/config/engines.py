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

from whoosh.analysis import StandardAnalyzer
from whoosh.fields import (
    BOOLEAN,
    DATETIME,
    ID,
    KEYWORD,
    NUMERIC,
    TEXT,
    Schema,
)
from whoosh.plugins.manager import PluginManager
from whoosh_modern.config.models import WhooshNGConfig
from whoosh_modern.data_sources import DataSource
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.data_sources.parquet_ds import ParquetSource
from whoosh_modern.data_sources.rest import RESTSource
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.facets import FacetManager
from whoosh_modern.storage import FileStorage, HybridStorage


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

    def build(self) -> DataSource | None:
        """Build a DataSource from the configured data source.

        Returns:
            A DataSource instance, or ``None`` if no data source is configured.
        """
        ds_config = self._config.data_source
        if ds_config is None:
            return None
        return self._build_data_source(ds_config)

    def _build_data_source(self, ds_config: Any) -> DataSource:
        """Build a concrete DataSource from a DataSourceConfigModel.

        Args:
            ds_config: Data source configuration model.

        Returns:
            A DataSource instance.

        Raises:
            ValueError: If the configuration is invalid for the chosen source type.
        """
        source_type = ds_config.type.lower()
        if source_type == "csv":
            path = ds_config.path
            if not path:
                raise ValueError("CSV data source requires a non-empty 'path'")
            return FastCSVSource(
                path=path,
                delimiter=ds_config.delimiter,
                encoding=ds_config.encoding,
            )
        if source_type == "json":
            path = ds_config.path
            if not path:
                raise ValueError("JSON data source requires a non-empty 'path'")
            return JSONSource(path=path)
        if source_type == "sql":
            connection = ds_config.connection
            query = ds_config.query
            if not connection:
                raise ValueError("SQL data source requires a non-empty 'connection'")
            if not query:
                raise ValueError("SQL data source requires a non-empty 'query'")
            return SQLSource(
                connection=connection,
                query=query,
            )
        if source_type == "rest":
            url = ds_config.url
            if not url:
                raise ValueError("REST data source requires a non-empty 'url'")
            return RESTSource(
                url=url,
                method=ds_config.method,
                headers=ds_config.headers or None,
            )
        if source_type == "pandas":
            raise ValueError("Pandas data source requires an explicit dataframe configuration")
        if source_type == "parquet":
            path = ds_config.path
            if not path:
                raise ValueError("Parquet data source requires a non-empty 'path'")
            return ParquetSource(path=path)
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

        Raises:
            ValueError: If the storage configuration is invalid.
        """
        storage_config = self._config.storage
        storage_type = storage_config.type.lower()
        if storage_type == "file":
            path = storage_config.path or "./index"
            return FileStorage(path)
        if storage_type == "s3":
            try:
                from whoosh_modern.storage import S3Storage
            except ImportError as exc:
                raise ImportError(
                    "S3 storage requires boto3. Install with: pip install whoosh-ng[s3]"
                ) from exc
            bucket = storage_config.bucket
            if not bucket:
                raise ValueError("S3 storage requires a non-empty 'bucket'")
            return S3Storage(
                bucket=bucket,
                prefix=storage_config.prefix,
            )
        if storage_type == "hybrid":
            try:
                from whoosh_modern.storage import S3Storage
            except ImportError as exc:
                raise ImportError(
                    "Hybrid storage requires boto3. Install with: pip install whoosh-ng[s3]"
                ) from exc
            bucket = storage_config.bucket
            if not bucket:
                raise ValueError("Hybrid storage requires a non-empty 'bucket'")
            local_cache = storage_config.path or "./cache"
            remote = S3Storage(
                bucket=bucket,
                prefix=storage_config.prefix,
            )
            return HybridStorage(local_cache=local_cache, remote=remote)
        raise ValueError(f"Unsupported storage type: {storage_type}")


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


class VectorEngine:
    """Build a ``VectorProvider`` from ``WhooshNGConfig.vector``.

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
        """Build a VectorProvider from the configured vector settings.

        Returns:
            A VectorProvider instance, or ``None`` if no vector configuration
            is provided.
        """
        vector_config = self._config.vector
        if not vector_config:
            return None
        provider_type = vector_config.get("provider", "numpy").lower()
        if provider_type == "numpy":
            try:
                from whoosh_modern.vector.numpy_provider import NumpyProvider

                return NumpyProvider()
            except ImportError as exc:
                raise ImportError(
                    "NumpyProvider requires numpy. Install with: pip install numpy"
                ) from exc
        if provider_type == "hnswlib":
            try:
                from whoosh_modern.vector.hnswlib_provider import HnswlibProvider

                return HnswlibProvider(
                    dimension=int(vector_config.get("dimension", 384)),
                    space=vector_config.get("space", "l2"),
                    max_elements=int(vector_config.get("max_elements", 10000)),
                    ef_construction=int(vector_config.get("ef_construction", 200)),
                    m=int(vector_config.get("m", 16)),
                )
            except ImportError as exc:
                raise ImportError(
                    "HnswlibProvider requires hnswlib. "
                    "Install with: pip install whoosh-ng[hnsw]"
                ) from exc
        raise ValueError(f"Unsupported vector provider: {provider_type}")


class EmbeddingEngine:
    """Build an ``EmbeddingProvider`` from ``WhooshNGConfig.embedding``.

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
        """Build an EmbeddingProvider from the configured embedding settings.

        Returns:
            An EmbeddingProvider instance, or ``None`` if no embedding
            configuration is provided.
        """
        embedding_config = self._config.embedding
        if not embedding_config:
            return None
        provider_type = embedding_config.get("provider", "sentence-transformers").lower()
        if provider_type == "sentence-transformers":
            try:
                from whoosh_modern.embeddings.sentence_transformers_provider import (
                    SentenceTransformersProvider,
                )

                return SentenceTransformersProvider(
                    model_name=embedding_config.get("model_name", "all-MiniLM-L6-v2")
                )
            except ImportError as exc:
                raise ImportError(
                    "SentenceTransformersProvider requires sentence-transformers. "
                    "Install with: pip install whoosh-ng[embeddings]"
                ) from exc
        raise ValueError(f"Unsupported embedding provider: {provider_type}")


class LanguageEngine:
    """Build a ``LanguageDetector`` from ``WhooshNGConfig.language_detection``.

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
        """Build a LanguageDetector from the configured language detection settings.

        Returns:
            A LanguageDetector instance, or ``None`` if no language detection
            configuration is provided.
        """
        detection_config = self._config.language_detection
        if not detection_config:
            return None
        detector_type = detection_config.get("provider", "stopword").lower()
        if detector_type == "stopword":
            supported = detection_config.get("supported_languages", ["fr", "en", "de", "es", "it"])
            from whoosh_modern.linguistics.detection.stopword_detector import StopwordDetector

            return StopwordDetector(supported_languages=list(supported))
        if detector_type == "langdetect":
            try:
                from whoosh_modern.linguistics.detection.langdetect_provider import (
                    LangDetectProvider,
                )

                return LangDetectProvider()
            except ImportError as exc:
                raise ImportError(
                    "LangDetectProvider requires langdetect. "
                    "Install with: pip install whoosh-ng[language-detection]"
                ) from exc
        raise ValueError(f"Unsupported language detector: {detector_type}")


__all__ = [
    "AnalyzerEngine",
    "APIEngine",
    "DataSourceEngine",
    "EmbeddingEngine",
    "FacetEngine",
    "LanguageEngine",
    "PluginEngine",
    "SchemaEngine",
    "SearchModelEngine",
    "StorageEngine",
    "VectorEngine",
]
