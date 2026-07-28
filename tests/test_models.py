from __future__ import annotations

import dataclasses
from typing import Optional

import pytest

from whoosh.fields import NUMERIC, TEXT, Schema
from whoosh_modern.models import ModelIndex, SearchField, SearchOptions, TypeMapper


def test_search_options_defaults():
    opts = SearchOptions()
    assert opts.fulltext is False
    assert opts.stored is False
    assert opts.sortable is False
    assert opts.faceted is False
    assert opts.id is False
    assert opts.multi is False
    assert opts.nullable is False
    assert opts.analyzer == ""
    assert opts.unique is False


def test_search_field_descriptor():
    class Book:
        title: str = SearchField(fulltext=True, stored=True)

    assert isinstance(Book.title, SearchField)
    assert Book.title.options.fulltext is True
    assert Book.title.options.stored is True


def test_type_mapper_registration():
    mapper = TypeMapper()
    opts = SearchOptions(stored=True)

    field = mapper.map(str, opts)
    assert field is not None


def test_model_index_dataclass():
    @dataclasses.dataclass
    class Book:
        title: str
        count: int
        tag: str | None = None

    idx = ModelIndex(Book)
    assert isinstance(idx.schema, Schema)
    assert "title" in idx.schema
    assert "count" in idx.schema
    assert "tag" in idx.schema


def test_model_index_to_whoosh_document_dataclass():
    @dataclasses.dataclass
    class Book:
        title: str
        count: int

    idx = ModelIndex(Book)
    doc = idx.to_whoosh_document(Book(title="Hello", count=42))
    assert doc == {"title": "Hello", "count": 42}


def test_model_index_plain_class():
    class Plain:
        __annotations__ = {"name": str, "value": int}

    idx = ModelIndex(Plain)
    assert "name" in idx.schema
    assert "value" in idx.schema
