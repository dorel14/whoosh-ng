"""Benchmark JSONSource on the large gouv_local JSON file (272MB)."""

from __future__ import annotations

import os

from benchmark import WhooshLikeSpec
from whoosh import fields
from whoosh_modern.data_sources.json import JSONSource


class GouvJSON(WhooshLikeSpec):
    name = "gouv_json"
    main_field = "nom"
    headline_field = "nom"
    default_query = "Paris"

    def __init__(self, options, args):
        super().__init__(options, args)
        json_path = os.path.join(
            self.options.dir, "Datas", "all_latest",
            "2026-07-31_053230-data.gouv_local.json"
        )
        self._source = JSONSource(
            path=json_path,
            document_path="service",
            incremental_field=None,
            id_field="id",
        )

    def whoosh_schema(self):
        schema = self._source.discover_schema()
        filtered = {
            name: field
            for name, field in schema.items()
            if isinstance(
                field,
                (fields.TEXT, fields.ID, fields.NUMERIC, fields.BOOLEAN, fields.DATETIME),
            )
        }
        from whoosh.fields import Schema
        return Schema(**filtered)

    def documents(self):
        schema_fields = set(self.whoosh_schema().names())
        for doc in self._source.iter_documents():
            filtered = {
                k: v for k, v in doc.items()
                if k in schema_fields and not isinstance(v, (dict, list))
            }
            if filtered:
                yield filtered
