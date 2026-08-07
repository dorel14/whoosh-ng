"""FastAPI plugin for Whoosh-NG.

Provides HTTP endpoints for search, autocomplete, suggest, health, and metrics.
All blocking core calls are executed off the event loop via
:func:`whoosh.utils.async_utils.run_sync` so the async server stays responsive.
"""

from __future__ import annotations

from typing import Any

from whoosh.index import Index
from whoosh.utils.async_utils import run_sync

try:
    from fastapi import FastAPI  # pyright: ignore[reportMissingImports]
    from pydantic import BaseModel  # pyright: ignore[reportMissingImports]

    class SearchRequest(BaseModel):
        """Request model for search endpoint."""

        q: str
        limit: int = 10
        offset: int = 0

    class SearchResponse(BaseModel):
        """Response model for search endpoint."""

        hits: list[dict[str, Any]]
        total: int
        limit: int
        offset: int

    class AutocompleteResponse(BaseModel):
        """Response model for autocomplete endpoint."""

        suggestions: list[str]

    class HealthResponse(BaseModel):
        """Response model for health endpoint."""

        status: str

    def _run_search(index: Index, query: str, **kwargs: Any) -> tuple[list[dict[str, Any]], int]:
        from whoosh.qparser import QueryParser

        with index.searcher() as searcher:
            default_field = index.schema.names()[0] if index.schema.names() else "content"
            parser = QueryParser(default_field, index.schema)
            parsed_query = parser.parse(query)
            results = searcher.search(parsed_query, **kwargs)
            hits = [
                {"docnum": hit.docnum, "score": hit.score, "fields": dict(hit)} for hit in results
            ]
            return hits, len(results)

    def create_app(
        index: Index,
        *,
        prefix: str = "/api/v1",
        autocomplete: Any = None,
    ) -> FastAPI:
        """Create a FastAPI application for Whoosh-NG.

        :param index: An Index instance to expose via API
        :param prefix: API endpoint prefix (default: /api/v1)
        :param autocomplete: Optional AutocompleteProvider for the autocomplete endpoint
        :returns: Configured FastAPI application
        """
        app = FastAPI(title="Whoosh-NG API", version="4.2.0")

        @app.get(f"{prefix}/health", response_model=HealthResponse)
        async def health_check() -> dict[str, str]:
            return {"status": "ok"}

        @app.post(f"{prefix}/search", response_model=SearchResponse)
        async def search_endpoint(request: SearchRequest) -> dict[str, Any]:
            kwargs: dict[str, Any] = {"limit": request.limit}
            hits, total = await run_sync(_run_search, index, request.q, **kwargs)
            return {"hits": hits, "total": total, "limit": request.limit, "offset": request.offset}

        @app.get(f"{prefix}/autocomplete", response_model=AutocompleteResponse)
        async def autocomplete_endpoint(q: str) -> dict[str, Any]:
            if autocomplete is None:
                return {"suggestions": []}
            hits = autocomplete.search(q, limit=10)
            return {"suggestions": [hit.text for hit in hits]}

        @app.get(f"{prefix}/suggest")
        async def suggest_endpoint(q: str) -> dict[str, Any]:
            try:
                with index.searcher() as searcher:
                    fieldname = index.schema.names()[0] if index.schema.names() else "content"
                    suggestions = searcher.suggest(fieldname, q)
                    return {"suggestions": suggestions}
            except Exception:
                return {"suggestions": []}

        return app

    def mount(app: FastAPI, index: Index, *, prefix: str = "/api/v1") -> None:
        """Mount Whoosh-NG API routes onto an existing FastAPI application.

        :param app: Existing FastAPI application
        :param index: Index instance to expose
        :param prefix: API endpoint prefix (default: /api/v1)
        """
        api_app = create_app(index, prefix=prefix)
        app.mount(prefix, api_app)

except ImportError as exc:
    raise ImportError(
        "FastAPI plugin requires fastapi. Install with: pip install whoosh-ng[api]"
    ) from exc


__all__ = [
    "create_app",
    "mount",
    "SearchRequest",
    "SearchResponse",
    "AutocompleteResponse",
    "HealthResponse",
]
