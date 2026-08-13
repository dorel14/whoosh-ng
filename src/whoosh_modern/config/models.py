"""Pydantic models for Whoosh-NG configuration validation.

These models define the schema for ``whoosh-ng.yml`` / ``whoosh-ng.json``
configuration files, enabling validation, IDE support, and hierarchical merging.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from whoosh_modern.linguistics.detection.protocol import LanguageDetector


class FieldConfig(BaseModel):
    """Configuration for a single Whoosh field.

    Attributes:
        type: Whoosh field type (``"text"``, ``"keyword"``, ``"numeric"``,
            ``"datetime"``, ``"boolean"``, ``"id"``).
        language: Optional language code for stemming/stopwords
            (e.g. ``"en"``, ``"fr"``).
        stemming: Whether to apply stemming for this field.
        stopwords: Whether to filter stopwords for this field.
        synonyms: Whether to expand synonyms for this field.
        stored: Whether the field value should be stored in the index.
        sortable: Whether the field should be sortable in search results.
        faceted: Whether the field should be usable for faceted search.
        dictionary_stem_overrides: Optional mapping of word -> stemmed form
            to override the default Snowball stemmer.
    """

    type: str = "text"
    language: str | None = None
    stemming: bool = False
    stopwords: bool = False
    synonyms: bool = False
    stored: bool = True
    sortable: bool = False
    faceted: bool = False
    dictionary_stem_overrides: dict[str, str] = Field(default_factory=dict)

    def effective_language(self, detector: LanguageDetector | None = None) -> str | None:
        """Return the effective language for this field.

        If ``language`` is ``"auto"`` and a ``detector`` is provided, the
        detector is used to guess the language from the field name. If the
        language cannot be determined, ``None`` is returned and the caller
        should fall back to a default.

        Args:
            detector: Optional ``LanguageDetector`` instance used when
                ``language == "auto"``.

        Returns:
            The resolved language code, or ``None``.
        """
        if self.language == "auto":
            if detector is None:
                return None
            return detector.detect(self.type)
        return self.language


class FuzzyConfig(BaseModel):
    """Fuzzy search configuration.

    Attributes:
        enabled: Whether fuzzy search is enabled.
        distance: Maximum Levenshtein distance for fuzzy matching.
    """

    enabled: bool = False
    distance: int = 2


class RankingConfig(BaseModel):
    """Search ranking configuration.

    Attributes:
        title_boost: Boost factor for the title field.
    """

    title_boost: float = 1.0


class AIConfig(BaseModel):
    """AI/extension configuration.

    Attributes:
        enabled: Whether AI features are enabled.
    """

    enabled: bool = False


class SearchConfig(BaseModel):
    """Search behaviour configuration.

    Attributes:
        fuzzy: Fuzzy search settings.
        ranking: Ranking/boost settings.
        ai: AI feature flags.
    """

    fuzzy: FuzzyConfig = Field(default_factory=FuzzyConfig)
    ranking: RankingConfig = Field(default_factory=RankingConfig)
    ai: AIConfig = Field(default_factory=AIConfig)


class DataSourceConfigModel(BaseModel):
    """Data source configuration.

    Attributes:
        type: Data source type (``"sql"``, ``"rest"``, ``"csv"``, etc.).
        path: Filesystem path (for file-based sources).
        url: Endpoint URL (for REST/GraphQL sources).
        query: Query string (for SQL sources).
        connection: Database connection string or engine.
        incremental_field: Field used for incremental syncs.
        id_field: Unique identifier field.
        delimiter: CSV delimiter.
        encoding: File encoding.
        document_path: Dotted path to documents in API responses.
        method: HTTP method.
        headers: HTTP headers.
        pagination: Pagination strategy.
        page_size: Items per page.
        timeout: Request timeout in seconds.
    """

    type: str = "csv"
    path: str | None = None
    url: str | None = None
    query: str | None = None
    connection: str | None = None
    incremental_field: str | None = None
    id_field: str | None = None
    delimiter: str = ","
    encoding: str = "utf-8"
    document_path: str | None = None
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    pagination: str | None = None
    page_size: int = 100
    timeout: int = 30


class StorageConfigModel(BaseModel):
    """Storage backend configuration.

    Attributes:
        type: Storage type (``"file"``, ``"s3"``, ``"hybrid"``).
        path: Local filesystem path (for file/hybrid storage).
        bucket: S3 bucket name (for S3/hybrid storage).
        prefix: S3 key prefix.
    """

    type: str = "file"
    path: str | None = None
    bucket: str | None = None
    prefix: str = ""


class WhooshNGConfig(BaseModel):
    """Top-level Whoosh-NG application configuration.

    Attributes:
        index: Index name/path.
        languages: Language configuration.
        fields: Field definitions keyed by field name.
        search: Search behaviour configuration.
        data_source: Data source configuration.
        storage: Storage backend configuration.
        vector: Optional vector search configuration.
        embedding: Optional embedding provider configuration.
        language_detection: Optional language detection configuration.
    """

    index: str = "default"
    languages: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, FieldConfig] = Field(default_factory=dict)
    search: SearchConfig = Field(default_factory=SearchConfig)
    data_source: DataSourceConfigModel | None = None
    storage: StorageConfigModel = Field(default_factory=StorageConfigModel)
    vector: dict[str, Any] = Field(default_factory=dict)
    embedding: dict[str, Any] = Field(default_factory=dict)
    language_detection: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AIConfig",
    "DataSourceConfigModel",
    "FieldConfig",
    "FuzzyConfig",
    "RankingConfig",
    "SearchConfig",
    "StorageConfigModel",
    "WhooshNGConfig",
]
