import pytest

from whoosh import collectors, fields, query, searching, sorting
from whoosh.filedb.filestore import RamStorage
from whoosh.util.testing import TempIndex


def test_add():
    schema = fields.Schema(id=fields.STORED, text=fields.TEXT)
    ix = RamStorage().create_index(schema)
    w = ix.writer()
    w.add_document(id=1, text="alfa bravo charlie")
    w.add_document(id=2, text="alfa bravo delta")
    w.add_document(id=3, text="alfa charlie echo")
    w.commit()

    with ix.searcher() as s:
        assert s.doc_frequency("text", "charlie") == 2
        r = s.search(query.Term("text", "charlie"))
        assert [hit["id"] for hit in r] == [1, 3]
        assert len(r) == 2


def test_filter_that_matches_no_document():
    schema = fields.Schema(id=fields.STORED, text=fields.TEXT)
    ix = RamStorage().create_index(schema)
    w = ix.writer()
    w.add_document(id=1, text="alfa bravo charlie")
    w.add_document(id=2, text="alfa bravo delta")
    w.commit()

    with ix.searcher() as s:
        r = s.search(query.Every(), filter=query.Term("text", "echo"))
        assert [hit["id"] for hit in r] == []
        assert len(r) == 0


def test_timelimit():
    schema = fields.Schema(text=fields.TEXT)
    ix = RamStorage().create_index(schema)
    w = ix.writer()
    for _ in range(50):
        w.add_document(text="alfa")
    w.commit()

    import time

    from whoosh import collectors, matching

    class SlowMatcher(matching.WrappingMatcher):
        def next(self):
            time.sleep(0.02)
            self.child.next()

    class SlowQuery(query.WrappingQuery):
        def matcher(self, searcher, context=None):
            return SlowMatcher(self.child.matcher(searcher, context))

    with ix.searcher() as s:
        oq = query.Term("text", "alfa")
        sq = SlowQuery(oq)

        col = collectors.TimeLimitCollector(s.collector(limit=None), timelimit=0.1)
        with pytest.raises(searching.TimeLimit):
            s.search_with_collector(sq, col)

        col = collectors.TimeLimitCollector(s.collector(limit=40), timelimit=0.1)
        with pytest.raises(collectors.TimeLimit):
            s.search_with_collector(sq, col)

        col = collectors.TimeLimitCollector(s.collector(limit=None), timelimit=0.25)
        try:
            s.search_with_collector(sq, col)
            assert False  # Shouldn't get here
        except collectors.TimeLimit:
            r = col.results()
            assert r.scored_length() > 0

        col = collectors.TimeLimitCollector(s.collector(limit=None), timelimit=0.5)
        s.search_with_collector(oq, col)
        assert col.results().runtime < 0.5


@pytest.mark.skipif("not hasattr(__import__('signal'), 'SIGALRM')")
def test_timelimit_alarm():
    import time

    from whoosh import matching

    class SlowMatcher(matching.Matcher):
        def __init__(self):
            self._id = 0

        def id(self):
            return self._id

        def is_active(self):
            return self._id == 0

        def next(self):
            time.sleep(10)
            self._id = 1

        def score(self):
            return 1.0

    class SlowQuery(query.Query):
        def matcher(self, searcher, context=None):
            return SlowMatcher()

    schema = fields.Schema(text=fields.TEXT)
    ix = RamStorage().create_index(schema)
    with ix.writer() as w:
        w.add_document(text="Hello")

    with ix.searcher() as s:
        q = SlowQuery()

        t = time.time()
        c = s.collector()
        c = collectors.TimeLimitCollector(c, 0.2)
        with pytest.raises(searching.TimeLimit):
            _ = s.search_with_collector(q, c)
        assert time.time() - t < 0.5, f"Actual time interval: {time.time() - t}"


