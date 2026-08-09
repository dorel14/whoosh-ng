"""GraphQL DataSource implementation with pagination support.

Author: dorel14
Version: 3.0.0
"""

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
        """HTTP client using the requests library.

        Args:
            timeout: Request timeout in seconds.
        """

        def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
            self._session = _requests.Session()
            self._timeout = timeout

        def post(
            self,
            url: str,
            json_data: dict[str, Any],
            headers: dict[str, str],
        ) -> dict[str, Any]:
            """Send a GraphQL POST request and return the parsed response.

            Args:
                url: The GraphQL endpoint URL.
                json_data: The GraphQL request payload (query,
                    variables, etc.).
                headers: HTTP headers to include in the request.

            Returns:
                The parsed JSON response body as a dictionary.

            Raises:
                requests.HTTPError: If the server returns an error
                    status code.
            """
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
    """HTTP client using urllib.request as fallback.

    Used when the ``requests`` library is not installed.

    Args:
        timeout: Request timeout in seconds.
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def post(
        self,
        url: str,
        json_data: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """Send a GraphQL POST request and return the parsed response.

        Args:
            url: The GraphQL endpoint URL.
            json_data: The GraphQL request payload.
            headers: HTTP headers to include in the request.

        Returns:
            The parsed JSON response body as a dictionary.

        Raises:
            urllib.error.URLError: If the request fails.
        """
        request = urllib.request.Request(
            url,
            data=json.dumps(json_data).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            return json.loads(response.read().decode("utf-8"))  # type: ignore[no-any-return]


def _get_http_client(timeout: int) -> Any:
    """Return the best available HTTP client.

    Prefers ``requests`` if installed, falls back to ``urllib``.

    Args:
        timeout: Request timeout in seconds.

    Returns:
        An HTTP client instance with a matching ``post`` method.
    """
    if _HTTPClient is not None:
        return _HTTPClient(timeout)
    return _UrllibHttpClient(timeout)


class GraphQLSource:
    """GraphQL API data source implementing the DataSource protocol.

    Sends a GraphQL query to an endpoint and yields the resulting
    documents. Supports bearer-token and API-key authentication.

    Args:
        url: The GraphQL endpoint URL.
        query: The GraphQL query string to execute.
        document_path: Optional dotted path within the response's
            ``data`` field that points to the list of documents.
        headers: Optional static HTTP headers.
        auth: Optional authentication configuration. May be a dict
            with ``type`` set to ``"bearer"`` and ``token``, or
            ``"api_key"`` and an ``api_key`` value.
        timeout: Request timeout in seconds.
        sample_size: Number of documents to sample during schema
            discovery.
    """

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
        """Return the data source name.

        Returns:
            A string in the form ``graphql:<url>``.
        """
        return f"graphql:{self.url}"

    def health_check(self) -> bool:
        """Return True if the GraphQL endpoint is reachable.

        Returns:
            ``True`` if a trivial ``{ __typename }`` query succeeds,
            ``False`` otherwise.
        """
        try:
            payload = {"query": "{ __typename }"}
            self._http_client.post(self.url, payload, self._get_headers())
            return True
        except Exception:
            return False

    def _get_headers(self) -> dict[str, str]:
        """Build headers including auth.

        Merges user-supplied headers with authentication headers
        derived from the ``auth`` configuration.

        Returns:
            A dictionary of HTTP headers for outgoing requests.
        """
        result = dict(self.headers)
        if isinstance(self.auth, dict):
            if self.auth.get("type") == "bearer":
                result["Authorization"] = f"Bearer {self.auth.get('token')}"
            elif self.auth.get("api_key"):
                result["X-API-Key"] = self.auth["api_key"]
        return result

    def _extract_documents(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract document list from GraphQL response.

        If ``document_path`` is set, navigates the response data using
        the dotted path. Otherwise returns the first list-valued field
        found in the response data.

        Args:
            data: The parsed JSON response from the GraphQL endpoint.

        Returns:
            A list of document dictionaries.

        Raises:
            DataSourceError: If the response contains errors.
        """
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
        """Discover schema from first page of GraphQL results.

        Executes the query once and uses
        :class:`SchemaDiscovery` to infer the Whoosh schema.

        Returns:
            A Whoosh :class:`~whoosh.fields.Schema` derived from
            sample documents.
        """
        documents = list(self.iter_documents())
        if not documents:
            return Schema()
        self._schema = SchemaDiscovery.from_sample(documents, sample_size=self.sample_size)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the GraphQL API.

        Sends the configured GraphQL query and yields each document
        extracted from the response.

        Yields:
            Document dictionaries from the GraphQL response.

        Raises:
            DataSourceError: If the request fails or the response
                contains errors.
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
        yield from documents

    def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield documents from the GraphQL API in batches.

        For GraphQL, each response is treated as a batch.

        Args:
            batch_size: Maximum number of documents per batch.

        Yields:
            Lists of document dictionaries, each list containing at
            most ``batch_size`` items.

        Raises:
            DataSourceError: If the request fails or the response
                contains errors.
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
        """Yield documents changed since a timestamp (not implemented for GraphQL).

        Args:
            since: A timestamp or cursor value (accepted but ignored).

        Yields:
            Nothing — incremental changes are not supported for this
            data source.
        """
        return iter([])

    def document_count(self) -> int:
        """Return approximate document count.

        Executes the GraphQL query and counts the returned documents.

        Returns:
            The number of documents in the response.
        """
        return sum(1 for _ in self.iter_documents())

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this GraphQL source.

        Returns:
            A dictionary with keys ``type``, ``url``, ``query``,
            ``document_path``, and ``timeout``.
        """
        return {
            "type": "graphql",
            "url": self.url,
            "query": self.query,
            "document_path": self.document_path,
            "timeout": self.timeout,
        }
