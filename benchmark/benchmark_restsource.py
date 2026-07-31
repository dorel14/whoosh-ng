"""Benchmarks for RESTSource data source indexing performance using real Reuters data."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.data_sources.rest import RESTSource

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
REUTERS_PATH = os.path.join(BENCHMARK_DIR, "reuters21578.txt")


def _load_reuters_documents() -> list[dict[str, Any]]:
    """Load real Reuters documents from the benchmark corpus."""
    documents: list[dict[str, Any]] = []
    with open(REUTERS_PATH, encoding="latin-1") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) < 2:
                continue
            article_date = parts[0].strip()
            body = parts[1].strip()
            documents.append(
                {
                    "id": idx + 1,
                    "article_date": article_date,
                    "headline": body[:70].replace("\n", " "),
                    "body": body,
                    "word_count": len(body.split()),
                }
            )
    return documents


class ReutersAPIHandler(BaseHTTPRequestHandler):
    """Mock REST API serving real Reuters documents."""

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        limit = min(int(params.get("limit", [50])[0]), len(_reuters_docs))
        offset = int(params.get("offset", [0])[0])
        page = int(params.get("page", [1])[0])

        start = offset if "offset" in params else (page - 1) * limit
        end = min(start + limit, len(_reuters_docs))
        data = _reuters_docs[start:end]

        response = {
            "results": data,
            "total": len(_reuters_docs),
            "next_cursor": str(end) if end < len(_reuters_docs) else None,
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass


_reuters_docs: list[dict[str, Any]] = []


def _ensure_docs_loaded() -> None:
    global _reuters_docs
    if not _reuters_docs:
        _reuters_docs = _load_reuters_documents()


@pytest.fixture(scope="module")
def mock_reuters_server():
    """Start a mock HTTP server serving real Reuters documents."""
    _ensure_docs_loaded()
    server = HTTPServer(("localhost", 18766), ReutersAPIHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


class BenchmarkRESTSource:
    """Benchmark suite for RESTSource using real Reuters data."""

    def setup_method(self):
        self.source = RESTSource(
            url="http://localhost:18766/api/v2/reuters",
            pagination="page",
            page_size=50,
        )

    def benchmark_page_pagination(self, benchmark, mock_reuters_server):
        """Benchmark page-based pagination over real Reuters data."""
        source = RESTSource(
            url="http://localhost:18766/api/v2/reuters",
            pagination="page",
            page_size=50,
        )

        def _paginate():
            return list(source.iter_documents())

        results = benchmark(_paginate)
        assert len(results) > 0

    def benchmark_offset_pagination(self, benchmark, mock_reuters_server):
        """Benchmark offset-based pagination over real Reuters data."""
        source = RESTSource(
            url="http://localhost:18766/api/v2/reuters",
            pagination="offset",
            page_size=50,
        )

        def _paginate():
            return list(source.iter_documents())

        results = benchmark(_paginate)
        assert len(results) > 0

    def benchmark_cursor_pagination(self, benchmark, mock_reuters_server):
        """Benchmark cursor-based pagination over real Reuters data."""
        source = RESTSource(
            url="http://localhost:18766/api/v2/reuters",
            pagination="cursor",
            page_size=50,
        )

        def _paginate():
            return list(source.iter_documents())

        results = benchmark(_paginate)
        assert len(results) > 0

    def benchmark_discover_schema(self, benchmark, mock_reuters_server):
        """Benchmark schema discovery from real Reuters results."""

        def _discover():
            return self.source.discover_schema()

        schema = benchmark(_discover)
        assert schema is not None

    def benchmark_document_count(self, benchmark, mock_reuters_server):
        """Benchmark document count."""

        def _count():
            return self.source.document_count()

        count = benchmark(_count)
        assert count > 0

    def benchmark_metadata(self, benchmark, mock_reuters_server):
        """Benchmark metadata retrieval."""

        def _meta():
            return self.source.metadata()

        meta = benchmark(_meta)
        assert meta["type"] == "rest"

    def benchmark_authentication_headers(self, benchmark, mock_reuters_server):
        """Benchmark REST source with authentication headers."""
        source = RESTSource(
            url="http://localhost:18766/api/v2/reuters",
            headers={"Authorization": "Bearer test_token"},
            pagination="page",
            page_size=50,
        )

        def _auth_query():
            return list(source.iter_documents())

        results = benchmark(_auth_query)
        assert len(results) > 0

    def benchmark_indexing_reuters(self, benchmark, mock_reuters_server):
        """Benchmark full indexing of Reuters articles via REST source."""
        import shutil

        from whoosh import fields, index
        from whoosh.analysis import StandardAnalyzer

        idx_dir = os.path.join(BENCHMARK_DIR, "indexes", "rest_reuters_index")
        if os.path.exists(idx_dir):
            shutil.rmtree(idx_dir)
        os.makedirs(idx_dir, exist_ok=True)

        schema = fields.Schema(
            id=fields.ID(stored=True),
            article_date=fields.TEXT(stored=True),
            headline=fields.TEXT(stored=True),
            body=fields.TEXT(analyzer=StandardAnalyzer(), stored=True),
        )
        schema_fields = set(schema.names())

        def _index():
            ix = index.create_in(idx_dir, schema)
            writer = ix.writer()
            count = 0
            for doc in self.source.iter_documents():
                filtered = {
                    k: str(v) if k == "id" else v for k, v in doc.items() if k in schema_fields
                }
                writer.add_document(**filtered)
                count += 1
            writer.commit()
            ix.close()
            return count

        count = benchmark(_index)
        assert count > 0

    def benchmark_search(self, benchmark, mock_reuters_server):
        """Benchmark search over REST-source-indexed data."""
        import shutil

        from whoosh import index, qparser

        idx_dir = os.path.join(BENCHMARK_DIR, "indexes", "rest_search_index")
        if os.path.exists(idx_dir):
            shutil.rmtree(idx_dir)
        os.makedirs(idx_dir, exist_ok=True)

        schema = self.source.discover_schema()
        ix = index.create_in(idx_dir, schema)
        writer = ix.writer()
        for doc in self.source.iter_documents():
            writer.add_document(**doc)
        writer.commit()
        ix.close()

        def _search():
            ix2 = index.open_dir(idx_dir)
            searcher = ix2.searcher()
            parser = qparser.QueryParser("headline", schema=ix2.schema)
            q = parser.parse("reuters")
            results = searcher.search(q, limit=10)
            searcher.close()
            ix2.close()
            return len(results)

        count = benchmark(_search)
        assert count >= 0