def test_reverse_collapse():
    from whoosh import sorting

    schema = fields.Schema(
        title=fields.TEXT(stored=True),
        content=fields.TEXT,
        path=fields.ID(stored=True),
        tags=fields.KEYWORD,
        order=fields.NUMERIC(stored=True),
    )

    ix = RamStorage().create_index(schema)
    with ix.writer() as w:
        w.add_document(
            title="First document",
            content="This is my document!",
            path="/a",
            tags="first",
            order=20.0,
        )
        w.add_document(
            title="Second document",
            content="This is the second example.",
            path="/b",
            tags="second",
            order=12.0,
        )
        w.add_document(
            title="Third document",
            content="Examples are many.",
            path="/c",
            tags="third",
            order=15.0,
        )
        w.add_document(
            title="Thirdish document",
            content="Examples are too many.",
            path="/d",
            tags="third",
            order=25.0,
        )

    with ix.searcher() as s:
        q = query.Every("content")
        r = s.search(q)
        assert [hit["path"] for hit in r] == ["/a", "/b", "/c", "/d"]

        q = query.Or(
            [
                query.Term("title", "document"),
                query.Term("content", "document"),
                query.Term("tags", "document"),
            ]
        )
        cf = sorting.FieldFacet("tags")
        of = sorting.FieldFacet("order", reverse=True)
        r = s.search(q, collapse=cf, collapse_order=of, terms=True)
        assert [hit["path"] for hit in r] == ["/a", "/b", "/d"]


def test_termdocs():
    schema = fields.Schema(key=fields.TEXT, city=fields.ID)
    ix = RamStorage().create_index(schema)
    with ix.writer() as w:
        w.add_document(key="ant", city="london")
        w.add_document(key="anteater", city="roma")
        w.add_document(key="bear", city="london")
        w.add_document(key="bees", city="roma")
        w.add_document(key="anorak", city="london")
        w.add_document(key="antimatter", city="roma")
        w.add_document(key="angora", city="london")
        w.add_document(key="angels", city="roma")

    with ix.searcher() as s:
        cond_q = query.Term("city", "london")
        pref_q = query.Prefix("key", "an")
        q = query.And([cond_q, pref_q]).normalize()
        r = s.search(q, scored=False, terms=True)

        field = s.schema["key"]
        terms = [field.from_bytes(term) for fieldname, term in r.termdocs if fieldname == "key"]
        assert sorted(terms) == ["angora", "anorak", "ant"]


def test_termdocs2():
    schema = fields.Schema(key=fields.TEXT, city=fields.ID)
    ix = RamStorage().create_index(schema)
    with ix.writer() as w:
        w.add_document(key="ant", city="london")
        w.add_document(key="anteater", city="roma")
        w.add_document(key="bear", city="london")
        w.add_document(key="bees", city="roma")
        w.add_document(key="anorak", city="london")
        w.add_document(key="antimatter", city="roma")
        w.add_document(key="angora", city="london")
        w.add_document(key="angels", city="roma")

    with ix.searcher() as s:
        # A query that matches the applicable documents
        cond_q = query.Term("city", "london")
        # Get a list of the documents that match the condition(s)
        cond_docnums = set(cond_q.docs(s))
        # Grab the suggestion field for later
        field = s.schema["key"]

        terms = []
        # Expand the prefix
        for term in s.reader().expand_prefix("key", "an"):
            # Get the documents the term is in
            for docnum in s.document_numbers(key=term):
                # Check if it's in the set matching the condition(s)
                if docnum in cond_docnums:
                    # If so, decode the term from bytes and add it to the list,
                    # then move on to the next term
                    terms.append(field.from_bytes(term))
                    break
        assert terms == ["angora", "anorak", "ant"]


def test_filter_results_count():
    schema = fields.Schema(id=fields.STORED, django_ct=fields.ID(stored=True), text=fields.TEXT)
    with TempIndex(schema) as ix:
        with ix.writer() as w:
            w.add_document(id=1, django_ct="app.model1", text="alfa bravo charlie")
            w.add_document(id=2, django_ct="app.model1", text="alfa bravo delta")
            w.add_document(id=3, django_ct="app.model2", text="alfa charlie echo")

        with ix.searcher() as s:
            q = query.Term("django_ct", "app.model1")
            r1 = s.search(q, limit=None)
            assert len(r1) == 2

            q = query.Term("text", "alfa")
            restrict_q = query.Term("django_ct", "app.model2")
            r2 = s.search(q, filter=restrict_q)
            assert len(r2) == 1
            assert r2[0]["id"] == 3


