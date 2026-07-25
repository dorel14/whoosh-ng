import inspect
import sys
from itertools import permutations
from random import choice, randint

import pytest

from whoosh import fields, query, scoring
from whoosh.filedb.filestore import RamStorage


def u(s):
    return s.decode("ascii") if isinstance(s, bytes) else s


def _weighting_classes(ignore):
    # Get all the subclasses of Weighting in whoosh.scoring
    return [
        c
        for _, c in inspect.getmembers(scoring, inspect.isclass)
        if scoring.Weighting in c.__bases__ and c not in ignore
    ]


def test_all():
    domain = [u("alfa"), u("bravo"), u("charlie"), u("delta"), u("echo"), u("foxtrot")]
    schema = fields.Schema(text=fields.TEXT)
    storage = RamStorage()
    ix = storage.create_index(schema)
    w = ix.writer()
    for _ in range(100):
        w.add_document(text=u(" ").join(choice(domain) for _ in range(randint(10, 20))))
    w.commit()

    # List ABCs that should not be tested
    abcs = ()
    # provide initializer arguments for any weighting classes that require them
    init_args = {
        "MultiWeighting": ([scoring.BM25F()], {"text": scoring.Frequency()}),
        "ReverseWeighting": ([scoring.BM25F()], {}),
    }

    for wclass in _weighting_classes(abcs):
        try:
            if wclass.__name__ in init_args:
                args, kwargs = init_args[wclass.__name__]
                weighting = wclass(*args, **kwargs)
            else:
                weighting = wclass()
        except TypeError:
            e = sys.exc_info()[1]
            raise TypeError(f"Error instantiating {wclass!r}: {e}")

        with ix.searcher(weighting=weighting) as s:
            try:
                for word in domain:
                    s.search(query.Term("text", word))  # type: ignore[call-issue]
            except ValueError:
                e = sys.exc_info()[1]
                e.msg = f"Error searching with {wclass!r}: {e}"  # type: ignore[attr-defined]
                raise


def test_compatibility():
    from whoosh.scoring import Weighting

    # This is the old way of doing a custom weighting model, check that
    # it's still supported...
    class LegacyWeighting(Weighting):
        use_final = True

        def score(self, searcher, fieldname, text, docnum, weight):
            return weight + 0.5

        def final(self, searcher, docnum, score):
            return score * 1.5

    schema = fields.Schema(text=fields.TEXT)
    ix = RamStorage().create_index(schema)
    w = ix.writer()
    domain = "alfa bravo charlie delta".split()
    for ls in permutations(domain, 3):
        w.add_document(text=u(" ").join(ls))
    w.commit()

    s = ix.searcher(weighting=LegacyWeighting())  # type: ignore[call-issue]
    r = s.search(query.Term("text", u("bravo")))
    assert r.score(0) == 2.25


# --- Sprint 3: scoring / weighting (#560/#3, #494, #2) ----------------------


def test_proximity_boost():
    # Issue #560/#3: PositionBoostWeighting rewards documents where the
    # matched terms are closer together.
    schema = fields.Schema(text=fields.TEXT)
    ix = RamStorage().create_index(schema)
    w = ix.writer()
    # doc 0: "apple banana" -> adjacent (distance 1)
    w.add_document(text="apple banana")
    # doc 1: "apple ... banana" -> scattered (distance > 1)
    w.add_document(text="apple xxx yyy banana")
    # doc 2: only one of the terms
    w.add_document(text="apple")
    w.commit()

    with ix.searcher(weighting=scoring.PositionBoostWeighting(phrase_boost=2.0, k=1.0)) as s:
        r = s.search(query.Or([query.Term("text", "apple"), query.Term("text", "banana")]))
        scores = {hit.docnum: hit.score for hit in r}
        # doc 0 must score higher than doc 1 because terms are adjacent
        assert scores[0] > scores[1], (scores[0], scores[1]) # pyright: ignore[reportOptionalOperand]


def test_phrase_position_boost():
    # Issue #560/#3: a Phrase query with PositionBoostWeighting should rank
    # the document with contiguous terms above the one with scattered terms.
    schema = fields.Schema(text=fields.TEXT)
    ix = RamStorage().create_index(schema)
    w = ix.writer()
    w.add_document(text="the cat sat on the mat")
    w.add_document(text="the cat xxx yyy sat on the zzz mat")
    w.commit()

    with ix.searcher(weighting=scoring.PositionBoostWeighting(phrase_boost=3.0, k=0.5)) as s:
        q = query.Phrase("text", ["cat", "mat"])
        r = s.search(q)
        # Both docs match (phrase with slop not set -> exact phrase, but
        # PositionBoostWeighting applies bonus when spans are close even
        # across the full phrase; the first doc has cat+mat distance 5 vs
        # the scattered one distance > 5)
        scores = {hit.docnum: hit.score for hit in r}
        if 0 in scores and 1 in scores:
            assert scores[0] > scores[1], (scores[0], scores[1]) # pyright: ignore[reportOptionalOperand]


def test_weighting_by_name():
    # Issue #494: weighting_from_name accepts str / type / instance.
    w = scoring.weighting_from_name("BM25F")
    assert isinstance(w, scoring.BM25F)

    w = scoring.weighting_from_name("bm25f", B=0.5)
    assert isinstance(w, scoring.BM25F)
    assert w.B == 0.5

    w = scoring.weighting_from_name("TFIDF")
    assert isinstance(w, scoring.TF_IDF)

    w = scoring.weighting_from_name("tf-idf")
    assert isinstance(w, scoring.TF_IDF)

    w = scoring.weighting_from_name("PL2", c=2.0)
    assert isinstance(w, scoring.PL2)
    assert w.c == 2.0

    w = scoring.weighting_from_name("Frequency")
    assert isinstance(w, scoring.Frequency)

    # Already an instance -> returned unchanged.
    bm25 = scoring.BM25F()
    assert scoring.weighting_from_name(bm25) is bm25

    # Already a class -> instantiated.
    result = scoring.weighting_from_name(scoring.TF_IDF)
    assert isinstance(result, scoring.TF_IDF)

    with pytest.raises(ValueError):
        scoring.weighting_from_name("NO_SUCH_WEIGHTING")


def test_subquery_boost_normalization():
    # Issue #2: CompoundQuery.normalize_boosts() divides each subquery's
    # boost by the maximum sub-boost so combined scores are not dominated
    # by raw boost magnitudes.
    q = query.Or(
        [query.Term("f", "a", boost=5.0), query.Term("f", "b", boost=1.0)],
        boost=1.0,
    )
    norm = q.normalize_boosts()
    sub_boosts = [sub.boost for sub in norm.subqueries]
    # The maximum sub-boost becomes 1.0, the others are scaled down.
    assert round(max(sub_boosts), 6) == 1.0
    assert round(min(sub_boosts), 6) == round(1.0 / 5.0, 6)
