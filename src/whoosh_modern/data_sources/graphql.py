"""GraphQL DataSource implementation with pagination support."""

import json
import logging
import urllib.request
from collections.abc import Iterator, Mapping
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

Document = Mapping[str, Any]
DEFAULT_TIMEOUT = 30


try:
    import requests as _requests

    class _HTTPClient:
        """HTTP client using the requests library."""

        def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
            self._session = _requests.Session()
            self._timeout = timeout

        def post(
            self,
            url: str,
            json_data: dict[str, Any],
            headers: dict[str, str],
        ) -> dict[str, Any]:
            response = self._session.post(
                url,
                json=json_data,
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]


except ImportError:
    _HTTPClient = None  # type: ignore[assignment,misc]


class _UrllibHttpClient:
    """HTTP client using urllib.request as fallback."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def post(
        self,
        url: str,
        json_data: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(json_data).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            return json.loads(response.read().decode("utf-8"))  # type: ignore[no-any-return]


def _get_http_client(timeout: int) -> Any:
    """Return the best available HTTP client."""
    if _HTTPClient is not None:
        return _HTTPClient(timeout)
    return _UrllibHttpClient(timeout)


class GraphQLSource:
    """GraphQL API data source implementing the DataSource protocol."""

    def __init__(
        self,
        url: str,
        query: str,
        document_path: str | None = None,
        headers: dict[str, str] | None = None,
        auth: Any | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        sample_size: int = 5,
    ) -> None:
        self.url = url
        self.query = query
        self.document_path = document_path
        self.headers = headers or {}
        self.auth = auth
        self.timeout = timeout
        self.sample_size = sample_size
        self._schema: Schema | None = None
        self._http_client = _get_http_client(timeout)

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"graphql:{self.url}"

    def health_check(self) -> bool:
        """Return True if the GraphQL endpoint is reachable."""
        try:
            payload = {"query": "{ __typename }"}
            self._http_client.post(self.url, payload, self._get_headers())
            return True
        except Exception:
            return False

    def _get_headers(self) -> dict[str, str]:
        """Build headers including auth."""
        result = dict(self.headers)
        if isinstance(self.auth, dict):
            if self.auth.get("type") == "bearer":
                result["Authorization"] = f"Bearer {self.auth.get('token')}"
            elif self.auth.get("api_key"):
                result["X-API-Key"] = self.auth["api_key"]
        return result

    def _extract_documents(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract document list from GraphQL response."""
        if "errors" in data:
            raise DataSourceError(
                f"GraphQL error: {data['errors']}",
                source="graphql",
            )

        if "data" not in data:
            return []

        result = data["data"]
        if self.document_path:
            for part in self.document_path.split("."):
                if isinstance(result, dict):
                    result = result.get(part, {})
                else:
                    return []
            if isinstance(result, list):
                return [item for item in result if isinstance(item, dict)]
            return []

        for value in result.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def discover_schema(self) -> Schema:
        """Discover schema from first page of GraphQL results."""
        documents = list(self.iter_documents())
        if not documents:
            return Schema()
        self._schema = SchemaDiscovery.from_sample(documents, sample_size=self.sample_size)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the GraphQL API."""
        payload: dict[str, Any] = {"query": self.query}
        try:
            data = self._http_client.post(self.url, payload, self._get_headers())
        except Exception as e:
            raise DataSourceError(
                f"GraphQL request failed: {e}",
                source="graphql",
            ) from e
        documents = self._extract_documents(data)
        yield from documents

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the GraphQL API in batches.

        For GraphQL, each response is treated as a batch.
        """
        payload: dict[str, Any] = {"query": self.query}
        try:
            data = self._http_client.post(self.url, payload, self._get_headers())
        except Exception as e:
            raise DataSourceError(
                f"GraphQL request failed: {e}",
                source="graphql",
            ) from e
        documents = self._extract_documents(data)

        batch: list[dict[str, Any]] = []
        for doc in documents:
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def iter_changes(self, since: Any) -> Iterator[Document]:
        """Yield documents changed since a timestamp (not implemented for GraphQL)."""
        return iter([])

    def document_count(self) -> int:
        """Return approximate document count."""
        return sum(1 for _ in self.iter_documents())

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this GraphQL source."""
        return {
            "type": "graphql",
            "url": self.url,
            "query": self.query,
            "document_path": self.document_path,
            "timeout": self.timeout,
        }
