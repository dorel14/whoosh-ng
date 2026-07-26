import gzip
import os

from benchmark import WhooshLikeSpec
from whoosh import analysis, fields


class VulgarTongue(WhooshLikeSpec):
    name = "dictionary"
    filename = "dcvgr10.txt.gz"
    main_field = "body"
    headline_field = "head"
    default_query = "bawd"

    def documents(self):
        path = os.path.join(self.options.dir, self.filename)
        f = gzip.GzipFile(path)
        head = body = ""
        for line in f:
            line = line.decode("latin1")
            if line[0].isalpha():
                if head:
                    yield {"head": head, "body": head + body}
                head, body = line.split(".", 1)
            else:
                body += line
        if head:
            yield {"head": head, "body": head + body}

    def whoosh_schema(self):
        ana = analysis.StemmingAnalyzer()
        schema = fields.Schema(
            head=fields.ID(stored=True), body=fields.TEXT(analyzer=ana, stored=True)
        )
        return schema
