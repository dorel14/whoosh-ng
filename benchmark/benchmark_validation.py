"""Benchmarks for validation framework performance."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh.fields import NUMERIC, TEXT, Schema
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.validation import ValidationFramework, ValidationResult


def _create_test_schema() -> Schema:
    """Create a test Whoosh schema."""
    return Schema(
        id=NUMERIC(stored=True),
        title=TEXT(stored=True),
        content=TEXT(),
        price=NUMERIC(),
    )


def _create_test_source() -> SQLSource:
    """Create a test SQLSource for validation benchmarks."""
    import sqlite3
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".db")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE test (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            price REAL
        )
        """
    )
    for i in range(1, 11):
        cursor.execute(
            "INSERT INTO test VALUES (?, ?, ?, ?)",
            (i, f"Title {i}", f"Content {i}", i * 1.5),
        )
    conn.commit()
    conn.close()

    conn2 = sqlite3.connect(path)
    return SQLSource(connection=conn2, query="SELECT * FROM test")


class BenchmarkValidationFramework:
    """Benchmark suite for validation framework performance."""

    def setup_method(self):
        self.validator = ValidationFramework()
        self.schema = _create_test_schema()
        self.source = _create_test_source()

    def teardown_method(self):
        self.source.connection.close()

    def benchmark_validate_structural(self, benchmark):
        """Benchmark Level 1: Structural validation."""

        def _validate():
            return self.validator.validate_structural(self.source)

        result = benchmark(_validate)
        assert isinstance(result, list)

    def benchmark_validate_search(self, benchmark):
        """Benchmark Level 2: Search validation."""

        def _validate():
            return self.validator.validate_search(self.schema)

        result = benchmark(_validate)
        assert isinstance(result, list)

    def benchmark_validate_performance(self, benchmark):
        """Benchmark Level 3: Performance validation."""

        def _validate():
            return self.validator.validate_performance(self.schema, self.source)

        result = benchmark(_validate)
        assert isinstance(result, list)

    def benchmark_validate_runtime(self, benchmark):
        """Benchmark Level 4: Runtime validation."""

        def _validate():
            return self.validator.validate_runtime(self.source, sample_size=10)

        result = benchmark(_validate)
        assert isinstance(result, list)

    def benchmark_validate_all_levels(self, benchmark):
        """Benchmark full validation (all 4 levels)."""

        def _validate():
            return self.validator.validate(self.source)

        results = benchmark(_validate)
        assert len(results) == 4
        assert all(isinstance(r, ValidationResult) for r in results)

    def benchmark_validation_with_large_source(self, benchmark):
        """Benchmark validation on larger data source."""
        import sqlite3
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".db")
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE large (
                id INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT
            )
            """
        )
        for i in range(1, 1001):
            cursor.execute(
                "INSERT INTO large VALUES (?, ?, ?)",
                (i, f"Title {i}", f"Content {i}"),
            )
        conn.commit()
        conn.close()

        large_conn = sqlite3.connect(path)
        large_source = SQLSource(connection=large_conn, query="SELECT * FROM large")

        def _validate():
            return self.validator.validate(large_source)

        results = benchmark(_validate)
        assert len(results) == 4

        large_conn.close()
        import os

        os.unlink(path)


class BenchmarkValidationEdgeCases:
    """Benchmark edge cases for validation."""

    def setup_method(self):
        self.validator = ValidationFramework()
        self.schema = _create_test_schema()
        self.source = _create_test_source()

    def teardown_method(self):
        self.source.connection.close()

    def benchmark_validate_empty_source(self, benchmark):
        """Benchmark validation on empty source."""
        import sqlite3
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".db")
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE empty (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        empty_conn = sqlite3.connect(path)
        empty_source = SQLSource(connection=empty_conn, query="SELECT * FROM empty")

        def _validate():
            return self.validator.validate(empty_source)

        results = benchmark(_validate)
        assert len(results) == 4

        empty_conn.close()
        import os

        os.unlink(path)

    def benchmark_validate_multiple_times(self, benchmark):
        """Benchmark multiple validation runs on same source."""

        def _validate():
            return self.validator.validate(self.source)

        for _ in range(5):
            results = benchmark(_validate)
            assert len(results) == 4
