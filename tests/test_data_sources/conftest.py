"""Shared fixtures for data source tests."""

import sqlite3
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

import pytest

from whoosh.fields import ID, KEYWORD, NUMERIC, TEXT, Schema
from whoosh_modern.data_sources.rest import RESTSource
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.exceptions import DataSourceError, SchemaDiscoveryError
from whoosh_modern.middleware import LoggingMiddleware, MiddlewarePipeline, RetryMiddleware
from whoosh_modern.validation import ValidationFramework


@pytest.fixture
def sqlite_conn():
    """Return an in-memory SQLite connection with test data."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT,
            category TEXT,
            weight REAL,
            is_published BOOLEAN,
            created_at TEXT
        )
        """
    )
    cursor.executemany(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "Hello World", "This is a test article.", "tech", 1.5, 1, "2024-01-01"),
            (2, "Python Tips", "Useful Python tips.", "tech", 2.0, 1, "2024-01-15"),
            (3, "Search Engines", "How search engines work.", "science", 3.5, 0, "2024-02-01"),
            (4, "Data Sources", "Connecting to data sources.", "tech", 1.0, 1, "2024-03-01"),
            (
                5,
                "Faceted Search",
                "Faceted search implementations.",
                "science",
                4.0,
                0,
                "2024-03-15",
            ),
        ],
    )
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def sql_source(sqlite_conn):
    """Return a SQLSource pointing to the test articles table."""
    return SQLSource(
        connection=sqlite_conn,
        query="SELECT * FROM articles",
        incremental_field="created_at",
        id_field="id",
    )


@pytest.fixture
def mock_http_handler():
    """Create a simple mock HTTP handler for RESTSource tests."""
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from threading import Thread

    _docs = [
        {"id": 1, "title": "Test Doc", "category": "tech", "weight": 1.5},
        {"id": 2, "title": "Another Doc", "category": "science", "weight": 2.0},
    ]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            import json

            response = {
                "results": _docs,
                "total": len(_docs),
            }
            self.wfile.write(json.dumps(response).encode())

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 18765), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


@pytest.fixture
def rest_source(mock_http_handler):
    """Return a RESTSource pointing to the mock server."""
    return RESTSource(
        url="http://127.0.0.1:18765/api/docs",
        pagination="page",
        page_size=100,
        timeout=5,
    )
