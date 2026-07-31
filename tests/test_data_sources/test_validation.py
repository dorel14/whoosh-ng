"""Tests for ValidationFramework."""

import os
import sqlite3
import tempfile
from tempfile import NamedTemporaryFile

import pytest

from whoosh.fields import ID, KEYWORD, NUMERIC, STORED, TEXT, Schema
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.validation import (
    ValidationFramework,
    ValidationResult,
)


def _create_test_source():
    """Create a test SQLSource for validation tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE test (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            price REAL,
            is_active BOOLEAN
        )
        """
    )
    for i in range(1, 11):
        cursor.execute(
            "INSERT INTO test VALUES (?, ?, ?, ?, ?)",
            (i, f"Title {i}", f"Content {i}", i * 1.5, i % 2 == 0),
        )
    conn.commit()
    conn.close()
    conn2 = sqlite3.connect(path)
    source = SQLSource(connection=conn2, query="SELECT * FROM test", id_field="id")
    return source, path


class TestValidationFramework:
    def test_validate_structural_valid(self):
        source, path = _create_test_source()
        try:
            validator = ValidationFramework()
            errors = validator.validate_structural(source)
            assert isinstance(errors, list)
        finally:
            source.connection.close()
            import os

            os.unlink(path)

    def test_validate_search(self):
        schema = Schema(
            id=ID(stored=True),
            title=TEXT(stored=True),
            content=TEXT(analyzer="standard"),
            price=NUMERIC(stored=True),
        )
        validator = ValidationFramework()
        errors = validator.validate_search(schema)
        assert isinstance(errors, list)

    def test_validate_performance(self):
        schema = Schema(
            title=TEXT(stored=True),
            price=NUMERIC(stored=True),
        )
        validator = ValidationFramework()
        warnings = validator.validate_performance(schema, None)
        assert isinstance(warnings, list)

    def test_validate_runtime_valid(self):
        source, path = _create_test_source()
        try:
            validator = ValidationFramework()
            errors = validator.validate_runtime(source, sample_size=5)
            assert isinstance(errors, list)
        finally:
            source.connection.close()
            import os

            os.unlink(path)

    def test_validate_all_levels(self):
        source, path = _create_test_source()
        try:
            validator = ValidationFramework()
            results = validator.validate(source)
            assert len(results) == 4
            assert all(isinstance(r, ValidationResult) for r in results)
            levels = [r.level for r in results]
            assert levels == [1, 2, 3, 4]
        finally:
            source.connection.close()
            import os

            os.unlink(path)

    def test_result_passed_boolean(self):
        result = ValidationResult(level=1, passed=True)
        assert result.passed is True

    def test_result_with_errors(self):
        result = ValidationResult(
            level=1,
            passed=False,
            errors=["some error"],
        )
        assert result.passed is False
        assert len(result.errors) == 1

    def test_result_with_warnings(self):
        result = ValidationResult(
            level=3,
            passed=True,
            warnings=["some warning"],
        )
        assert len(result.warnings) == 1

    def test_validate_structural_with_bad_source(self):
        class BadSource:
            def discover_schema(self):
                raise RuntimeError("connection failed")

        validator = ValidationFramework()
        errors = validator.validate_structural(BadSource())
        assert len(errors) > 0
        assert "connection failed" in errors[0]

    def test_validate_runtime_type_checking(self):
        source, path = _create_test_source()
        try:
            schema = source.discover_schema()
            validator = ValidationFramework()
            errors = validator.validate_runtime(source, schema=schema, sample_size=3)
            assert isinstance(errors, list)
        finally:
            source.connection.close()
            import os

            os.unlink(path)
