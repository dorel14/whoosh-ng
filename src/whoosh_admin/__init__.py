"""Admin UI plugin for Whoosh-NG.

Provides a management interface for index exploration and queries.
Consumes only public APIs (no direct access to internal core objects).

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.index import Index

try:
    from fastapi import FastAPI  # pyright: ignore[reportMissingImports]
    from fastapi.responses import HTMLResponse  # pyright: ignore[reportMissingImports]

    def create_admin_app(index: Index, *, prefix: str = "/admin") -> FastAPI:
        """Create the Admin UI FastAPI application.

        Builds and configures a FastAPI application that exposes endpoints for
        browsing the index schema, viewing statistics, exploring documents,
        executing ad-hoc queries, and managing synonyms.

        Args:
            index: An Index instance to manage.
            prefix: API endpoint prefix.

        Returns:
            A configured FastAPI application with admin routes registered.

        Raises:
            ImportError: If the ``fastapi`` package is not installed.
        """
        app = FastAPI(title="Whoosh-NG Admin", version="5.1.0")

        @app.get(f"{prefix}/", response_class=HTMLResponse)
        async def index_page() -> str:
            """Render the admin landing page.

            Returns:
                HTML string for the admin home page.
            """
            return "<h1>Whoosh-NG Admin</h1>"

        @app.get(f"{prefix}/stats")
        async def stats() -> dict[str, Any]:
            """Retrieve high-level index statistics.

            Returns:
                A dictionary containing the document count and a list of
                schema field names.
            """
            return {
                "index_stats": {
                    "doc_count": index.doc_count(),
                    "schema": list(index.schema.names()),
                }
            }

        @app.get(f"{prefix}/explore")
        async def explore() -> dict[str, Any]:
            """Browse documents in the index.

            Returns:
                A dictionary with up to 100 documents from the index.
            """
            from whoosh.query import Every

            with index.searcher() as searcher:
                documents = []
                for hit in searcher.search(Every(), limit=100):
                    documents.append(dict(hit))
                return {"documents": documents}

        @app.get(f"{prefix}/schema")
        async def schema_explorer() -> dict[str, Any]:
            """Inspect the index schema.

            Returns:
                A dictionary listing each field name and its type.
            """
            return {
                "fields": [
                    {"name": name, "type": str(field)} for name, field in index.schema.items()
                ]
            }

        @app.post(f"{prefix}/query")
        async def query_playground(request: dict[str, Any]) -> dict[str, Any]:
            """Execute a query against the index.

            Args:
                request: A dictionary with keys ``q`` (query string),
                    ``field`` (optional target field), and ``limit``
                    (optional maximum number of hits).

            Returns:
                A dictionary with matching hits (including docnum, score,
                and field values) and the total hit count.
            """
            from whoosh.qparser import QueryParser

            query_string = request.get("q", "")
            field = request.get(
                "field", index.schema.names()[0] if index.schema.names() else "content"
            )
            parser = QueryParser(field, index.schema)
            query = parser.parse(query_string)
            with index.searcher() as searcher:
                results = searcher.search(query, limit=request.get("limit", 10))
                hits = [
                    {"docnum": hit.docnum, "score": hit.score, "fields": dict(hit)}
                    for hit in results
                ]
                return {"hits": hits, "total": len(results)}

        @app.get(f"{prefix}/synonyms")
        async def synonym_manager() -> dict[str, Any]:
            """List synonyms for a default word.

            Returns:
                A dictionary with the queried word and its synonyms.
            """
            from whoosh_modern.linguistics.synonyms.manager import SynonymManager

            manager = SynonymManager()
            word = "test"
            return {"word": word, "synonyms": manager.get_synonyms(word)}

        @app.post(f"{prefix}/synonyms")
        async def synonym_manager_add(request: dict[str, Any]) -> dict[str, Any]:
            """Add synonyms for a given word.

            Args:
                request: A dictionary with keys ``word`` (the target word)
                    and ``synonyms`` (a list of synonyms to add).

            Returns:
                A dictionary confirming the operation and listing the
                updated synonyms for the word.
            """
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
