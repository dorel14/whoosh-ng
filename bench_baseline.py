import gzip
import os
import tempfile
import time

from whoosh import analysis, fields, index, qparser

BASE = os.path.dirname(__file__)


def bench_reuters(tmp):
    schema = fields.Schema(
        id=fields.ID(stored=True),
        headline=fields.STORED,
        text=fields.TEXT(analyzer=analysis.StandardAnalyzer(), stored=True),
    )
    ix = index.create_in(tmp, schema, indexname="reuters")
    w = ix.writer()
    path = os.path.join(BASE, "benchmark", "reuters21578.txt.gz")
    n = 0
    t0 = time.perf_counter()
    with gzip.GzipFile(path) as f:
        for line in f:
            did, text = line.decode("latin1").split("\t")
            w.add_document(id=did, text=text, headline=text[:70])
            n += 1
    w.commit()
    index_time = time.perf_counter() - t0

    qp = qparser.QueryParser("text", schema)
    q = qp.parse("oil price")
    t0 = time.perf_counter()
    with ix.searcher() as s:
        r = s.search(q, limit=10)
        _ = len(r)
    search_time = time.perf_counter() - t0
    print(f"BASELINE[reuters] docs={n} index={index_time:.3f}s search={search_time:.4f}s")


def bench_dictionary(tmp):
    schema = fields.Schema(
        head=fields.ID(stored=True),
        body=fields.TEXT(analyzer=analysis.StemmingAnalyzer(), stored=True),
    )
    ix = index.create_in(tmp, schema, indexname="dictionary")
    w = ix.writer()
    path = os.path.join(BASE, "benchmark", "dcvgr10.txt.gz")
    n = 0
    t0 = time.perf_counter()
    head = body = None
    with gzip.GzipFile(path) as f:
        for line in f:
            line = line.decode("latin1")
            if line[0].isalpha():
                if head:
                    w.add_document(head=head, body=head + body)
                    n += 1
                head, body = line.split(".", 1)
            else:
                body += line
    if head:
        w.add_document(head=head, body=head + body)
        n += 1
    w.commit()
    index_time = time.perf_counter() - t0

    qp = qparser.QueryParser("body", schema)
    q = qp.parse("love money")
    t0 = time.perf_counter()
    with ix.searcher() as s:
        r = s.search(q, limit=10)
        _ = len(r)
    search_time = time.perf_counter() - t0
    print(f"BASELINE[dictionary] docs={n} index={index_time:.3f}s search={search_time:.4f}s")


with tempfile.TemporaryDirectory() as tmp:
    for sub in ("r", "d"):
        os.makedirs(os.path.join(tmp, sub))
    bench_reuters(os.path.join(tmp, "r"))
    bench_dictionary(os.path.join(tmp, "d"))
