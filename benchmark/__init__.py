# Benchmark package for Whoosh-NG
# Provides indexing, querying, and ranking benchmarks with CSV/JSON reporting.

import os

from whoosh import analysis, fields, index, qparser, scoring
from whoosh.support.bench import Bench, Spec


class WhooshLikeSpec(Spec):
    """Mixin giving Spec subclasses a complete Whoosh index/search lifecycle."""
    default_query = ""

    def whoosh_schema(self):
        """Return the Whoosh Schema for this benchmark. Subclasses must override."""
        raise NotImplementedError

    @staticmethod
    def _index_root(options_dir: str) -> str:
        return os.path.join(options_dir, "indexes")

    @staticmethod
    def _index_path(options_dir: str, indexname: str) -> str:
        return os.path.join(WhooshLikeSpec._index_root(options_dir), f"{indexname}_whoosh")

    def indexer(self, create=True, **kwargs):
        schema = self.whoosh_schema()
        path = self._index_path(self.options.dir, self.options.indexname)
        if create:
            os.makedirs(path, exist_ok=True)
            self.ix = index.create_in(path, schema)
        else:
            self.ix = index.open_dir(path)
        self.writer = self.ix.writer(
            limitmb=int(self.options.limitmb),
            procs=int(getattr(self.options, "procs", 0)),
        )

    def index_document(self, d):
        self.writer.add_document(**d)

    def finish(self, merge=True, optimize=False):
        self.writer.commit(merge=merge, optimize=optimize)

    def searcher(self):
        path = self._index_path(self.options.dir, self.options.indexname)
        self.ix = index.open_dir(path)
        self.srch = self.ix.searcher(weighting=scoring.PL2())
        self.qp = qparser.QueryParser(self.main_field, schema=self.ix.schema)

    def query(self):
        qstring = " ".join(self.args)
        return qstring if qstring else self.default_query

    def find(self, q):
        limit = int(getattr(self.options, "limit", 10))
        return self.srch.search(self.qp.parse(q), limit=limit)

    def print_results(self, ls):
        limit = int(getattr(self.options, "limit", 10))
        for i, hit in enumerate(ls):
            if i >= limit:
                break
            if hasattr(hit, "keys"):
                try:
                    headline = hit[self.headline_field]
                except KeyError:
                    headline = hit.get(self.main_field, str(hit)) if hasattr(hit, "get") else str(hit)
                print(f"  {i + 1}. {headline}")
                if getattr(self.options, "showbody", False):
                    try:
                        body = hit[self.main_field]
                    except KeyError:
                        body = ""
                    if body:
                        print(f"     {str(body)[:200]}")
            else:
                print(f"  {i + 1}. {hit}")


__all__ = ["Bench", "Spec", "WhooshLikeSpec"]
