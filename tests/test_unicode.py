import pytest

from whoosh import fields, query
from whoosh.filedb.filestore import RamStorage


def test_unicode_search_french():
    """Issue #440: French/latin characters should be searchable."""
    schema = fields.Schema(content=fields.TEXT)
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(content="café")
        w.add_document(content="naïve")
        w.add_document(content="hello")

    with ix.searcher() as s:
        r = s.search(query.Term("content", "café"))
        assert len(r) == 1

        r = s.search(query.Term("content", "naïve"))
        assert len(r) == 1


def test_unicode_search_chinese():
    """Issue #441: Chinese characters should be searchable."""
    schema = fields.Schema(content=fields.TEXT)
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(content="中文")
        w.add_document(content="日本語")
        w.add_document(content="한국어")

    with ix.searcher() as s:
        r = s.search(query.Term("content", "中文"))
        assert len(r) == 1

        r = s.search(query.Term("content", "日本語"))
        assert len(r) == 1


def test_unicode_search_arabic():
    """Arabic characters should be searchable."""
    schema = fields.Schema(content=fields.TEXT)
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(content="مرحبا")
        w.add_document(content="السلام عليكم")

    with ix.searcher() as s:
        r = s.search(query.Term("content", "مرحبا"))
        assert len(r) == 1
