"""DataSource configuration DSL and factory."""

from dataclasses import dataclass, field
from typing import Any

from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.data_sources.graphql import GraphQLSource
from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.data_sources.pydantic import PydanticSource
from whoosh_modern.data_sources.rest import RESTSource
from whoosh_modern.data_sources.sql import SQLSource


@dataclass
class DataSourceConfig:
    """Declarative configuration for a DataSource.

    Example:
        config = DataSourceConfig(
            type="csv",
            path="data/articles.csv",
            delimiter=",",
        )
        source = config.create()
    """

    type: str
    path: str | None = None
    url: str | None = None
    query: str | None = None
    connection: Any = None
    models: list[Any] = field(default_factory=list)
    model: Any = None
    dataframe: Any = None
    delimiter: str = ","
    encoding: str = "utf-8"
    document_path: str | None = None
    incremental_field: str | None = None
    id_field: str | None = None
    method: str = "GET"
    headers: dict[str, str] | None = None
    auth: Any | None = None
    pagination: str | None = None
    page_size: int = 100
    timeout: int = 30
    sample_size: int = 5
    engine: str = "auto"

    def create(self) -> Any:
        """Create a DataSource instance from this configuration.

        Returns:
            A DataSource instance.

        Raises:
            ValueError: If the configuration is invalid or unsupported.
        """
        source_type = self.type.lower()

        if source_type == "sql":
            if self.connection is None:
                raise ValueError("SQLSource requires a 'connection' parameter")
            if not self.query:
                raise ValueError("SQLSource requires a 'query' parameter")
            return SQLSource(
                connection=self.connection,
                query=self.query,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
            )

        if source_type == "rest":
            if not self.url:
                raise ValueError("RESTSource requires a 'url' parameter")
            return RESTSource(
                url=self.url,
                method=self.method,
                headers=self.headers,
                auth=self.auth,
                pagination=self.pagination,
                page_size=self.page_size,
                document_path=self.document_path,
                incremental_field=self.incremental_field,
                timeout=self.timeout,
            )

        if source_type == "csv":
            if not self.path:
                raise ValueError("CSVSource requires a 'path' parameter")
            return FastCSVSource(
                path=self.path,
                delimiter=self.delimiter,
                encoding=self.encoding,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        if source_type == "json":
            if not self.path:
                raise ValueError("JSONSource requires a 'path' parameter")
            return JSONSource(
                path=self.path,
                document_path=self.document_path,
                encoding=self.encoding,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        if source_type == "graphql":
            if not self.url:
                raise ValueError("GraphQLSource requires a 'url' parameter")
            if not self.query:
                raise ValueError("GraphQLSource requires a 'query' parameter")
            return GraphQLSource(
                url=self.url,
                query=self.query,
                document_path=self.document_path,
                headers=self.headers,
                auth=self.auth,
                timeout=self.timeout,
                sample_size=self.sample_size,
            )

        if source_type == "pydantic":
            if not self.models:
                raise ValueError("PydanticSource requires a 'models' list")
            return PydanticSource(
                models=self.models,
                model=self.model,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        if source_type == "sqlalchemy":
            if self.connection is None:
                raise ValueError("SQLAlchemySource requires an 'engine' parameter")
            try:
                from whoosh_modern.data_sources.sqlalchemy_ds import SQLAlchemySource
            except ImportError as e:
                raise ValueError(
                    "SQLAlchemySource requires sqlalchemy to be installed"
                ) from e
            return SQLAlchemySource(
                engine=self.connection,
                query=self.query or "",
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        if source_type == "pandas":
            if self.dataframe is None:
                raise ValueError("PandasSource requires a 'dataframe' parameter")
            try:
                from whoosh_modern.data_sources.pandas_ds import PandasSource
            except ImportError as e:
                raise ValueError(
                    "PandasSource requires pandas to be installed"
                ) from e
            return PandasSource(
                dataframe=self.dataframe,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        if source_type == "polars":
            if self.dataframe is None:
                raise ValueError("PolarsSource requires a 'dataframe' parameter")
            try:
                from whoosh_modern.data_sources.polars_ds import PolarsSource
            except ImportError as e:
                raise ValueError(
                    "PolarsSource requires polars to be installed"
                ) from e
            return PolarsSource(
                dataframe=self.dataframe,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        if source_type == "parquet":
            if not self.path:
                raise ValueError("ParquetSource requires a 'path' parameter")
            try:
                from whoosh_modern.data_sources.parquet_ds import ParquetSource
            except ImportError as e:
                raise ValueError(
                    "ParquetSource requires pyarrow, pandas, or polars to be installed"
                ) from e
            return ParquetSource(
                path=self.path,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
                engine=self.engine,
            )

        if source_type == "peewee":
            if self.model is None and not self.query:
                raise ValueError("PeeweeSource requires a 'model' or 'query' parameter")
            try:
                from whoosh_modern.data_sources.peewee_ds import PeeweeSource
            except ImportError as e:
                raise ValueError(
                    "PeeweeSource requires peewee to be installed"
                ) from e
            return PeeweeSource(
                model=self.model,
                query=self.query,
                database=self.connection,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        if source_type == "tortoise":
            if self.model is None:
                raise ValueError("TortoiseSource requires a 'model' parameter")
            try:
                from whoosh_modern.data_sources.tortoise_ds import TortoiseSource
            except ImportError as e:
                raise ValueError(
                    "TortoiseSource requires tortoise-orm to be installed"
                ) from e
            return TortoiseSource(
                model=self.model,
                incremental_field=self.incremental_field,
                id_field=self.id_field,
                sample_size=self.sample_size,
            )

        raise ValueError(
            f"Unsupported DataSource type: {source_type!r}. "
            f"Supported types: sql, sqlalchemy, rest, csv, json, graphql, pydantic, "
            f"pandas, polars, parquet, peewee, tortoise"
        )
