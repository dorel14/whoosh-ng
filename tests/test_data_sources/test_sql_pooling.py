"""Tests for SQLSource connection pooling."""

import sqlite3

import pytest

from whoosh_modern.data_sources.sql import SQLSource, _ConnectionPool


class TestConnectionPool:
    def test_acquire_returns_connection(self):
        conn = sqlite3.connect(":memory:")
        pool = _ConnectionPool(conn, max_size=2)
        result = pool.acquire()
        assert result is conn

    def test_release_returns_to_pool(self):
        conn = sqlite3.connect(":memory:")
        pool = _ConnectionPool(conn, max_size=2)
        pool.acquire()
        pool.release(conn)
        assert len(pool._available) == 1

    def test_max_size_respected(self):
        conn = sqlite3.connect(":memory:")
        pool = _ConnectionPool(conn, max_size=2)
        pool.acquire()
        pool.acquire()
        pool.release(conn)
        pool.release(conn)
        assert len(pool._available) == 2

    def test_close_all(self):
        conn = sqlite3.connect(":memory:")
        pool = _ConnectionPool(conn, max_size=2)
        pool.acquire()
        pool.release(conn)
        pool.close_all()
        assert len(pool._available) == 0


class TestSQLSourcePooling:
    def test_pool_size_parameter(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE articles (id INTEGER, title TEXT)")
        cursor.execute("INSERT INTO articles VALUES (1, 'Hello')")
        conn.commit()

        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            pool_size=3,
        )
        assert source.pool_size == 3

    def test_health_check(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE articles (id INTEGER, title TEXT)")
        cursor.execute("INSERT INTO articles VALUES (1, 'Hello')")
        conn.commit()

        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        assert source.health_check() is True
        conn.close()

    def test_health_check_closed_connection(self):
        conn = sqlite3.connect(":memory:")
        conn.close()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        assert source.health_check() is False

    def test_metadata_includes_pool_size(self):
        conn = sqlite3.connect(":memory:")
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            pool_size=10,
        )
        meta = source.metadata()
        assert meta["pool_size"] == 10
        conn.close()
