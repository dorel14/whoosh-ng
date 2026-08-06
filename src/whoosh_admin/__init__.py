"""Admin UI plugin for Whoosh-NG.

Provides a management interface for index exploration and queries.
Consumes only public APIs (no direct access to internal core objects).
"""

from __future__ import annotations

from typing import Any

from whoosh.index import Index

try:
    from fastapi import FastAPI  # pyright: ignore[reportMissingImports]
    from fastapi.responses import HTMLResponse, JSONResponse  # pyright: ignore[reportMissingImports]

    def create_admin_app(index: Index, *, prefix: str = "/admin") -> FastAPI:
        """Create admin UI FastAPI application.

        :param index: An Index instance to manage
        :param prefix: API endpoint prefix
        :returns: Configured FastAPI application
        """
        app = FastAPI(title="Whoosh-NG Admin", version="4.0.0")

        @app.get(f"{prefix}/", response_class=HTMLResponse)
        async def index_page() -> str:
            return "<h1>Whoosh-NG Admin</h1>"

        @app.get(f"{prefix}/stats")
        async def stats() -> dict[str, Any]:
            with index.searcher() as searcher:
                return {
                    "index_stats": {
                        "doc_count": index.doc_count(),
                        "schema": list(index.schema.names()),
                    }
                }

        @app.get(f"{prefix}/explore")
        async def explore() -> dict[str, Any]:
            from whoosh.query import Every

            with index.searcher() as searcher:
                documents = []
                for hit in searcher.search(Every(), limit=100):
                    documents.append(dict(hit))
                return {"documents": documents}

        @app.get(f"{prefix}/schema")
        async def schema_explorer() -> dict[str, Any]:
            return {
                "fields": [
                    {"name": name, "type": str(field)}
                    for name, field in index.schema.items()
                ]
            }

        @app.post(f"{prefix}/query")
        async def query_playground(request: dict[str, Any]) -> dict[str, Any]:
            from whoosh.qparser import QueryParser

            query_string = request.get("q", "")
            field = request.get("field", index.schema.names()[0] if index.schema.names() else "content")
            parser = QueryParser(field, index.schema)
            query = parser.parse(query_string)
            with index.searcher() as searcher:
                results = searcher.search(query, limit=request.get("limit", 10))
                hits = [{"docnum": hit.docnum, "score": hit.score, "fields": dict(hit)} for hit in results]
                return {"hits": hits, "total": len(results)}

        @app.get(f"{prefix}/synonyms")
        async def synonym_manager() -> dict[str, Any]:
            from whoosh_modern.linguistics.synonyms.manager import SynonymManager

            manager = SynonymManager()
            word = "test"
            return {"word": word, "synonyms": manager.get_synonyms(word)}

        @app.post(f"{prefix}/synonyms")
        async def synonym_manager_add(request: dict[str, Any]) -> dict[str, Any]:
            from whoosh_modern.linguistics.synonyms.manager import SynonymManager

            manager = SynonymManager()
            word = request.get("word", "")
            synonyms = request.get("synonyms", [])
            manager.add_synonyms(word, synonyms)
            return {"status": "ok", "word": word, "synonyms": manager.get_synonyms(word)}

        return app

    __all__ = ["create_admin_app"]

except ImportError as exc:
    raise ImportError(
        "Admin plugin requires fastapi. Install with: pip install whoosh-ng[api]"
    ) from exc