def test_filter_with_reverse_sorting():
    schema = fields.Schema(
        id=fields.STORED,
        text=fields.TEXT,
        category=fields.ID(stored=True),
        score=fields.NUMERIC(stored=True),
    )
    ix = RamStorage().create_index(schema)
    with ix.writer() as w:
        w.add_document(id=1, text="alfa bravo", category="A", score=10)
        w.add_document(id=2, text="bravo charlie", category="B", score=20)
        w.add_document(id=3, text="charlie delta", category="A", score=15)
        w.add_document(id=4, text="delta echo", category="B", score=25)

    with ix.searcher() as s:
        q = query.Term("text", "bravo")
        filter_q = query.Term("category", "A")
        r = s.search(q, filter=filter_q, sortedby=sorting.FieldFacet("score"), reverse=True)
        assert [hit["id"] for hit in r] == [1]
        assert len(r) == 1


def test_timelimit_preserves_filter():
    schema = fields.Schema(id=fields.STORED, text=fields.TEXT, status=fields.ID)
    ix = RamStorage().create_index(schema)
    with ix.writer() as w:
        w.add_document(id=1, text="alfa bravo charlie", status="public")
        w.add_document(id=2, text="bravo charlie delta", status="private")
        w.add_document(id=3, text="charlie delta echo", status="public")
        w.add_document(id=4, text="delta echo foxtrot", status="private")
        w.add_document(id=5, text="echo foxtrot golf", status="public")

    with ix.searcher() as s:
        q = query.Term("text", "charlie")
        filter_q = query.Term("status", "public")
        col = collectors.TimeLimitCollector(
            s.collector(filter=filter_q, limit=None), timelimit=5.0
        )
        s.search_with_collector(q, col)
        r = col.results()
        result_ids = {hit["id"] for hit in r}
        # The filter (status == "public") must NOT be dropped by the
        # TimeLimitCollector, even though it iterates child.matches().
        assert result_ids == {1, 3}


def test_unlimited_collector_returns_all():
    """Issue #479: UnlimitedCollector must return all matching documents."""
    from whoosh.collectors import UnlimitedCollector

    schema = fields.Schema(content=fields.TEXT)
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        for i in range(100):
            w.add_document(content=f"doc {i}")

    with ix.searcher() as s:
        q = query.Every()
        uc = UnlimitedCollector()
        s.search_with_collector(q, uc)
        r = uc.results()
        assert len(r) == 100


def test_or_groups():
    """Issue #454: OR queries should preserve grouped results correctly."""
    schema = fields.Schema(content=fields.TEXT(stored=True), category=fields.KEYWORD)
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(content="hello world", category="A")
        w.add_document(content="hello there", category="A")
        w.add_document(content="help me", category="B")
        w.add_document(content="world peace", category="B")

    with ix.searcher() as s:
        q = query.Or([query.Term("content", "hello"), query.Term("content", "world")])
        r = s.search(q, groupedby="category")
        groups = r.groups("category")
        assert set(groups.keys()) == {"A", "B"}
        assert len(groups["A"]) == 2
        assert len(groups["B"]) == 1


def test_collapse_with_order_length():
    """Issue #453: collapse + collapse_order should report correct result length."""
    schema = fields.Schema(content=fields.TEXT(stored=True), category=fields.KEYWORD, sort=fields.NUMERIC)
    st = RamStorage()
    ix = st.create_index(schema)

    with ix.writer() as w:
        w.add_document(content="hello world", category="A", sort=1)
        w.add_document(content="hello there", category="A", sort=2)
        w.add_document(content="help me", category="B", sort=3)
        w.add_document(content="world peace", category="B", sort=4)

    with ix.searcher() as s:
        q = query.Every()
        r = s.search(q, collapse="category", collapse_order=sorting.FieldFacet("sort"), limit=10)
        assert len(r) == 2
        assert r.collapsed_counts["A"] == 1
        assert r.collapsed_counts["B"] == 1
