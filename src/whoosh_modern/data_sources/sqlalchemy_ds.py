"""SQLAlchemy DataSource implementation (optional backend).

Author: dorel14
Version: 3.0.0
"""

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

    Args:
        engine: A SQLAlchemy ``Engine`` instance used to connect to the
            database.
        query: SQL ``SELECT`` statement whose results are iterated as
            documents.
        incremental_field: Optional column name for incremental syncs.
        id_field: Optional primary-key or unique-column name.
        schema: Optional pre-built Whoosh :class:`~whoosh.fields.Schema`.
            If ``None``, schema is discovered automatically.
        sample_size: Number of rows to inspect during schema discovery.
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
        """Return the data source name.

        Returns:
            A string in the form ``sqlalchemy:<query_prefix>``.
        """
        return f"sqlalchemy:{self.query[:50]}"

    def health_check(self) -> bool:
        """Return True if the database connection is healthy.

        Returns:
            ``True`` if a trivial ``SELECT 1`` succeeds, ``False``
            otherwise.
        """
        try:
            with self._engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            return True
        except Exception:
            return False

    def discover_schema(self) -> Schema:
        """Discover schema from query result metadata using SQLAlchemy.

        Executes the configured query with ``LIMIT 0``-equivalent
        introspection and uses the SQLAlchemy inspector to map column
        types to Whoosh field types.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from the
            query's result columns.

        Raises:
            DataSourceError: If ``query`` or ``engine`` is missing.
        """
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
        """Build Whoosh field types from SQLAlchemy column types.

        Args:
            inspector: A SQLAlchemy ``Inspector`` for the engine.
            dialect: The SQLAlchemy ``Dialect`` in use.
            columns: List of column names from the query result.

        Returns:
            A mapping of column names to Whoosh field instances
            (e.g. ``TEXT(stored=True)``).
        """
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
        """Extract table name from query (best effort).

        Parses the ``FROM`` clause of the configured query to guess
        the primary table name.

        Returns:
            The guessed table name, or ``"unknown"`` if it cannot be
            determined.
        """
        query_upper = self.query.upper()
        if "FROM" in query_upper:
            parts = query_upper.split("FROM")[1].strip()
            table = parts.split()[0].strip('`"[] ')
            return table
        return "unknown"

    def _map_sqlalchemy_type(self, col_type: Any, dialect: Any) -> Any:
        """Map SQLAlchemy type to Whoosh field.

        Delegates to the canonical
        :class:`whoosh_modern.models.base.TypeMapper`: the column's
        ``python_type`` is mapped when available, otherwise the SQL type name
        is mapped through :meth:`~whoosh_modern.models.base.TypeMapper.map_dtype`.

        Args:
            col_type: A SQLAlchemy column type instance.
            dialect: The SQLAlchemy ``Dialect`` in use.

        Returns:
            A Whoosh field instance matching the column type, or
            ``TEXT(stored=True)`` as a fallback.
        """
        from whoosh.fields import STORED, TEXT
        from whoosh_modern.models.base import TypeMapper
        from whoosh_modern.models.types import SearchOptions

        options = SearchOptions(stored=True)
        try:
            python_type = col_type.python_type
        except Exception:
            python_type = None

        if python_type is not None:
            mapped = TypeMapper.map(python_type, options)
            if mapped is not STORED:
                return mapped

        mapped = TypeMapper.map_dtype(type(col_type).__name__, options)
        return mapped if mapped is not None else TEXT(stored=True)

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the SQLAlchemy query.

        Executes the configured ``SELECT`` and yields each row as a
        dictionary of column-name → value.

        Yields:
            Document dictionaries from the query result.

        Raises:
            DataSourceError: If ``query`` or ``engine`` is missing.
        """
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
        """Yield documents changed since a timestamp using SQLAlchemy.

        Appends an ``AND <incremental_field> > :since`` (or ``WHERE``
        clause if none exists) to the base query to filter for recent
        changes.

        Args:
            since: A value (timestamp, ID, etc.) to compare against
                the ``incremental_field``.

        Yields:
            Document dictionaries whose ``incremental_field`` value
            is greater than ``since``.

        Raises:
            DataSourceError: If ``query`` or ``engine`` is missing.
        """
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
        """Return total document count using SQLAlchemy.

        Wraps the configured query in ``SELECT COUNT(*) FROM (...)``.

        Returns:
            The number of rows returned by the base query.

        Raises:
            DataSourceError: If ``query`` or ``engine`` is missing.
        """
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
        """Return metadata about this source.

        Returns:
            A dictionary with keys ``type``, ``query``,
            ``incremental_field``, ``id_field``, and ``dialect``.
        """
        return {
            "type": "sqlalchemy",
            "query": self.query,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
            "dialect": getattr(self._engine.dialect, "name", "unknown"),
        }
