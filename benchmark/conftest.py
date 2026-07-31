"""Shared fixtures and utilities for benchmark tests."""

import sqlite3
import tempfile
from collections.abc import Generator

import pytest


def create_test_db(num_rows: int = 1000) -> tuple[sqlite3.Connection, str]:
    """Create a temporary SQLite database with test data for benchmarks.

    Returns:
        Tuple of (connection, path) for the temporary database file.
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            description TEXT,
            active INTEGER,
            created_at TEXT,
            updated_at INTEGER
        )
        """
    )

    for i in range(1, num_rows + 1):
        cursor.execute(
            "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                i,
                f"Product {i}",
                f"Category {i % 10}",
                round(i * 1.5, 2),
                f"Description for product {i}",
                1 if i % 2 == 0 else 0,
                f"2025-01-{(i % 28) + 1:02d}",
                i,
            ),
        )

    conn.commit()
    return conn, path


@pytest.fixture
def temp_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provide a temporary database connection for benchmarks."""
    conn, path = create_test_db(1000)
    yield conn
    # Cleanup
    conn.close()
    import os

    os.unlink(path)
