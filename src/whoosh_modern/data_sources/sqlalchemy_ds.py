"""SQLAlchemy DataSource implementation (optional backend)."""

import logging
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


class SQLAlchemySource:
    """SQLAlchemy-based data source implementing the DataSource protocol.

    Supports any SQLAlchemy dialect (PostgreSQL, MySQL, SQLite, Oracle, etc.)
    with proper type mapping and connection pooling via SQLAlchemy's pool.

    Uses the SQLAlchemy inspector and column types to infer the Whoosh
    schema directly, so ``SchemaDiscovery`` is not needed here.

    Example:
        from sqlalchemy import create_engine
        from whoosh_modern.data_sources.sqlalchemy_ds import SQLAlchemySource

        engine = create_engine("postgresql://user:pass@localhost/db")
        source = SQLAlchemySource(engine=engine, query="SELECT * FROM articles")
    """

    def __init__(
        self,
        engine: Any,
        query: str,
        incremental_field: str | None = None,
        id_field: str | None = None,
        schema: Schema | None = None,
        sample_size: int = 5,
    ) -> None:
        self._engine = engine
        self.query = query
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self._schema = schema
        self._last_sync_value: Any = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"sqlalchemy:{self.query[:50]}"

    def health_check(self) -> bool:
        """Return True if the database connection is healthy."""
        try:
            with self._engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            return True
        except Exception:
            return False

    def discover_schema(self) -> Schema:
        """Discover schema from query result metadata using SQLAlchemy."""
        from sqlalchemy import inspect, text

        if self._schema is not None:
            return self._schema

        if not self.query or self._engine is None:
            raise DataSourceError(
                "SQLAlchemySource requires a 'query' and 'engine' to discover schema",
                source="sqlalchemy",
            )

        with self._engine.connect() as conn:
            stmt = text(self.query)
            result = conn.execution_options(stream_results=True).execute(stmt)
            columns = list(result.keys())

        if not columns:
            from whoosh.fields import Schema

            return Schema()

        # Use SQLAlchemy inspector for type mapping when possible
        try:
            inspector = inspect(self._engine)
            dialect = self._engine.dialect
            type_map = self._build_type_map(inspector, dialect, columns)
        except Exception:
            type_map = {col: "TEXT" for col in columns}

        from whoosh.fields import Schema

        self._schema = Schema(**type_map)
        return self._schema

    def _build_type_map(self, inspector: Any, dialect: Any, columns: list[str]) -> dict[str, Any]:
        """Build Whoosh field types from SQLAlchemy column types."""
        type_map: dict[str, Any] = {}
        for col_name in columns:
            try:
                col_info = inspector.get_columns(self._get_table_name())
                col_type = next((c["type"] for c in col_info if c["name"] == col_name), None)
                if col_type is not None:
                    type_map[col_name] = self._map_sqlalchemy_type(col_type, dialect)
                else:
                    type_map[col_name] = "TEXT"
            except Exception:
                type_map[col_name] = "TEXT"
        return type_map

    def _get_table_name(self) -> str:
        """Extract table name from query (best effort)."""
        query_upper = self.query.upper()
        if "FROM" in query_upper:
            parts = query_upper.split("FROM")[1].strip()
            table = parts.split()[0].strip('`"[] ')
            return table
        return "unknown"

    def _map_sqlalchemy_type(self, col_type: Any, dialect: Any) -> Any:
        """Map SQLAlchemy type to Whoosh field."""
        from sqlalchemy import (
            BigInteger,
            Boolean,
            Date,
            DateTime,
            Float,
            Integer,
            String,
        )

        from whoosh.fields import BOOLEAN, DATETIME, NUMERIC, TEXT

        if isinstance(col_type, String):
            return TEXT(stored=True)
        if isinstance(col_type, Integer | BigInteger):
            return NUMERIC(int, stored=True)
        if isinstance(col_type, Float):
            return NUMERIC(float, stored=True)
        if isinstance(col_type, Boolean):
            return BOOLEAN(stored=True)
        if isinstance(col_type, Date | DateTime):
            return DATETIME(stored=True)

        return TEXT(stored=True)

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the SQLAlchemy query."""
        from sqlalchemy import text

        if self._engine is None or not self.query:
            raise DataSourceError(
                "SQLAlchemySource requires a 'query' and 'engine' to iterate documents",
                source="sqlalchemy",
            )

        with self._engine.connect() as conn:
            stmt = text(self.query)
            result = conn.execution_options(stream_results=True).execute(stmt)
            columns = list(result.keys())

            for row in result:
                doc: dict[str, Any] = dict(zip(columns, row, strict=True))
                yield doc

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp using SQLAlchemy."""
        from sqlalchemy import text

        if not self.incremental_field:
            return

        if self._engine is None or not self.query:
            raise DataSourceError(
                "SQLAlchemySource requires a 'query' and 'engine' to iterate changes",
                source="sqlalchemy",
            )

        query = (
            f"{self.query} AND {self.incremental_field} > :since"
            if "WHERE" in self.query.upper()
            else f"{self.query} WHERE {self.incremental_field} > :since"
        )

        with self._engine.connect() as conn:
            stmt = text(query)
            result = conn.execute(stmt, {"since": since})
            columns = list(result.keys())

            for row in result:
                doc: dict[str, Any] = dict(zip(columns, row, strict=True))
                yield doc

    def document_count(self) -> int:
        """Return total document count using SQLAlchemy."""
        from sqlalchemy import text

        if self._engine is None or not self.query:
            raise DataSourceError(
                "SQLAlchemySource requires a 'query' and 'engine' to count documents",
                source="sqlalchemy",
            )

        count_query = f"SELECT COUNT(*) FROM ({self.query}) AS count_query"
        with self._engine.connect() as conn:
            stmt = text(count_query)
            result = conn.execute(stmt)
            row = result.fetchone()
            return row[0] if row else 0

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this source."""
        return {
            "type": "sqlalchemy",
            "query": self.query,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
            "dialect": getattr(self._engine.dialect, "name", "unknown"),
        }
