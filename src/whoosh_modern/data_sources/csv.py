"""CSV DataSource implementation with streaming and schema discovery."""

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
    """Sanitize a CSV header into a valid Whoosh field name."""
    name = name.strip()
    name = re.sub(r"[^\w]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_") or "field"


class CSVSource:
    """CSV file data source implementing the DataSource protocol."""

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
        self._file: Any = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"csv:{self.path}"

    def health_check(self) -> bool:
        """Return True if the CSV file exists and is readable."""
        return os.path.isfile(self.path) and os.access(self.path, os.R_OK)

    def _open_file(self) -> Any:
        """Open the CSV file for reading."""
        try:
            return open(self.path, newline="", encoding=self.encoding)
        except OSError as e:
            raise DataSourceError(
                f"Cannot open CSV file: {e}",
                source="csv",
            ) from e

    def _sanitize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Sanitize a CSV row dict so keys are valid Whoosh field names."""
        return {_sanitize_field_name(k): v for k, v in row.items()}

    def discover_schema(self) -> Schema:
        """Discover schema from CSV header and sample rows."""
        if not self.health_check():
            raise DataSourceError(
                f"CSV file not found or not readable: {self.path}",
                source="csv",
            )

        with self._open_file() as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            if not reader.fieldnames:
                return Schema()

            samples = []
            for i, row in enumerate(reader):
                if i >= self.sample_size:
                    break
                samples.append(self._sanitize_row(dict(row)))

        self._schema = SchemaDiscovery.from_sample(samples, sample_size=self.sample_size)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the CSV file."""
        if not self.health_check():
            raise DataSourceError(
                f"CSV file not found or not readable: {self.path}",
                source="csv",
            )

        with self._open_file() as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            for row in reader:
                yield self._sanitize_row(dict(row))

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for CSV)."""
        return iter([])

    def document_count(self) -> int:
        """Return total row count in the CSV file."""
        if not self.health_check():
            raise DataSourceError(
                f"CSV file not found or not readable: {self.path}",
                source="csv",
            )
        count = 0
        with self._open_file() as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            for _ in reader:
                count += 1
        return count

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this CSV source."""
        return {
            "type": "csv",
            "path": self.path,
            "delimiter": self.delimiter,
            "encoding": self.encoding,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
