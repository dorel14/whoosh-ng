"""Schema discovery logic for result sets from various data sources.

``SchemaDiscovery`` is used by data sources that consume **raw/untyped**
records (JSON, CSV, REST, GraphQL, Pydantic models, SQL result sets).
It infers a Whoosh ``Schema`` from actual data values or DB metadata.

Data sources backed by **strongly-typed systems** (Pandas, Polars,
PyArrow, SQLAlchemy, Peewee, Tortoise ORM) implement their own
``discover_schema()`` directly from the native type system and do not
need ``SchemaDiscovery``.
"""

from collections import Counter
from collections.abc import Sequence
from typing import Any

from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, TEXT, Schema
from whoosh_modern.exceptions import SchemaDiscoveryError


class SchemaDiscovery:
    """Infers Whoosh Schema from data source results."""

    SQL_TYPE_MAP: dict[str, type] = {
        "VARCHAR": TEXT,
        "TEXT": TEXT,
        "CHAR": TEXT,
        "INTEGER": NUMERIC,
        "BIGINT": NUMERIC,
        "SMALLINT": NUMERIC,
        "FLOAT": NUMERIC,
        "DOUBLE": NUMERIC,
        "DECIMAL": NUMERIC,
        "BOOLEAN": BOOLEAN,
        "DATE": DATETIME,
        "TIMESTAMP": DATETIME,
        "UUID": ID,
        "JSON": KEYWORD,
        "ENUM": KEYWORD,
        "COUNT": NUMERIC,
        "SUM": NUMERIC,
        "AVG": NUMERIC,
        "MIN": NUMERIC,
        "MAX": NUMERIC,
        "STRING_AGG": TEXT,
    }

    @staticmethod
    def from_result_set(columns: Sequence[Sequence[str]]) -> Schema:
        """Infer Schema from column name/type tuples.

        Args:
            columns: List of (column_name, sql_type) tuples or lists.

        Returns:
            Whoosh Schema with fields inferred from column types.

        Raises:
            SchemaDiscoveryError: If duplicate column names are found.
        """
        fields: dict[str, Any] = {}
        seen: set[str] = set()

        for col in columns:
            col_name = col[0]
            sql_type = col[1]
            if col_name in seen:
                raise SchemaDiscoveryError(
                    f"Duplicate column name: {col_name}",
                    field=col_name,
                )
            seen.add(col_name)

            whoosh_field = SchemaDiscovery._map_type(sql_type)
            fields[col_name] = whoosh_field

        return Schema(**fields)

    @staticmethod
    def from_sample(documents: Sequence[Any], sample_size: int = 5) -> Schema:
        """Infer Schema from sample documents.

        Samples multiple documents and takes the majority type
        for each field to avoid outliers skewing the schema.

        Args:
            documents: List of document mappings to infer types from.
            sample_size: Number of documents to sample for type inference.

        Returns:
            Whoosh Schema with fields inferred from document values.
        """
        if not documents:
            return Schema()

        sample = documents[:sample_size]
        field_types: dict[str, list[type]] = {}

        for doc in sample:
            for key, value in doc.items():
                inferred = SchemaDiscovery._infer_field_type(value)
                field_types.setdefault(key, []).append(inferred)

        fields: dict[str, Any] = {}
        for field_name, types in field_types.items():
            if not types:
                fields[field_name] = TEXT
            else:
                most_common = Counter(types).most_common(1)[0][0]
                fields[field_name] = most_common

        return Schema(**fields)

    @staticmethod
    def from_sample_optimized(
        documents: Sequence[Any],
        sample_size: int = 5,
        searchable_text: Sequence[str] | None = None,
    ) -> Schema:
        """Infer an optimized Schema from sample documents.

        Applies post-processing rules to reduce index size:
        - drop TEXT fields not listed in ``searchable_text``
        - downgrade obviously unique identifiers from TEXT to ID
        - downgrade low-cardinality boolean-like TEXT to BOOLEAN

        Args:
            documents: List of document mappings to infer types from.
            sample_size: Number of documents to sample for type inference.
            searchable_text: field names that should remain TEXT. All other
                TEXT-like fields are dropped unless their inferred type is
                already more specific than TEXT.

        Returns:
            Optimized Whoosh Schema.
        """
        base = SchemaDiscovery.from_sample(documents, sample_size=sample_size)
        searchable = set(searchable_text or [])
        optimized: dict[str, Any] = {}
        for name, field in base.items():
            current = type(field).__name__
            if current == "TEXT" and name not in searchable:
                continue
            if current == "TEXT" and SchemaDiscovery._looks_like_id(name):
                optimized[name] = ID(stored=True)
                continue
            if current == "TEXT" and SchemaDiscovery._looks_like_bool(documents, name):
                optimized[name] = BOOLEAN(stored=True)
                continue
            optimized[name] = field
        return Schema(**optimized)

    @staticmethod
    def detect_id_field(fields: dict[str, Any]) -> str | None:
        """Detect ID field from schema fields.

        Args:
            fields: Dict of field name to Whoosh field type.

        Returns:
            Name of the ID field, or None if no ID field is found.
        """
        for name, field in fields.items():
            if isinstance(field, ID):
                return name
        return None

    @staticmethod
    def _map_type(sql_type: str) -> Any:
        """Map a SQL type string to a Whoosh field class."""
        upper = (sql_type or "UNKNOWN").upper().strip()
        return SchemaDiscovery.SQL_TYPE_MAP.get(upper, TEXT)

    @staticmethod
    def _infer_field_type(value: Any) -> Any:
        """Infer a Whoosh field type from a Python value."""
        if isinstance(value, bool):
            return BOOLEAN
        if isinstance(value, int):
            return NUMERIC
        if isinstance(value, float):
            return NUMERIC
        if isinstance(value, dict):
            return KEYWORD
        if isinstance(value, list):
            return KEYWORD
        return TEXT

    @staticmethod
    def _looks_like_id(name: str) -> bool:
        lower = name.lower()
        return lower.endswith("id") or lower == "id"

    @staticmethod
    def _looks_like_bool(documents: Sequence[Any], field: str, sample_size: int = 20) -> bool:
        sample = [doc.get(field) for doc in documents[:sample_size] if field in doc]
        if not sample:
            return False
        lowered = {str(v).lower() for v in sample}
        return lowered.issubset({"true", "false", "1", "0", "yes", "no", "oui", "non"})
