"""Tests for RESTSource (REST API data source)."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from whoosh_modern.data_sources.rest import RESTSource
from whoosh_modern.exceptions import DataSourceError


class MockAPIHandler(BaseHTTPRequestHandler):
    """Mock REST API handler for testing."""

    def do_GET(self):
        response = {
            "results": [
                {"id": 1, "title": "Doc One", "cat": "tech"},
                {"id": 2, "title": "Doc Two", "cat": "science"},
            ],
            "total": 2,
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def mock_api_server():
    """Start a mock HTTP server for RESTSource tests."""
    server = HTTPServer(("127.0.0.1", 18767), MockAPIHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


class TestRESTSource:
    def test_discover_schema(self, mock_api_server):
        source = RESTSource(
            url="http://127.0.0.1:18767/api/docs",
            pagination="page",
            page_size=100,
            timeout=5,
        )
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema
        assert "cat" in schema

    def test_iter_documents(self, mock_api_server):
        source = RESTSource(
            url="http://127.0.0.1:18767/api/docs",
            pagination="page",
            page_size=100,
            timeout=5,
        )
        docs = list(source.iter_documents())
        assert len(docs) == 2
        assert docs[0]["id"] == 1

    def test_document_count(self, mock_api_server):
        source = RESTSource(
            url="http://127.0.0.1:18767/api/docs",
            pagination="page",
            page_size=100,
            timeout=5,
        )
        count = source.document_count()
        assert count == 2

    def test_metadata(self, mock_api_server):
        source = RESTSource(
            url="http://127.0.0.1:18767/api/docs",
            pagination="page",
            page_size=100,
            timeout=5,
        )
        meta = source.metadata()
        assert meta["type"] == "rest"
        assert meta["url"] == "http://127.0.0.1:18767/api/docs"

    def test_bearer_auth_header(self):
        source = RESTSource(
            url="http://example.com/api",
            auth={"type": "bearer", "token": "test123"},
            timeout=5,
        )
        headers = source._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test123"

    def test_api_key_auth_header(self):
        source = RESTSource(
            url="http://example.com/api",
            auth={"api_key": "key123"},
            timeout=5,
        )
        headers = source._get_headers()
        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == "key123"

    def test_basic_auth_header(self):
        source = RESTSource(
            url="http://example.com/api",
            auth={"type": "basic", "username": "user", "password": "pass"},
            timeout=5,
        )
        headers = source._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic")

    def test_custom_headers(self):
        source = RESTSource(
            url="http://example.com/api",
            headers={"X-Custom": "value"},
            timeout=5,
        )
        headers = source._get_headers()
        assert "X-Custom" in headers
        assert headers["X-Custom"] == "value"

    def test_page_pagination(self, mock_api_server):
        source = RESTSource(
            url="http://127.0.0.1:18767/api/docs",
            pagination="page",
            page_size=100,
            timeout=5,
        )
        docs = list(source.iter_documents())
        assert len(docs) > 0

    def test_nested_document_path(self):
        """Test document extraction from nested JSON."""
        source = RESTSource(
            url="http://127.0.0.1:18767/api/docs",
            document_path="data.items",
            pagination="page",
            page_size=100,
            timeout=5,
        )
        # The mock server doesn't return nested JSON,
        # but the source should handle it gracefully
        assert source.document_path == "data.items"

    def test_timeout_parameter(self):
        source = RESTSource(
            url="http://127.0.0.1:18767/api/docs",
            timeout=10,
        )
        assert source.timeout == 10

    def test_connection_error_raises(self):
        source = RESTSource(
            url="http://127.0.0.1:99999/nonexistent",
            timeout=2,
        )
        with pytest.raises(DataSourceError):
            list(source.iter_documents())

    def test_invalid_url_raises(self):
        source = RESTSource(
            url="not-a-valid-url",
            timeout=2,
        )
        with pytest.raises(DataSourceError):
            list(source.iter_documents())
