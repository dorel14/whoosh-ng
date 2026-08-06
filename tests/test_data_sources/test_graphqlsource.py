"""Tests for GraphQLSource."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

import pytest

from whoosh_modern.data_sources.graphql import GraphQLSource
from whoosh_modern.exceptions import DataSourceError


class MockGraphQLHandler(BaseHTTPRequestHandler):
    """Mock GraphQL API handler for testing."""

    def do_POST(self):  # noqa: N802
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body)
        query = payload.get("query", "")
        response: dict[str, Any] = {}

        if "articles" in query:
            response = {
                "data": {
                    "articles": [
                        {"id": 1, "title": "Doc One", "cat": "tech"},
                        {"id": 2, "title": "Doc Two", "cat": "science"},
                    ]
                }
            }
        elif "products" in query:
            response = {
                "data": {
                    "products": [
                        {"id": 1, "name": "Laptop", "price": 999},
                    ]
                }
            }
        else:
            response = {"data": {"__typename": "Query"}}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def mock_graphql_server():
    """Start a mock GraphQL server for tests."""
    server = HTTPServer(("127.0.0.1", 18768), MockGraphQLHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


class TestGraphQLSource:
    def test_discover_schema(self, mock_graphql_server):
        source = GraphQLSource(
            url="http://127.0.0.1:18768/graphql",
            query="{ articles { id title cat } }",
            document_path="articles",
            timeout=5,
        )
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema
        assert "cat" in schema

    def test_iter_documents(self, mock_graphql_server):
        source = GraphQLSource(
            url="http://127.0.0.1:18768/graphql",
            query="{ articles { id title cat } }",
            document_path="articles",
            timeout=5,
        )
        docs = list(source.iter_documents())
        assert len(docs) == 2
        assert docs[0]["id"] == 1

    def test_document_count(self, mock_graphql_server):
        source = GraphQLSource(
            url="http://127.0.0.1:18768/graphql",
            query="{ articles { id title } }",
            document_path="articles",
            timeout=5,
        )
        count = source.document_count()
        assert count == 2

    def test_metadata(self, mock_graphql_server):
        source = GraphQLSource(
            url="http://127.0.0.1:18768/graphql",
            query="{ articles { id } }",
            document_path="articles",
            timeout=5,
        )
        meta = source.metadata()
        assert meta["type"] == "graphql"
        assert meta["url"] == "http://127.0.0.1:18768/graphql"

    def test_name_property(self, mock_graphql_server):
        source = GraphQLSource(
            url="http://127.0.0.1:18768/graphql",
            query="{ articles { id } }",
            document_path="articles",
            timeout=5,
        )
        assert source.name == "graphql:http://127.0.0.1:18768/graphql"

    def test_health_check_success(self, mock_graphql_server):
        source = GraphQLSource(
            url="http://127.0.0.1:18768/graphql",
            query="{ articles { id } }",
            document_path="articles",
            timeout=5,
        )
        assert source.health_check() is True

    def test_health_check_failure(self):
        source = GraphQLSource(
            url="http://127.0.0.1:99999/graphql",
            query="{ articles { id } }",
            document_path="articles",
            timeout=2,
        )
        assert source.health_check() is False

    def test_connection_error_raises(self):
        source = GraphQLSource(
            url="http://192.0.2.1:99999/graphql",
            query="{ articles { id } }",
            document_path="articles",
            timeout=2,
        )
        with pytest.raises(DataSourceError):
            list(source.iter_documents())
