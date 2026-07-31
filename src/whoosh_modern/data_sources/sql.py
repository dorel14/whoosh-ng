"""SQL DataSource implementation with GROUP BY, JOIN, and incremental support."""

import logging
import re
from collections.abc import Iterator, Mapping
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
    """Validate that an identifier name is safe for SQL interpolation.

    Args:
        name: The identifier to validate.

    Raises:
        DataSourceError: If the name contains SQL keywords, semicolons,
            or whitespace.
    """
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


class SQLSource:
    """SQL data source implementing the DataSource protocol."""

    def __init__(
        self,
        connection: Any,
        query: str,
        incremental_field: str | None = None,
        id_field: str | None = None,
    ) -> None:
        self.connection = connection
        self.query = query
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.last_sync_value: Any = None
        self._schema: Schema | None = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"sql:{self.query[:50]}"

    def discover_schema(self) -> Schema:
        """Discover schema from query result metadata."""
        schema_query = self.query.rstrip(";")
        if not schema_query.upper().endswith("LIMIT"):
            schema_query = self._append_limit_zero(schema_query)

        cursor = self.connection.cursor()
        cursor.execute(schema_query)
        columns = [(desc[0], desc[1]) for desc in cursor.description] if cursor.description else []

        # Check for duplicate column names
        seen_names: set[str] = set()
        for col_name, _ in columns:
            if col_name in seen_names:
                raise SchemaDiscoveryError(
                    f"Duplicate column name: {col_name}",
                    field=col_name,
                )
            seen_names.add(col_name)

        # Validate incremental_field against discovered columns
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
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        for row in cursor:
            doc: dict[str, Any] = {}
            for col_name, value in zip(columns, row, strict=True):
                doc[col_name] = value
            yield doc

    def iter_changes(self, since: datetime) -> Iterator[Document]:
        """Yield documents changed since a timestamp."""
        if not self.incremental_field:
            return

        # Validate the incremental_field against discovered schema
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
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        for row in cursor:
            doc: dict[str, Any] = {}
            for col_name, value in zip(columns, row, strict=True):
                doc[col_name] = value
            yield doc

    def document_count(self) -> int:
        """Return total document count."""
        _validate_query_is_select(self.query)
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM ({self.query})")
        result = cursor.fetchone()
        return result[0] if result else 0

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this source."""
        return {
            "type": "sql",
            "query": self.query,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }


def _validate_query_is_select(query: str) -> None:
    """Validate that a query is a SELECT statement before wrapping it.

    Args:
        query: The SQL query to validate.

    Raises:
        DataSourceError: If the query is not a SELECT statement.
    """
    stripped = query.strip().lstrip("(").strip()
    if not stripped.upper().startswith("SELECT"):
        raise DataSourceError(
            f"document_count() requires a SELECT query, got: {stripped[:50]!r}",
        )
