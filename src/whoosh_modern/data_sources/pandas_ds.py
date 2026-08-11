"""Pandas DataSource implementation (optional backend).

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


class PandasSource:
    """Pandas DataFrame data source implementing the DataSource protocol.

    Uses pandas dtypes to infer the Whoosh schema directly, so
    ``SchemaDiscovery`` is not needed here.

    Args:
        dataframe: A pandas ``DataFrame`` to iterate over.
        incremental_field: Optional column name for incremental syncs.
        id_field: Optional column name that uniquely identifies a
            document.
        sample_size: Number of rows to inspect during schema discovery.
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
        """Return the data source name.

        Returns:
            A string in the form ``pandas:<id>`` where ``id`` is the
            Python ``id()`` of the DataFrame.
        """
        return f"pandas:{id(self._dataframe)}"

    def health_check(self) -> bool:
        """Return True if the DataFrame is non-empty.

        Returns:
            ``True`` if the DataFrame has at least one row, ``False``
            otherwise.
        """
        try:
            return len(self._dataframe) > 0
        except Exception:
            return False

    def discover_schema(self) -> Schema:
        """Discover schema from pandas DataFrame dtypes.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from the
            DataFrame's column dtypes.

        Raises:
            DataSourceError: If the DataFrame is not initialised or
                has no columns.
        """
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
        """Map pandas dtype to Whoosh field.

        Delegates to the canonical
        :meth:`whoosh_modern.models.base.TypeMapper.map_dtype`.

        Args:
            dtype: A pandas dtype instance.

        Returns:
            A Whoosh field instance (``NUMERIC``, ``BOOLEAN``,
            ``DATETIME``, or ``TEXT``) configured as stored.
        """
        from whoosh_modern.models.base import TypeMapper

        return TypeMapper.map_dtype(dtype)

    def compile_mapper(self) -> Any:
        """Return a compiled document mapper for this source.

        Pre-computes column names for fast DataFrame-to-dict conversion.
        Uses to_dict(orient='records') for batch extraction.

        Returns:
            A callable that accepts a pandas DataFrame and returns a
            list of document dictionaries.
        """
        if self._compiled_mapper is not None:
            return self._compiled_mapper

        columns = list(self._dataframe.columns)

        def mapper(df_batch: Any) -> list[dict[str, Any]]:
            return df_batch[columns].to_dict(orient="records")  # type: ignore[no-any-return]

        self._compiled_mapper = mapper
        return self._compiled_mapper

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the DataFrame.

        Yields:
            Document dictionaries, one per row.

        Raises:
            DataSourceError: If the DataFrame is not initialised.
        """
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

        Args:
            batch_size: Maximum number of rows per batch.

        Yields:
            Lists of document dictionaries, each list containing at
            most ``batch_size`` items.

        Raises:
            DataSourceError: If the DataFrame is not initialised.
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
        """Yield documents changed since a timestamp (not implemented for Pandas).

        Args:
            since: A timestamp or cursor value (accepted but ignored).

        Yields:
            Nothing — incremental changes are not supported for this
            data source.
        """
        return iter([])

    def document_count(self) -> int:
        """Return total row count.

        Returns:
            The number of rows in the DataFrame.

        Raises:
            DataSourceError: If the DataFrame is not initialised.
        """
        if self._dataframe is None:
            raise DataSourceError(
                "DataFrame is not initialized",
                source="pandas",
            )
        return len(self._dataframe)

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this Pandas source.

        Returns:
            A dictionary with keys ``type``, ``shape``, ``columns``,
            ``incremental_field``, and ``id_field``.
        """
        return {
            "type": "pandas",
            "shape": tuple(self._dataframe.shape),
            "columns": list(self._dataframe.columns),
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
