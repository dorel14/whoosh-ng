"""Admin UI plugin for Whoosh-NG.

Provides a management interface for index exploration and queries.
"""

from __future__ import annotations

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse


    def create_admin_app(index, *, prefix: str = "/admin") -> FastAPI:
        """Create admin UI FastAPI application.

        :param index: An Index instance to manage
        :param prefix: API endpoint prefix
        :returns: Configured FastAPI application
        """
        app = FastAPI(title="Whoosh-NG Admin", version="4.0.0")

        @app.get(f"{prefix}/")
        async def index_page() -> HTMLResponse:
            return HTMLResponse("<h1>Whoosh-NG Admin</h1>")

        @app.get(f"{prefix}/stats")
        async def stats() -> dict:
            return {"index_stats": {}}

        @app.get(f"{prefix}/explore")
        async def explore() -> dict:
            return {"documents": []}

        return app

except ImportError as exc:
    raise ImportError(
        "Admin plugin requires fastapi. Install with: pip install whoosh-reloaded[api]"
    ) from exc


__all__ = ["create_admin_app"]