import pytest

from whoosh import fields, query
from whoosh.filedb.filestore import RamStorage
from whoosh.query.autocomplete import AutocompleteQuery, suggestions


def test_autocomplete_query_prefix_match():
    schema = fields.Schema(content=fields.TEXT(stored=True))
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(content="hello world")
        w.add_document(content="hello there")
        w.add_document(content="help me")
        w.add_document(content="world peace")

    with ix.searcher() as s:
        q = AutocompleteQuery("content", "hel")
        r = s.search(q)
        assert set(hit["content"] for hit in r) == {"hello world", "hello there", "help me"}


def test_suggestions_by_frequency():
    schema = fields.Schema(title=fields.TEXT(stored=True))
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(title="apple")
        w.add_document(title="apple")
        w.add_document(title="apple")
        w.add_document(title="apricot")
        w.add_document(title="banana")

    with ix.searcher() as s:
        result = suggestions(s, "title", "ap", limit=2)
        assert result[0] == "apple"
        assert "apricot" in result


def test_suggestions_alpha_order():
    schema = fields.Schema(title=fields.TEXT(stored=True))
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(title="apple")
        w.add_document(title="apricot")
        w.add_document(title="banana")

    with ix.searcher() as s:
        result = suggestions(s, "title", "ap", limit=2, scorer="alpha")
        assert result == ["apple", "apricot"]
