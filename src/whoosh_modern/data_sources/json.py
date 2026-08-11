"""JSON DataSource implementation with streaming and schema discovery.

Author: dorel14
Version: 3.0.0
"""

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

    Args:
        path: Filesystem path to the JSON or JSONL file.
        document_path: Optional dotted path within the JSON object
            that points to the array of documents.
        encoding: File encoding (default ``"utf-8"``).
        incremental_field: Optional field name for incremental syncs.
        id_field: Optional field name that uniquely identifies a
            document.
        sample_size: Number of documents to sample during schema
            discovery.
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
        self._compiled_mapper: Any = None
        self._cached_data: Any = None

    @property
    def name(self) -> str:
        """Return the data source name.

        Returns:
            A string in the form ``json:<path>``.
        """
        return f"json:{self.path}"

    def health_check(self) -> bool:
        """Return True if the JSON file exists and is readable.

        Returns:
            ``True`` if the file is readable, ``False`` otherwise.
        """
        return os.path.isfile(self.path) and os.access(self.path, os.R_OK)

    def _read_file(self) -> Any:
        """Read and parse the JSON file.

        Caches the parsed result so subsequent reads are fast.

        Returns:
            The parsed JSON content (usually a list or dict).

        Raises:
            DataSourceError: If the file cannot be read or contains
                invalid JSON.
        """
        if self._cached_data is not None:
            return self._cached_data
        try:
            with open(self.path, encoding=self.encoding) as f:
                self._cached_data = json.load(f)
            return self._cached_data
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
        """Extract document list from parsed JSON data.

        If ``document_path`` is set, navigates the data using the
        dotted path. Otherwise looks for ``"results"`` or ``"data"``
        keys.

        Args:
            data: The parsed JSON content.

        Returns:
            A list of document dictionaries.
        """
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

    def _is_jsonl(self) -> bool:
        """Check if the file is line-delimited JSON (JSONL).

        Returns:
            ``True`` if the file appears to be JSONL, ``False``
            otherwise.
        """
        try:
            with open(self.path, encoding=self.encoding) as f:
                first_line = f.readline().strip()
                if not (first_line.startswith("{") or first_line.startswith("[")):
                    return False
                second_line = f.readline().strip()
                if not second_line:
                    return False
                return second_line.startswith("{") or second_line.startswith("[")
        except Exception:
            return False

    def _iter_jsonl(self) -> Iterator[dict[str, Any]]:
        """Iterate over line-delimited JSON (JSONL) efficiently.

        Yields:
            Each line parsed as a JSON object, as a dictionary.
        """
        with open(self.path, encoding=self.encoding) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    if isinstance(doc, dict):
                        yield doc
                except json.JSONDecodeError:
                    continue

    def compile_mapper(self) -> Any:
        """Return a compiled document mapper for this source.

        The mapper is a callable that transforms raw data into
        Whoosh documents. For JSON, this is the _extract_documents
        function bound with the document_path.

        Returns:
            A callable that accepts parsed JSON data and returns a
            list of document dictionaries.
        """
        if self._compiled_mapper is not None:
            return self._compiled_mapper

        document_path = self.document_path
        if document_path:
            parts = document_path.split(".")

            def mapper(data: Any) -> list[dict[str, Any]]:
                result = data
                for part in parts:
                    if isinstance(result, dict):
                        result = result.get(part, [])
                    else:
                        return []
                return [item for item in result if isinstance(item, dict)]

            self._compiled_mapper = mapper
        else:

            def mapper(data: Any) -> list[dict[str, Any]]:
                if isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
                if isinstance(data, dict):
                    results = data.get("results") or data.get("data")
                    if isinstance(results, list):
                        return [item for item in results if isinstance(item, dict)]
                return []

            self._compiled_mapper = mapper

        return self._compiled_mapper

    def discover_schema(self) -> Schema:
        """Discover schema from sample documents in the JSON file.

        Reads up to ``sample_size`` documents and uses
        :class:`SchemaDiscovery` to infer the Whoosh schema.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from
            sample documents.

        Raises:
            DataSourceError: If the file is not found or not readable.
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
            documents.append(dict(doc))

        if not documents:
            return Schema()

        self._schema = SchemaDiscovery.from_sample(documents, sample_size=self.sample_size)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the JSON file.

        Automatically detects JSONL format and streams line by line,
        or parses the full JSON document otherwise.

        Yields:
            Document dictionaries from the JSON file.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"JSON file not found or not readable: {self.path}",
                source="json",
            )

        if self._cached_data is not None:
            data = self._cached_data
            documents = self._extract_documents(data)
            yield from documents
            return

        if self._is_jsonl():
            yield from self._iter_jsonl()
            return

        data = self._read_file()
        documents = self._extract_documents(data)
        yield from documents

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the JSON file in batches.

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
                f"JSON file not found or not readable: {self.path}",
                source="json",
            )

        if self._cached_data is not None:
            data = self._cached_data
            documents = self._extract_documents(data)
            batch: list[dict[str, Any]] = []
            for doc in documents:
                batch.append(doc)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch
            return

        if self._is_jsonl():
            jsonl_batch: list[dict[str, Any]] = []
            for doc in self._iter_jsonl():
                jsonl_batch.append(doc)
                if len(jsonl_batch) >= batch_size:
                    yield jsonl_batch
                    jsonl_batch = []
            if jsonl_batch:
                yield jsonl_batch
            return

        data = self._read_file()
        documents = self._extract_documents(data)
        batch = []
        for doc in documents:
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for JSON).

        Args:
            since: A timestamp or cursor value (accepted but ignored).

        Yields:
            Nothing — incremental changes are not supported for this
            data source.
        """
        return iter([])

    def document_count(self) -> int:
        """Return total document count.

        Returns:
            The number of documents in the JSON file.

        Raises:
            DataSourceError: If the file is not found or not readable.
        """
        if not self.health_check():
            raise DataSourceError(
                f"JSON file not found or not readable: {self.path}",
                source="json",
            )

        if self._is_jsonl():
            return sum(1 for _ in self._iter_jsonl())

        return sum(1 for _ in self.iter_documents())

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this JSON source.

        Returns:
            A dictionary with keys ``type``, ``path``,
            ``document_path``, ``encoding``, ``incremental_field``,
            and ``id_field``.
        """
        return {
            "type": "json",
            "path": self.path,
            "document_path": self.document_path,
            "encoding": self.encoding,
            "incremental_field": self.incremental_field,
            "id_field": self.id_field,
        }
