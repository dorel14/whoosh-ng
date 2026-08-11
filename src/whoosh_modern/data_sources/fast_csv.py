"""Fast CSV DataSource using csv.reader with pre-compiled column mapping.

Author: dorel14
Version: 3.0.0
"""

import csv
import logging
import os
import re
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]

_DEFAULT_DELIMITER = ","
_DEFAULT_ENCODING = "utf-8"


def _sanitize_field_name(name: str) -> str:
    """Sanitize a CSV header into a valid Whoosh field name.

    Strips whitespace, replaces non-word characters with underscores,
    and collapses consecutive underscores.

    Args:
        name: The raw header string.

    Returns:
        A sanitized field name string.
    """
    name = name.strip()
    name = re.sub(r"[^\w]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_") or "field"


class FastCSVSource:
    """High-performance CSV data source using csv.reader.

    Uses a pre-compiled column index-to-field-name mapping to avoid
    per-row dictionary creation overhead. Significantly faster than
    CSVSource for large files.

    Example::

        source = FastCSVSource("data.csv")
        for batch in source.stream_batches(batch_size=5000):
            writer.add_batch(batch)

    Args:
        path: Filesystem path to the CSV file.
        delimiter: Column delimiter (default ``","``).
        encoding: File encoding (default ``"utf-8"``).
        incremental_field: Optional field name for incremental syncs.
        id_field: Optional field name that uniquely identifies a
            document.
        sample_size: Number of rows to sample during schema
            discovery.
    """

    def __init__(
        self,
        path: str,
        delimiter: str = _DEFAULT_DELIMITER,
        encoding: str = _DEFAULT_ENCODING,
        incremental_field: str | None = None,
        id_field: str | None = None,
        sample_size: int = 5,
    ) -> None:
        self.path = path
        self.delimiter = delimiter
        self.encoding = encoding
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self._schema: Schema | None = None
        self._column_map: list[tuple[int, str]] | None = None

    @property
    def name(self) -> str:
        """Return the data source name.

        Returns:
            A string in the form ``fast_csv:<path>``.
        """
        return f"fast_csv:{self.path}"

    def health_check(self) -> bool:
        """Return True if the CSV file exists and is readable.

        Returns:
            ``True`` if the file is readable, ``False`` otherwise.
        """
        return os.path.isfile(self.path) and os.access(self.path, os.R_OK)

    def _open_file(self) -> Any:
        """Open the CSV file for reading.

        Returns:
            An open file handle.

        Raises:
            DataSourceError: If the file cannot be opened.
        """
        try:
            return open(self.path, newline="", encoding=self.encoding)
        except OSError as e:
            raise DataSourceError(
                f"Cannot open CSV file: {e}",
                source="fast_csv",
            ) from e

    def _build_column_map(self, headers: list[str]) -> list[tuple[int, str]]:
        """Build a list of (column_index, sanitized_field_name) pairs.

        Args:
            headers: List of raw CSV header strings.

        Returns:
            A list of tuples pairing column indices with sanitized
            field names.
        """
        return [(i, _sanitize_field_name(name)) for i, name in enumerate(headers)]

    def _row_to_doc(self, row: list[str]) -> dict[str, Any]:
        """Convert a csv.reader row to a document dict using the column map.

        Args:
            row: A list of string values from a CSV row.

        Returns:
            A dictionary mapping sanitized field names to values.
            If no column map has been built, returns an empty dict.
        """
        column_map = self._column_map
        if column_map is None:
            return {}
        return {
            field_name: row[col_idx] for col_idx, field_name in column_map if col_idx < len(row)
        }

    def discover_schema(self) -> Schema:
        """Discover schema from CSV header and sample rows.

        Reads the header row and up to ``sample_size`` data rows, then
        uses :class:`SchemaDiscovery` to infer field types.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from the
            sample data.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"CSV file not found or not readable: {self.path}",
                source="fast_csv",
            )

        with self._open_file() as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            headers = next(reader, None)
            if not headers:
                return Schema()

            self._column_map = self._build_column_map(headers)
            samples = []
            for i, row in enumerate(reader):
                if i >= self.sample_size:
                    break
                samples.append(self._row_to_doc(row))

        self._schema = SchemaDiscovery.from_sample(samples, sample_size=self.sample_size)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the CSV file.

        Yields:
            Document dictionaries, one per data row.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"CSV file not found or not readable: {self.path}",
                source="fast_csv",
            )

        with self._open_file() as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            headers = next(reader, None)
            if headers is None:
                return
            self._column_map = self._build_column_map(headers)
            for row in reader:
                yield self._row_to_doc(row)

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the CSV file in batches.

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
                f"CSV file not found or not readable: {self.path}",
                source="fast_csv",
            )

        with self._open_file() as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            headers = next(reader, None)
            if headers is None:
                return
            self._column_map = self._build_column_map(headers)
            batch: list[dict[str, Any]] = []
            for row in reader:
                batch.append(self._row_to_doc(row))
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for CSV).

        Args:
            since: A timestamp or cursor value (accepted but ignored).

        Yields:
            Nothing — incremental changes are not supported for this
            data source.
        """
        return iter([])

    def document_count(self) -> int:
        """Return total row count in the CSV file.

        Returns:
            The number of data rows (excluding the header).

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"CSV file not found or not readable: {self.path}",
                source="fast_csv",
            )
        count = 0
        with self._open_file() as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            next(reader, None)
            for _ in reader:
                count += 1
        return count

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this CSV source.

        Returns:
            A dictionary with keys ``type``, ``path``,
            ``delimiter``, ``encoding``, ``incremental_field``, and
            ``id_field``.
        """
        return {
            "type": "fast_csv",
            "path": self.path,
            "delimiter": self.delimiter,
            "encoding": self.encoding,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
