"""Pandas DataSource implementation (optional backend)."""

import logging
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


class PandasSource:
    """Pandas DataFrame data source implementing the DataSource protocol.

    Supports iterating over a pandas DataFrame and discovering the Whoosh schema
    from the DataFrame's dtypes.

    Example:
        import pandas as pd
        from whoosh_modern.data_sources.pandas_ds import PandasSource

        df = pd.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PandasSource(dataframe=df)
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
        return f"pandas:{id(self._dataframe)}"

    def health_check(self) -> bool:
        """Return True if the DataFrame is non-empty."""
        try:
            return len(self._dataframe) > 0
        except Exception:
            return False

    def discover_schema(self) -> Schema:
        """Discover schema from pandas DataFrame dtypes."""
        if self._schema is not None:
            return self._schema

        columns: dict[str, Any] = {}
        for col_name, dtype in self._dataframe.dtypes.items():
            columns[str(col_name)] = self._map_pandas_dtype(dtype)

        from whoosh.fields import Schema

        self._schema = Schema(**columns)
        return self._schema

    def _map_pandas_dtype(self, dtype: Any) -> Any:
        """Map pandas dtype to Whoosh field."""
        from whoosh.fields import BOOLEAN, DATETIME, ID, NUMERIC, TEXT

        dtype_str = str(dtype).lower()

        if "int" in dtype_str:
            return NUMERIC(int, stored=True)
        if "float" in dtype_str:
            return NUMERIC(float, stored=True)
        if "bool" in dtype_str:
            return BOOLEAN(stored=True)
        if "datetime" in dtype_str:
            return DATETIME(stored=True)
        if "object" in dtype_str or "string" in dtype_str:
            return TEXT(stored=True)

        return TEXT(stored=True)

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the DataFrame."""
        for _, row in self._dataframe.iterrows():
            yield row.to_dict()

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for Pandas)."""
        return iter([])

    def document_count(self) -> int:
        """Return total row count."""
        return len(self._dataframe)

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this Pandas source."""
        return {
            "type": "pandas",
            "shape": tuple(self._dataframe.shape),
            "columns": list(self._dataframe.columns),
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
