"""Polars DataSource implementation (optional backend)."""

import logging
from collections.abc import Iterator, Mapping
from datetime import date, datetime
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


def _to_datetime(value: Any) -> Any:
    """Convert date-only values to datetime for Whoosh compatibility."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    return value


class PolarsSource:
    """Polars DataFrame data source implementing the DataSource protocol.

    Supports iterating over a Polars DataFrame and discovering the Whoosh schema
    from the DataFrame's dtypes.

    Example:
        import polars as pl
        from whoosh_modern.data_sources.polars_ds import PolarsSource

        df = pl.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PolarsSource(dataframe=df)
    """

    def __init__(
        self,
        dataframe: Any,
        incremental_field: str | None = None,
        id_field: str | None = None,
        sample_size: int = 5,
    ) -> None:
        self._dataframe = dataframe
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self._schema: Schema | None = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"polars:{id(self._dataframe)}"

    def health_check(self) -> bool:
        """Return True if the DataFrame is non-empty."""
        try:
            return len(self._dataframe) > 0
        except Exception:
            return False

    def discover_schema(self) -> Schema:
        """Discover schema from Polars DataFrame dtypes."""
        if self._schema is not None:
            return self._schema

        columns: dict[str, Any] = {}
        for col_name, dtype in zip(self._dataframe.columns, self._dataframe.dtypes, strict=True):
            columns[str(col_name)] = self._map_polars_dtype(dtype)

        from whoosh.fields import Schema

        self._schema = Schema(**columns)
        return self._schema

    def _map_polars_dtype(self, dtype: Any) -> Any:
        """Map Polars dtype to Whoosh field."""
        from whoosh.fields import BOOLEAN, DATETIME, ID, NUMERIC, TEXT

        dtype_str = str(dtype).lower()

        if "int" in dtype_str:
            return NUMERIC(int, stored=True)
        if "float" in dtype_str:
            return NUMERIC(float, stored=True)
        if "bool" in dtype_str:
            return BOOLEAN(stored=True)
        if "date" in dtype_str or "time" in dtype_str:
            return DATETIME(stored=True)
        if "str" in dtype_str or "utf" in dtype_str:
            return TEXT(stored=True)

        return TEXT(stored=True)

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the DataFrame."""
        for row in self._dataframe.iter_rows(named=True):
            yield {k: _to_datetime(v) for k, v in row.items()}

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for Polars)."""
        return iter([])

    def document_count(self) -> int:
        """Return total row count."""
        return len(self._dataframe)

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this Polars source."""
        return {
            "type": "polars",
            "shape": tuple(self._dataframe.shape),
            "columns": list(self._dataframe.columns),
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
