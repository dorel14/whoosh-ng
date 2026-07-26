"""Fuzz tests guarding against search hangs / infinite loops.

These exercise random queries over random indexes. If a matcher combination
triggers an infinite loop (issues #229 and #446), the worker process will not
finish within the timeout and the test fails instead of freezing the suite.
"""

import multiprocessing
import random

from whoosh import fields, query
from whoosh.filedb.filestore import RamStorage

VOCAB = ["alfa", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel"]


def _build_index(st, seed):
    rng = random.Random(seed)
    schema = fields.Schema(
        title=fields.TEXT(stored=True),
        body=fields.TEXT,
        tag=fields.ID,
    )
    ix = st.create_index(schema)
    w = ix.writer()
    for i in range(rng.randint(5, 30)):
        words = [rng.choice(VOCAB) for _ in range(rng.randint(1, 6))]
        w.add_document(title=f"doc{i}", body=" ".join(words), tag=rng.choice(VOCAB))
    w.commit()
    return ix


def _random_query(rng):
    terms = [query.Term("body", w) for w in rng.sample(VOCAB, rng.randint(1, 3))]
    op = rng.choice(["and", "or", "not"])
    if op == "and":
        return query.And(terms)
    if op == "or":
        return query.Or(terms)
    q = query.And(terms[:1])
    if len(terms) > 1:
        return query.And([q, query.Not(query.Or(terms[1:]))])
    return q


def _run_fuzz(queue, n=200, seed=1234):
    try:
        rng = random.Random(seed)
        st = RamStorage()
        ix = _build_index(st, seed)
        for _ in range(n):
            q = _random_query(rng)
            with ix.searcher() as s:
                # Exercise sorting, limiting, filtering, reversing -- the
                # combinations most likely to expose matcher quality loops.
                try:
                    s.search(
                        q,
                        limit=rng.choice([None, 5, 10]),
                        sortedby=rng.choice([None, "title"]),
                        reverse=rng.choice([True, False]),
                        filter=query.Term("tag", rng.choice(VOCAB)),
                    )
                except Exception:
                    # Query semantics are out of scope; we only guard hangs.
                    pass
        queue.put(True)
    except Exception:
        queue.put(False)


def test_fuzz_search_no_hang():
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    proc = ctx.Process(target=_run_fuzz, args=(queue,))
    proc.start()
    proc.join(timeout=45)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        raise AssertionError("Fuzz search hung (possible regression of #229/#446)")
    assert queue.get(timeout=5), "fuzz worker failed"
