"""Pandas DataSource implementation (optional backend)."""

import logging
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


class PandasSource:
    """Pandas DataFrame data source implementing the DataSource protocol.

    Uses pandas dtypes to infer the Whoosh schema directly, so
    ``SchemaDiscovery`` is not needed here.
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
        self._compiled_mapper: Any = None

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

        try:
            columns = list(self._dataframe.columns)
        except Exception:
            raise DataSourceError(
                "DataFrame is not initialized or has no columns",
                source="pandas",
            ) from None

        if not columns:
            raise DataSourceError(
                "DataFrame has no columns to infer schema",
                source="pandas",
            )

        column_types: dict[str, Any] = {}
        for col_name, dtype in self._dataframe.dtypes.items():
            column_types[str(col_name)] = self._map_pandas_dtype(dtype)

        from whoosh.fields import Schema

        self._schema = Schema(**column_types)
        return self._schema

    def _map_pandas_dtype(self, dtype: Any) -> Any:
        """Map pandas dtype to Whoosh field."""
        from whoosh.fields import BOOLEAN, DATETIME, NUMERIC, TEXT

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

    def compile_mapper(self) -> Any:
        """Return a compiled document mapper for this source.

        Pre-computes column names for fast DataFrame-to-dict conversion.
        Uses to_dict(orient='records') for batch extraction.
        """
        if self._compiled_mapper is not None:
            return self._compiled_mapper

        columns = list(self._dataframe.columns)

        def mapper(df_batch: Any) -> list[dict[str, Any]]:
            return df_batch[columns].to_dict(orient="records")  # type: ignore[no-any-return]

        self._compiled_mapper = mapper
        return self._compiled_mapper

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the DataFrame."""
        if self._dataframe is None:
            raise DataSourceError(
                "DataFrame is not initialized",
                source="pandas",
            )
        for _, row in self._dataframe.iterrows():
            yield row.to_dict()

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the DataFrame in batches.

        Uses to_dict(orient='records') for efficient batch extraction.
        """
        if self._dataframe is None:
            raise DataSourceError(
                "DataFrame is not initialized",
                source="pandas",
            )

        df = self._dataframe
        length = len(df)
        columns = list(df.columns)

        for start in range(0, length, batch_size):
            end = min(start + batch_size, length)
            batch_df = df.iloc[start:end]
            yield batch_df[columns].to_dict(orient="records")

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for Pandas)."""
        return iter([])

    def document_count(self) -> int:
        """Return total row count."""
        if self._dataframe is None:
            raise DataSourceError(
                "DataFrame is not initialized",
                source="pandas",
            )
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
