"""SQL DataSource implementation with GROUP BY, JOIN, incremental support,
and connection pooling."""

import asyncio
import logging
import re
from collections.abc import AsyncIterator, Iterator, Mapping
from datetime import datetime
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError, SchemaDiscoveryError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]

_SQL_KEYWORD_PATTERN = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE"
    r"|UNION|EXEC|EXECUTE|OR|AND|--|;)\b",
    re.IGNORECASE,
)


def _validate_identifier(name: str) -> None:
    """Validate that an identifier name is safe for SQL interpolation."""
    if not name:
        raise DataSourceError("Incremental field name cannot be empty")
    if '"' in name or " " in name or ";" in name or "'" in name:
        raise DataSourceError(
            f"Invalid incremental field name: {name!r}",
        )
    if _SQL_KEYWORD_PATTERN.search(name):
        raise DataSourceError(
            f"Incremental field name {name!r} contains SQL keywords",
        )


class _ConnectionPool:
    """Simple connection pool for SQLite or DB-API 2.0 connections."""

    def __init__(self, connection: Any, max_size: int = 5) -> None:
        self._connection = connection
        self._max_size = max_size
        self._available: list[Any] = [connection]

    def acquire(self) -> Any:
        """Acquire a connection from the pool."""
        if self._available:
            return self._available.pop()
        if hasattr(self._connection, "connect"):
            return self._connection.connect()
        return self._connection

    def release(self, connection: Any) -> None:
        """Release a connection back to the pool."""
        if len(self._available) < self._max_size:
            self._available.append(connection)

    def close_all(self) -> None:
        """Close all pooled connections."""
        while self._available:
            conn = self._available.pop()
            if hasattr(conn, "close"):
                conn.close()


class SQLSource:
    """SQL data source implementing the DataSource protocol."""

    def __init__(
        self,
        connection: Any,
        query: str,
        incremental_field: str | None = None,
        id_field: str | None = None,
        pool_size: int = 5,
    ) -> None:
        self.connection = connection
        self.query = query
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.pool_size = pool_size
        self.last_sync_value: Any = None
        self._schema: Schema | None = None
        self._pool: _ConnectionPool | None = None
        self._columns: list[str] | None = None
        self._compiled_mapper: Any = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"sql:{self.query[:50]}"

    def health_check(self) -> bool:
        """Return True if the database connection is healthy."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False

    def _get_connection(self) -> Any:
        """Get a connection, using the pool if available."""
        if self._pool is None:
            self._pool = _ConnectionPool(self.connection, max_size=self.pool_size)
        return self._pool.acquire()

    def _get_columns(self) -> list[str]:
        """Get column names from the query result, cached."""
        if self._columns is not None:
            return self._columns

        cursor = self.connection.cursor()
        cursor.execute(self.query)
        self._columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return self._columns

    def compile_mapper(self) -> Any:
        """Return a compiled document mapper for this source.

        Pre-computes column names for fast row-to-doc mapping.
        """
        if self._compiled_mapper is not None:
            return self._compiled_mapper

        columns = self._get_columns()

        def mapper(row: Any) -> dict[str, Any]:
            return dict(zip(columns, row, strict=True))

        self._compiled_mapper = mapper
        return self._compiled_mapper

    def discover_schema(self) -> Schema:
        """Discover schema from query result metadata."""
        schema_query = self.query.rstrip(";")
        if not schema_query.upper().endswith("LIMIT"):
            schema_query = self._append_limit_zero(schema_query)

        cursor = self.connection.cursor()
        cursor.execute(schema_query)
        columns = [(desc[0], desc[1]) for desc in cursor.description] if cursor.description else []

        seen_names: set[str] = set()
        for col_name, _ in columns:
            if col_name in seen_names:
                raise SchemaDiscoveryError(
                    f"Duplicate column name: {col_name}",
                    field=col_name,
                )
            seen_names.add(col_name)

        if self.incremental_field:
            column_names = {col_name for col_name, _ in columns}
            if self.incremental_field not in column_names:
                raise DataSourceError(
                    f"Incremental field {self.incremental_field!r} not found in query results",
                    field=self.incremental_field,
                )
            _validate_identifier(self.incremental_field)

        self._schema = SchemaDiscovery.from_result_set(columns)
        return self._schema

    @staticmethod
    def _append_limit_zero(query: str) -> str:
        """Append LIMIT 0 to a query for metadata-only introspection."""
        stripped = query.rstrip().rstrip(";").strip()
        return f"{stripped} LIMIT 0"

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the SQL query result."""
        cursor = self.connection.cursor()
        cursor.execute(self.query)
        columns = self._get_columns()

        for row in cursor:
            yield dict(zip(columns, row, strict=True))

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the SQL query result in batches.

        Uses fetchmany() for efficient batch reading from the database.
        """
        cursor = self.connection.cursor()
        cursor.execute(self.query)
        columns = self._get_columns()

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            yield [dict(zip(columns, row, strict=True)) for row in rows]

    def iter_changes(self, since: datetime) -> Iterator[Document]:
        """Yield documents changed since a timestamp."""
        if not self.incremental_field:
            return

        schema = self.discover_schema()
        field_names = {name for name, _ in schema.items()}
        if self.incremental_field not in field_names:
            raise DataSourceError(
                f"Incremental field {self.incremental_field!r} not found in schema",
                field=self.incremental_field,
            )
        _validate_identifier(self.incremental_field)

        cursor = self.connection.cursor()
        placeholder = "?"
        query = (
            f"{self.query} AND {self.incremental_field} > {placeholder}"
            if "WHERE" in self.query.upper()
            else f"{self.query} WHERE {self.incremental_field} > {placeholder}"
        )
        cursor.execute(query, (since,))
        columns = self._get_columns()

        for row in cursor:
            yield dict(zip(columns, row, strict=True))

    def document_count(self) -> int:
        """Return total document count."""
        _validate_query_is_select(self.query)
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM ({self.query})")
        result = cursor.fetchone()
        return result[0] if result else 0

    async def adiscover_schema(self) -> Schema:
        """Async equivalent of :meth:`discover_schema` via ``asyncio.to_thread``."""
        return await asyncio.to_thread(self.discover_schema)

    async def aiter_documents(self) -> AsyncIterator[Document]:
        """Async document streaming via ``asyncio.to_thread``."""
        for doc in await asyncio.to_thread(list, self.iter_documents()):
            yield doc

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this source."""
        return {
            "type": "sql",
            "query": self.query,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
            "pool_size": self.pool_size,
        }


def _validate_query_is_select(query: str) -> None:
    """Validate that a query is a SELECT statement before wrapping it."""
    stripped = query.strip().lstrip("(").strip()
    if not stripped.upper().startswith("SELECT"):
        raise DataSourceError(
            f"document_count() requires a SELECT query, got: {stripped[:50]!r}",
        )
