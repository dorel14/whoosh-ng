from __future__ import annotations

from whoosh_modern.application import FileStorage, SearchApplication
from whoosh_modern.autocomplete import FuzzySuggestProvider, NGramProvider, create_autocomplete
from whoosh_modern.data_sources import DataSource, ObservableDataSource
from whoosh_modern.data_sources.config import DataSourceConfig
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.data_sources.graphql import GraphQLSource
from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.data_sources.pandas_ds import PandasSource
from whoosh_modern.data_sources.parquet_ds import ParquetSource
from whoosh_modern.data_sources.peewee_ds import PeeweeSource
from whoosh_modern.data_sources.polars_ds import PolarsSource
from whoosh_modern.data_sources.pydantic import PydanticSource
from whoosh_modern.data_sources.rest import RESTSource
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.data_sources.sqlalchemy_ds import SQLAlchemySource
from whoosh_modern.data_sources.tortoise_ds import TortoiseSource
from whoosh_modern.exceptions import (
    DataSourceError,
    DocumentIterationError,
    SchemaDiscoveryError,
    ValidationError,
)
from whoosh_modern.facets import FacetManager
from whoosh_modern.indexing import (
    BatchAnalyzer,
    BatchIndexWriter,
    CompiledDataSource,
    LogMergePolicy,
    MergePolicy,
    ModernIndexBuilder,
    NoMergePolicy,
    ParallelIndexBuilder,
    TieredMergePolicy,
)
from whoosh_modern.linguistics import (
    LANG_SYNONYMS,
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    ItalianAnalyzer,
    JSONSynonymProvider,
    SpanishAnalyzer,
    SQLiteSynonymStore,
    StaticSynonymProvider,
    SynonymCompiler,
    SynonymExpansionMiddleware,
    SynonymManager,
    SynonymProvider,
    YAMLSynonymProvider,
)
from whoosh_modern.middleware import (
    AnalyzerMiddleware,
    CacheMiddleware,
    FileStorageProvider,
    LoggingMiddleware,
    MiddlewarePipeline,
    QueryRewriteMiddleware,
    RankingMiddleware,
    RetryMiddleware,
    S3StorageProvider,
    SearchMiddleware,
    SQLiteStorageProvider,
    StemmingMiddleware,
    StorageMiddleware,
    SynonymMiddleware,
)
from whoosh_modern.profiling import (
    AnalyzerCache,
    AnalyzerStepProfiler,
    AutoCacheAdvisor,
    BatchSizeOptimizer,
    CacheAnalyzer,
    CommitProfilerV2,
    FieldAnalyzerCache,
    FieldProfiler,
    IndexProfiler,
    MemoryProfiler,
    MetricsCollector,
    profile_commit,
)
from whoosh_modern.schema_discovery import SchemaDiscovery
from whoosh_modern.storage import (
    AsyncFileStorage,
    AsyncHybridStorage,
    HybridStorage,
    S3Storage,
)
from whoosh_modern.validation import ValidationFramework
from whoosh_modern.views import SearchView
from whoosh_modern.writer import ModernIndex, ModernIndexWriter

__all__ = [
    "SearchApplication",
    "FileStorage",
    "S3Storage",
    "HybridStorage",
    "AsyncHybridStorage",
    "AsyncFileStorage",
    "DataSource",
    "ObservableDataSource",
    "SQLSource",
    "SQLAlchemySource",
    "RESTSource",
    "FastCSVSource",
    "JSONSource",
    "GraphQLSource",
    "PydanticSource",
    "PandasSource",
    "PolarsSource",
    "ParquetSource",
    "PeeweeSource",
    "TortoiseSource",
    "DataSourceConfig",
    "FacetManager",
    "ValidationFramework",
    "SchemaDiscovery",
    "SearchView",
    "MiddlewarePipeline",
    "RetryMiddleware",
    "LoggingMiddleware",
    "CacheMiddleware",
    "StorageMiddleware",
    "FileStorageProvider",
    "SQLiteStorageProvider",
    "S3StorageProvider",
    "SearchMiddleware",
    "QueryRewriteMiddleware",
    "RankingMiddleware",
    "AnalyzerMiddleware",
    "StemmingMiddleware",
    "SynonymMiddleware",
    "SynonymProvider",
    "StaticSynonymProvider",
    "YAMLSynonymProvider",
    "JSONSynonymProvider",
    "SQLiteSynonymStore",
    "SynonymCompiler",
    "SynonymManager",
    "SynonymExpansionMiddleware",
    "LANG_SYNONYMS",
    "FrenchAnalyzer",
    "EnglishAnalyzer",
    "GermanAnalyzer",
    "SpanishAnalyzer",
    "ItalianAnalyzer",
    "FuzzySuggestProvider",
    "NGramProvider",
    "create_autocomplete",
    "DataSourceError",
    "SchemaDiscoveryError",
    "DocumentIterationError",
    "ValidationError",
    "ModernIndex",
    "ModernIndexWriter",
    "BatchIndexWriter",
    "BatchAnalyzer",
    "CompiledDataSource",
    "ModernIndexBuilder",
    "IndexProfiler",
    "MemoryProfiler",
    "MetricsCollector",
    "AnalyzerStepProfiler",
    "AutoCacheAdvisor",
    "BatchSizeOptimizer",
    "CacheAnalyzer",
    "CommitProfilerV2",
    "FieldProfiler",
    "AnalyzerCache",
    "FieldAnalyzerCache",
    "profile_commit",
    "MergePolicy",
    "NoMergePolicy",
    "LogMergePolicy",
    "TieredMergePolicy",
    "ParallelIndexBuilder",
]
