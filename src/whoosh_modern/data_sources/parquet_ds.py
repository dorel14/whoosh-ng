"""Parquet DataSource implementation (optional backend).

Author: dorel14
Version: 3.0.0
"""

import logging
import os
from collections.abc import Iterator, Mapping
from datetime import date, datetime
from typing import Any, Literal

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]

_BATCH_SIZE = 1000


def _to_datetime(value: Any) -> Any:
    """Convert date-only values to datetime for Whoosh compatibility.

    Args:
        value: A value that may be a ``date`` (but not ``datetime``).

    Returns:
        A ``datetime`` if ``value`` was a date, otherwise the original
        value unchanged.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    return value


class ParquetSource:
    """Parquet file data source implementing the DataSource protocol.

    Supports reading Parquet files using pyarrow, pandas, or polars.
    Prefers PyArrow streaming for large files to avoid loading the entire
    dataset into memory.

    Uses PyArrow schema / pandas dtypes / Polars dtypes to infer the
    Whoosh schema directly, so ``SchemaDiscovery`` is not needed here.

    Args:
        path: Filesystem path to the Parquet file.
        incremental_field: Optional column name for incremental syncs.
        id_field: Optional column name that uniquely identifies a
            document.
        sample_size: Number of rows to sample during schema discovery.
        engine: Parquet read engine (``"auto"``, ``"fastparquet"``,
            ``"pyarrow"``).
    """

    def __init__(
        self,
        path: str,
        incremental_field: str | None = None,
        id_field: str | None = None,
        sample_size: int = 5,
        engine: Literal["auto", "fastparquet", "pyarrow"] = "auto",
    ) -> None:
        self.path = path
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self.engine: Literal["auto", "fastparquet", "pyarrow"] = engine
        self._schema: Schema | None = None
        self._compiled_mapper: Any = None

    @property
    def name(self) -> str:
        """Return the data source name.

        Returns:
            A string in the form ``parquet:<path>``.
        """
        return f"parquet:{self.path}"

    def health_check(self) -> bool:
        """Return True if the Parquet file exists and is readable.

        Returns:
            ``True`` if the file is readable, ``False`` otherwise.
        """
        return os.path.isfile(self.path) and os.access(self.path, os.R_OK)

    def _read_parquet(self, sample: bool = False) -> Any:
        """Read the Parquet file and return a DataFrame.

        Tries ``pandas``, then ``polars``, then ``pyarrow``+pandas
        as backends.

        Args:
            sample: If ``True``, read only the first ``sample_size``
                rows.

        Returns:
            A DataFrame (pandas or polars) containing the data.

        Raises:
            DataSourceError: If no Parquet engine is installed.
        """
        try:
            import pandas as pd  # pyright: ignore[reportMissingImports]

            engine = self.engine
            if engine == "pyarrow":
                engine = "auto"

            if sample:
                return pd.read_parquet(self.path, engine=engine).head(self.sample_size)
            return pd.read_parquet(self.path, engine=engine)
        except ImportError:
            pass

        try:
            import polars as pl  # pyright: ignore[reportMissingImports]

            if sample:
                return pl.read_parquet(self.path).head(self.sample_size)
            return pl.read_parquet(self.path)
        except ImportError:
            pass

        try:
            import pyarrow.parquet as pq  # pyright: ignore[reportMissingImports]

            if sample:
                return pq.read_table(self.path).slice(0, self.sample_size).to_pandas()
            table = pq.read_table(self.path)
            return table.to_pandas()
        except ImportError:
            pass

        raise DataSourceError(
            "No Parquet engine available. Install pandas, polars, or pyarrow.",
            source="parquet",
        )

    def _iter_pyarrow_batches(self, batch_size: int = _BATCH_SIZE) -> Iterator[dict[str, Any]]:
        """Stream documents from a Parquet file using PyArrow batches.

        Args:
            batch_size: Number of rows per PyArrow batch.

        Yields:
            Document dictionaries streamed from the Parquet file.
        """
        try:
            import pyarrow.parquet as pq  # pyright: ignore[reportMissingImports]
        except ImportError:
            df = self._read_parquet()
            for _, row in df.iterrows():
                yield {k: _to_datetime(v) for k, v in row.to_dict().items()}
            return

        pf = pq.ParquetFile(self.path)
        for batch in pf.iter_batches(batch_size=batch_size):
            batch_dict = batch.to_pydict()
            keys = list(batch_dict.keys())
            length = len(batch)
            for i in range(length):
                yield {key: _to_datetime(batch_dict[key][i]) for key in keys}

    def compile_mapper(self) -> Any:
        """Return a compiled document mapper for this source.

        Pre-computes column keys for fast batch extraction.

        Returns:
            A callable that transforms a batch result into a list
            of document dictionaries.
        """
        if self._compiled_mapper is not None:
            return self._compiled_mapper

        try:
            import pyarrow.parquet as pq  # pyright: ignore[reportMissingImports]

            pf = pq.ParquetFile(self.path)
            batch = next(pf.iter_batches(batch_size=1))
            keys = list(batch.to_pydict().keys())

            def _pyarrow_mapper(batch_dict: dict[str, Any], length: int) -> list[dict[str, Any]]:
                result = []
                for i in range(length):
                    result.append({key: _to_datetime(batch_dict[key][i]) for key in keys})
                return result

            self._compiled_mapper = _pyarrow_mapper
        except ImportError:
            keys = list(self._read_parquet(sample=True).columns)

            def _fallback_mapper(row: Any) -> dict[str, Any]:
                return {k: _to_datetime(v) for k, v in zip(keys, row, strict=True)}

            self._compiled_mapper = _fallback_mapper

        return self._compiled_mapper

    def discover_schema(self) -> Schema:
        """Discover schema from Parquet file metadata.

        Uses PyArrow's schema introspection when available, falling
        back to pandas dtypes.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from the
            Parquet file's column types.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"Parquet file not found or not readable: {self.path}",
                source="parquet",
            )

        from whoosh_modern.models.base import TypeMapper

        try:
            import pyarrow.parquet as pq  # pyright: ignore[reportMissingImports]

            schema = pq.read_schema(self.path)
            columns: dict[str, Any] = {
                str(field.name): TypeMapper.map_dtype(field.type) for field in schema
            }

            from whoosh.fields import Schema

            self._schema = Schema(**columns)
            return self._schema
        except ImportError:
            pass

        df = self._read_parquet(sample=True)
        columns = {
            str(col_name): TypeMapper.map_dtype(dtype)
            for col_name, dtype in zip(df.columns, df.dtypes, strict=True)
        }

        from whoosh.fields import Schema

        self._schema = Schema(**columns)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the Parquet file.

        Yields:
            Document dictionaries streamed from the Parquet file.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"Parquet file not found or not readable: {self.path}",
                source="parquet",
            )

        yield from self._iter_pyarrow_batches()

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the Parquet file in batches.

        Uses PyArrow native batch reading when available to avoid loading
        the entire dataset into memory.

        Args:
            batch_size: Maximum number of documents per batch.

        Yields:
            Lists of document dictionaries, each list containing at
            most ``batch_size`` items.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"Parquet file not found or not readable: {self.path}",
                source="parquet",
            )

        try:
            import pyarrow.parquet as pq  # pyright: ignore[reportMissingImports]

            pf = pq.ParquetFile(self.path)
            for pb in pf.iter_batches(batch_size=batch_size):
                batch_dict = pb.to_pydict()
                keys = list(batch_dict.keys())
                length = len(pb)
                batch_docs: list[dict[str, Any]] = []
                for i in range(length):
                    batch_docs.append({key: _to_datetime(batch_dict[key][i]) for key in keys})
                yield batch_docs
        except ImportError:
            batch: list[dict[str, Any]] = []
            for doc in self._iter_pyarrow_batches():
                batch.append(dict(doc))
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for Parquet).

        Args:
            since: A timestamp or cursor value (accepted but ignored).

        Yields:
            Nothing — incremental changes are not supported for this
            data source.
        """
        return iter([])

    def document_count(self) -> int:
        """Return total row count.

        Uses PyArrow metadata for a fast count when available.

        Returns:
            The number of rows in the Parquet file.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"Parquet file not found or not readable: {self.path}",
                source="parquet",
            )

        try:
            import pyarrow.parquet as pq  # pyright: ignore[reportMissingImports]

            pf = pq.ParquetFile(self.path)
            return int(pf.metadata.num_rows)
        except ImportError:
            pass

        df = self._read_parquet()
        return len(df)

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this Parquet source.

        Returns:
            A dictionary with keys ``type``, ``path``, ``engine``,
            ``incremental_field``, and ``id_field``.
        """
        return {
            "type": "parquet",
            "path": self.path,
            "engine": self.engine,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
