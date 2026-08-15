"""Engine for building a ``DataSource`` from ``WhooshNGConfig.data_source``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.config.models import WhooshNGConfig
from whoosh_modern.data_sources import DataSource
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.data_sources.parquet_ds import ParquetSource
from whoosh_modern.data_sources.rest import RESTSource
from whoosh_modern.data_sources.sql import SQLSource


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
