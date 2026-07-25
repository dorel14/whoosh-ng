import gzip
import os.path

from benchmark import WhooshLikeSpec
from benchmark.reporting import BenchmarkResult
from whoosh import analysis, fields
from whoosh.util import now


class Reuters(WhooshLikeSpec):
    name = "reuters"
    filename = "reuters21578.txt.gz"
    main_field = "text"
    headline_field = "headline"
    default_query = "trade"

    def documents(self):
        path = os.path.join(self.options.dir, self.filename)
        f = gzip.GzipFile(path)
        for line in f:
            id, text = line.decode("latin1").split("\t")
            yield {"id": id, "text": text, "headline": text[:70]}

    def whoosh_schema(self):
        ana = analysis.StandardAnalyzer()
        schema = fields.Schema(
            id=fields.ID(stored=True),
            headline=fields.STORED,
            text=fields.TEXT(analyzer=ana, stored=True),
        )
        return schema
