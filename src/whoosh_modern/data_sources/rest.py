"""REST DataSource implementation with pagination and authentication."""

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Iterator, Mapping
from datetime import datetime
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.exceptions import DataSourceError
from whoosh_modern.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
MAX_PAGES = 1000

Document = Mapping[str, Any]

try:
    import requests as _requests

    class _HTTPClient:
        """HTTP client using the requests library."""

        def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
            self._session = _requests.Session()
            self._timeout = timeout

        def fetch(self, url: str, headers: dict[str, str]) -> dict[str, Any]:
            """Fetch a URL and return parsed JSON."""
            response = self._session.get(url, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

except ImportError:
    _HTTPClient = None  # type: ignore[assignment,misc]


class _UrllibHttpClient:
    """HTTP client using urllib.request as fallback."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def fetch(self, url: str, headers: dict[str, str]) -> dict[str, Any]:
        """Fetch a URL and return parsed JSON."""
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            result: dict[str, Any] = json.loads(response.read().decode("utf-8"))
            return result


def _get_http_client(timeout: int) -> Any:
    """Return the best available HTTP client."""
    if _HTTPClient is not None:
        return _HTTPClient(timeout)
    return _UrllibHttpClient(timeout)


class RESTSource:
    """REST API data source implementing the DataSource protocol."""

    def __init__(
        self,
        url: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: Any | None = None,
        pagination: str | None = None,
        page_size: int = 100,
        document_path: str | None = None,
        incremental_field: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.url = url
        self.method = method
        self.params = params or {}
        self.headers = headers or {}
        self.auth = auth
        self.pagination = pagination
        self.page_size = page_size
        self.document_path = document_path
        self.incremental_field = incremental_field
        self.timeout = timeout
        self._schema: Schema | None = None
        self._http_client = _get_http_client(timeout)
        self._total_count: int | None = None

    @property
    def name(self) -> str:
        """Return the data source name."""
        return f"rest:{self.url}"

    def discover_schema(self) -> Schema:
        """Discover schema from first page of results."""
        documents = list(self.iter_documents())
        if not documents:
            return Schema()
        self._schema = SchemaDiscovery.from_sample(documents)
        return self._schema

    def iter_documents(self) -> Iterator[Document]:
        """Yield documents from the REST API with pagination."""
        page = 1
        offset = 0
        cursor: str | None = None
        has_more = True
        pages_fetched = 0

        while has_more:
            pages_fetched += 1
            if pages_fetched > MAX_PAGES:
                logger.warning(
                    "RESTSource iter_documents hit max_pages=%d limit, stopping pagination for %s",
                    MAX_PAGES,
                    self.url,
                )
                break

            url = self._build_url(
                page=page,
                offset=offset,
                cursor=cursor,
            )

            try:
                data = self._http_client.fetch(url, self._get_headers())
            except Exception as e:
                from urllib.error import HTTPError, URLError

                if isinstance(e, (HTTPError, URLError)):
                    if isinstance(e, HTTPError) and e.code == 429:
                        retry_after = e.headers.get("Retry-After")
                        if retry_after:
                            import time

                            time.sleep(float(retry_after))
                            continue
                    raise DataSourceError(
                        f"REST API error: {e}",
                        source="rest",
                    ) from e
                raise DataSourceError(
                    f"Connection error: {e}",
                    source="rest",
                ) from e

            # Extract documents from response
            results: list[Any] = []
            if isinstance(data, dict):
                if self.document_path:
                    # Navigate nested JSON path
                    parts = self.document_path.split(".")
                    result: Any = data
                    for part in parts:
                        result = result.get(part, [])
                    results = result if isinstance(result, list) else []
                else:
                    raw_results = data.get("results") or data.get("data")
                    results = raw_results if isinstance(raw_results, list) else []
                # Try metadata-based count for document_count optimization
                if "total" in data and isinstance(data["total"], int):
                    self._total_count = data["total"]
            elif isinstance(data, list):
                results = data
            else:
                results = []

            if not results:
                has_more = False
                break

            yield from results

            # Pagination logic
            if self.pagination == "page":
                page += 1
                has_more = len(results) >= self.page_size
            elif self.pagination == "offset":
                offset += len(results)
                has_more = len(results) >= self.page_size
            elif self.pagination == "cursor":
                cursor = data.get("next_cursor") if isinstance(data, dict) else None
                has_more = cursor is not None
            else:
                has_more = False

    def document_count(self) -> int:
        """Return approximate document count."""
        # If we already know the total from metadata, use it
        if hasattr(self, "_total_count") and self._total_count is not None:
            return self._total_count
        # Fallback: iterate (but limit to avoid exhaustion)
        count = 0
        for _ in self.iter_documents():
            count += 1
            if count >= MAX_PAGES * self.page_size:
                break
        return count

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this REST source."""
        return {
            "type": "rest",
            "url": self.url,
            "method": self.method,
            "pagination": self.pagination,
            "page_size": self.page_size,
            "timeout": self.timeout,
        }

    def _build_url(
        self,
        page: int = 1,
        offset: int = 0,
        cursor: str | None = None,
    ) -> str:
        """Build URL with pagination parameters."""
        from urllib.parse import urlencode, urljoin

        url = self.url
        params: dict[str, Any] = {}

        if self.pagination == "page":
            params["page"] = page
            params["size"] = self.page_size
        elif self.pagination == "offset":
            params["offset"] = offset
            params["limit"] = self.page_size
        elif self.pagination == "cursor" and cursor is not None:
            params["cursor"] = cursor
            params["size"] = self.page_size

        if params:
            url = f"{url}?{urlencode(params)}"
        return url

    def _get_headers(self) -> dict[str, str]:
        """Build headers including auth."""
        result = dict(self.headers)

        if isinstance(self.auth, dict):
            if self.auth.get("type") == "bearer":
                result["Authorization"] = f"Bearer {self.auth.get('token')}"
            elif self.auth.get("type") == "basic":
                import base64

                creds = f"{self.auth.get('username')}:{self.auth.get('password')}"
                result["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"
            elif self.auth.get("api_key"):
                result["X-API-Key"] = self.auth["api_key"]

        return result
