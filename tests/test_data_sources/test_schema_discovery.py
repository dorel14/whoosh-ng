"""Tests for SchemaDiscovery."""

import pytest

from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, TEXT, Schema
from whoosh_modern.exceptions import SchemaDiscoveryError
from whoosh_modern.schema_discovery import SchemaDiscovery


class TestSchemaDiscoveryFromResultSet:
    def test_basic_column_mapping(self):
        columns = [
            ("id", "INTEGER"),
            ("title", "VARCHAR"),
            ("score", "FLOAT"),
        ]
        schema = SchemaDiscovery.from_result_set(columns)
        assert "id" in schema
        assert "title" in schema
        assert "score" in schema

    def test_text_types_map_to_text(self):
        for sql_type in ("VARCHAR", "TEXT", "CHAR"):
            columns = [("col", sql_type)]
            schema = SchemaDiscovery.from_result_set(columns)
            assert isinstance(schema["col"], TEXT)

    def test_numeric_types_map_to_numeric(self):
        for sql_type in ("INTEGER", "BIGINT", "SMALLINT", "FLOAT", "DOUBLE"):
            columns = [("col", sql_type)]
            schema = SchemaDiscovery.from_result_set(columns)
            assert isinstance(schema["col"], NUMERIC)

    def test_boolean_maps_to_boolean(self):
        columns = [("flag", "BOOLEAN")]
        schema = SchemaDiscovery.from_result_set(columns)
        assert isinstance(schema["flag"], BOOLEAN)

    def test_uuid_maps_to_id(self):
        columns = [("uuid", "UUID")]
        schema = SchemaDiscovery.from_result_set(columns)
        assert isinstance(schema["uuid"], ID)

    def test_json_maps_to_keyword(self):
        columns = [("data", "JSON")]
        schema = SchemaDiscovery.from_result_set(columns)
        assert isinstance(schema["data"], KEYWORD)

    def test_aggregate_types_map_to_numeric(self):
        for sql_type in ("COUNT", "SUM", "AVG", "MIN", "MAX"):
            columns = [("col", sql_type)]
            schema = SchemaDiscovery.from_result_set(columns)
            assert isinstance(schema["col"], NUMERIC)

    def test_string_agg_maps_to_text(self):
        columns = [["name", "STRING_AGG"]]
        schema = SchemaDiscovery.from_result_set(columns)
        assert isinstance(schema["name"], TEXT)

    def test_unknown_type_defaults_to_text(self):
        columns = [["col", "UNKNOWN_TYPE"]]
        schema = SchemaDiscovery.from_result_set(columns)
        assert isinstance(schema["col"], TEXT)

    def test_duplicate_column_raises(self):
        columns = [
            ("id", "INTEGER"),
            ("id", "TEXT"),
        ]
        with pytest.raises(SchemaDiscoveryError) as exc_info:
            SchemaDiscovery.from_result_set(columns)
        assert "Duplicate column name" in str(exc_info.value)
        assert exc_info.value.field == "id"

    def test_empty_columns_returns_empty_schema(self):
        schema = SchemaDiscovery.from_result_set([])
        assert len(schema) == 0


class TestSchemaDiscoveryFromSample:
    def test_infer_string_field(self):
        docs = [{"title": "Hello World"}]
        schema = SchemaDiscovery.from_sample(docs)
        assert isinstance(schema["title"], TEXT)

    def test_infer_int_field(self):
        docs = [{"count": 42}]
        schema = SchemaDiscovery.from_sample(docs)
        assert isinstance(schema["count"], NUMERIC)

    def test_infer_float_field(self):
        docs = [{"score": 3.14}]
        schema = SchemaDiscovery.from_sample(docs)
        assert isinstance(schema["score"], NUMERIC)

    def test_infer_bool_field(self):
        docs = [{"active": True}]
        schema = SchemaDiscovery.from_sample(docs)
        assert isinstance(schema["active"], BOOLEAN)

    def test_infer_dict_field(self):
        docs = [{"meta": {"key": "value"}}]
        schema = SchemaDiscovery.from_sample(docs)
        assert isinstance(schema["meta"], KEYWORD)

    def test_infer_list_field(self):
        docs = [{"tags": ["a", "b"]}]
        schema = SchemaDiscovery.from_sample(docs)
        assert isinstance(schema["tags"], KEYWORD)

    def test_multiple_documents_majority_type(self):
        docs = [
            {"value": 1},
            {"value": 2},
            {"value": "string"},
            {"value": "also string"},
            {"value": "string again"},
        ]
        schema = SchemaDiscovery.from_sample(docs)
        assert isinstance(schema["value"], TEXT)

    def test_empty_documents_returns_empty_schema(self):
        schema = SchemaDiscovery.from_sample([])
        assert len(schema) == 0

    def test_null_values(self):
        docs = [{"name": None}]
        schema = SchemaDiscovery.from_sample(docs)
        assert "name" in schema


class TestSchemaDiscoveryDetectIdField:
    def test_detects_id_field(self):
        schema = Schema(id=ID(stored=True), title=TEXT())
        result = SchemaDiscovery.detect_id_field(schema)
        assert result == "id"

    def test_no_id_field_returns_none(self):
        schema = Schema(title=TEXT(), count=NUMERIC())
        result = SchemaDiscovery.detect_id_field(schema)
        assert result is None
