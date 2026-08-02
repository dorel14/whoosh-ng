"""JSON DataSource implementation with streaming and schema discovery."""

import json
import logging
import os
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]


class JSONSource:
    """JSON file data source implementing the DataSource protocol.

    Supports:
    - JSON array of objects: [{"id": 1, "title": "..."}, ...]
    - JSON object with array field: {"results": [{"id": 1, ...}]}
    - Line-delimited JSON (JSONL): one JSON object per line
    """

    def __init__(
        self,
        path: str,
        document_path: str | None = None,
        encoding: str = "utf-8",
        incremental_field: str | None = None,
        id_field: str | None = None,
        sample_size: int = 5,
    ) -> None:
        self.path = path
        self.document_path = document_path
        self.encoding = encoding
        self.incremental_field = incremental_field
        self.id_field = id_field
        self.sample_size = sample_size
        self._schema: Schema | None = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"json:{self.path}"

    def health_check(self) -> bool:
        """Return True if the JSON file exists and is readable."""
        return os.path.isfile(self.path) and os.access(self.path, os.R_OK)

    def _read_file(self) -> Any:
        """Read and parse the JSON file."""
        try:
            with open(self.path, encoding=self.encoding) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataSourceError(
                f"Invalid JSON in {self.path}: {e}",
                source="json",
            ) from e
        except OSError as e:
            raise DataSourceError(
                f"Cannot read JSON file: {e}",
                source="json",
            ) from e

    def _extract_documents(self, data: Any) -> list[dict[str, Any]]:
        """Extract document list from parsed JSON data."""
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            if self.document_path:
                result = data
                for part in self.document_path.split("."):
                    if isinstance(result, dict):
                        result = result.get(part, [])
                    else:
                        return []
                return [item for item in result if isinstance(item, dict)]
            if "results" in data and isinstance(data["results"], list):
                return [item for item in data["results"] if isinstance(item, dict)]
            if "data" in data and isinstance(data["data"], list):
                return [item for item in data["data"] if isinstance(item, dict)]
            return []
        return []

    def discover_schema(self) -> Schema:
        """Discover schema from sample documents in the JSON file.

        Uses sampling to avoid loading the entire file into memory for
        large JSON datasets.
        """
        if not self.health_check():
            raise DataSourceError(
                f"JSON file not found or not readable: {self.path}",
                source="json",
            )

        documents: list[dict[str, Any]] = []
        for i, doc in enumerate(self.iter_documents()):
            if i >= self.sample_size:
                break
            documents.append(doc)

        if not documents:
            return Schema()

        self._schema = SchemaDiscovery.from_sample(documents, sample_size=self.sample_size)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the JSON file."""
        if not self.health_check():
            raise DataSourceError(
                f"JSON file not found or not readable: {self.path}",
                source="json",
            )

        data = self._read_file()
        documents = self._extract_documents(data)
        yield from documents

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for JSON)."""
        return iter([])

    def document_count(self) -> int:
        """Return total document count."""
        if not self.health_check():
            raise DataSourceError(
                f"JSON file not found or not readable: {self.path}",
                source="json",
            )
        return sum(1 for _ in self.iter_documents())

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this JSON source."""
        return {
            "type": "json",
            "path": self.path,
            "document_path": self.document_path,
            "encoding": self.encoding,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
