"""FastAPI plugin for Whoosh-NG.

Provides HTTP endpoints for search, autocomplete, suggest, health, and metrics.
All blocking core calls are executed off the event loop via
:func:`whoosh.utils.async_utils.run_sync` so the async server stays responsive.

This module is part of the optional ``api`` extra. ``fastapi`` and ``pydantic``
are **not** installed by default. The ``try/except ImportError`` guard ensures
that importing ``whoosh_fastapi`` without the extra produces a clear error
message pointing to ``pip install whoosh-ng[api]``. This keeps the core
``whoosh``/``whoosh_modern`` packages free of mandatory ASG/HTTP dependencies.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any

from whoosh.index import Index
from whoosh.utils.async_utils import run_sync

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from pydantic import BaseModel

    class SearchRequest(BaseModel):
        """Request model for search endpoint.

        Attributes:
            q: The search query string.
            limit: Maximum number of hits to return.
            offset: Number of initial hits to skip.
        """

        q: str
        limit: int = 10
        offset: int = 0

    class SearchResponse(BaseModel):
        """Response model for search endpoint.

        Attributes:
            hits: List of matching document hits.
            total: Total number of matching documents.
            limit: Maximum number of hits requested.
            offset: Number of hits skipped.
        """

        hits: list[dict[str, Any]]
        total: int
        limit: int
        offset: int

    class AutocompleteResponse(BaseModel):
        """Response model for autocomplete endpoint.

        Attributes:
            suggestions: List of autocomplete suggestion strings.
        """

        suggestions: list[str]

    class HealthResponse(BaseModel):
        """Response model for health endpoint.

        Attributes:
            status: Current service health status.
        """

        status: str

    def _run_search(index: Index, query: str, **kwargs: Any) -> tuple[list[dict[str, Any]], int]:
        """Execute a Whoosh search query and return hits with total count.

        Args:
            index: An open Whoosh Index instance to search.
            query: The query string to parse and execute.
            **kwargs: Additional keyword arguments forwarded to the searcher
                (e.g. ``limit``, ``offset``).

        Returns:
            A tuple of ``(hits, total)`` where ``hits`` is a list of dicts
            containing ``docnum``, ``score``, and ``fields`` keys, and
            ``total`` is the total number of matching documents.
        """
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

        Args:
            index: An Index instance to expose via API.
            prefix: API endpoint prefix (default: ``/api/v1``).
            autocomplete: Optional AutocompleteProvider for the autocomplete
                endpoint.

        Returns:
            A configured FastAPI application with search, autocomplete,
            suggest, and health routes mounted under the given prefix.
        """
        app = FastAPI(title="Whoosh-NG API", version="5.0.0")

        @app.get(f"{prefix}/health", response_model=HealthResponse)
        async def health_check() -> dict[str, str]:
            """Health check endpoint.

            summary: Health Check
            description: Returns the current health status of the Whoosh-NG API service.
            """
            return {"status": "ok"}

        @app.post(f"{prefix}/search", response_model=SearchResponse)
        async def search_endpoint(request: SearchRequest) -> dict[str, Any]:
            """Search endpoint.

            summary: Search
            description: Executes a search query against the configured Whoosh-NG
                index and returns matching documents with scores and total count.
            """
            kwargs: dict[str, Any] = {"limit": request.limit}
            hits, total = await run_sync(_run_search, index, request.q, **kwargs)
            return {"hits": hits, "total": total, "limit": request.limit, "offset": request.offset}

        @app.get(f"{prefix}/autocomplete", response_model=AutocompleteResponse)
        async def autocomplete_endpoint(q: str) -> dict[str, Any]:
            """Autocomplete endpoint.

            summary: Autocomplete
            description: Returns autocomplete suggestions for the given query
                prefix using the configured AutocompleteProvider.
            """
            if autocomplete is None:
                return {"suggestions": []}
            hits = autocomplete.search(q, limit=10)
            return {"suggestions": [hit.text for hit in hits]}

        @app.websocket(f"{prefix}/autocomplete/ws")
        async def autocomplete_ws(websocket: WebSocket) -> None:
            """WebSocket autocomplete endpoint.

            Accepts persistent WebSocket connections. The client sends JSON
            payloads with a ``q`` key containing the query prefix, and the
            server responds with JSON payloads containing a ``suggestions``
            list.

            Example client message::

                {"q": "pyth"}

            Example client message with custom limit::

                {"q": "pyth", "limit": 5}

            Example server response::

                {"suggestions": ["python", "pythagorean"]}
            """
            await websocket.accept()
            try:
                while True:
                    payload = await websocket.receive_json()
                    query = payload.get("q", "")
                    limit_raw = payload.get("limit", 10)
                    try:
                        limit = int(limit_raw)
                    except (TypeError, ValueError):
                        logger.warning("Invalid 'limit' value in WebSocket: %s", limit_raw)
                        await websocket.send_json(
                            {"error": "Invalid 'limit' value. Must be an integer."}
                        )
                        continue
                    if autocomplete is None:
                        await websocket.send_json({"suggestions": []})
                    else:
                        hits = await run_sync(autocomplete.search, query, limit=limit)
                        await websocket.send_json({"suggestions": [hit.text for hit in hits]})
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected from autocomplete.")
            except Exception as exc:  # pragma: no cover - safety net
                logger.error("Unexpected error in autocomplete WebSocket: %s", exc, exc_info=True)
                with suppress(RuntimeError):
                    await websocket.send_json({"error": "Internal server error"})

        @app.get(f"{prefix}/suggest")
        async def suggest_endpoint(q: str) -> dict[str, Any]:
            """Suggest endpoint.

            summary: Suggest
            description: Returns spelling suggestions for the given query term
                using the Whoosh-NG spell-checker.
            """
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

        Args:
            app: Existing FastAPI application to mount routes on.
            index: Index instance to expose via the mounted routes.
            prefix: API endpoint prefix (default: ``/api/v1``).
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
