"""FastAPI plugin for Whoosh-NG.

Provides HTTP endpoints for search, autocomplete, and health checks.
"""

from __future__ import annotations

from typing import Any

from whoosh.index import Index

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse


    def create_app(index: Index, *, prefix: str = "/api/v1") -> FastAPI:
        """Create a FastAPI application for Whoosh-NG.

        :param index: An Index instance to expose via API
        :param prefix: API endpoint prefix (default: /api/v1)
        :returns: Configured FastAPI application
        """
        app = FastAPI(title="Whoosh-NG API", version="4.0.0")

        @app.get(f"{prefix}/health")
        async def health_check() -> dict[str, str]:
            return {"status": "ok"}

        @app.post(f"{prefix}/search")
        async def search_endpoint(query: dict[str, Any]) -> JSONResponse:
            q = query.get("q", "")
            kwargs = {k: v for k, v in query.items() if k != "q"}
            with index.searcher() as searcher:
                results = searcher.search(q, **kwargs)
                hits = [
                    {"docnum": hit.docnum, "score": hit.score, "fields": dict(hit)}
                    for hit in results
                ]
            return JSONResponse({"hits": hits, "total": len(results)})

        @app.get(f"{prefix}/autocomplete")
        async def autocomplete_endpoint(q: str) -> dict[str, Any]:
            suggestions: list[str] = []
            return {"suggestions": suggestions}

        return app

except ImportError as exc:
    raise ImportError(
        "FastAPI plugin requires fastapi. Install with: pip install whoosh-reloaded[api]"
    ) from exc


__all__ = ["create_app"]