"""AutoCacheAdvisor for Whoosh-NG.

Analyzes schema and field usage to recommend which fields should be cached
by AnalyzerCache.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from whoosh.fields import Schema
from whoosh_modern.schema_discovery import SchemaDiscovery


class AutoCacheAdvisor:
    """Recommend which fields benefit from analyzer caching.

    Uses simple heuristics on observed values:
    - repetition ratio
    - number of unique values
    - field type

    Example::

        advisor = AutoCacheAdvisor(min_repetition_ratio=2.0)
        recommendations = advisor.advise(schema, documents_iter)
        print(recommendations)
    """

    def __init__(
        self,
        min_repetition_ratio: float = 2.0,
        sample_size: int = 10000,
    ) -> None:
        self.min_repetition_ratio = min_repetition_ratio
        self.sample_size = sample_size

    def advise(self, schema: Schema, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Return cache recommendations for the given documents.

        :param schema: Whoosh Schema
        :param documents: list of document dicts
        :returns: recommendation dict with fields, stats, and cache config
        """
        field_values: dict[str, list[Any]] = {name: [] for name in schema.names()}
        for doc in documents[: self.sample_size]:
            for name in schema.names():
                if name in doc:
                    field_values[name].append(doc[name])

        fields_stats: dict[str, dict[str, Any]] = {}
        recommended: list[str] = []
        for name, values in field_values.items():
            total = len(values)
            unique = len(set(values))
            repetition_ratio = total / unique if unique else 0.0
            fields_stats[name] = {
                "total": total,
                "unique": unique,
                "repetition_ratio": round(repetition_ratio, 2),
            }
            if repetition_ratio >= self.min_repetition_ratio:
                recommended.append(name)

        return {
            "fields": fields_stats,
            "recommended_fields": recommended,
            "cache_config": {
                "fields": recommended,
                "cache_size": min(50000, sum(fields_stats[f]["unique"] for f in recommended) * 2),
            },
        }

    def advise_from_source(self, source: Any) -> dict[str, Any]:
        """Return cache recommendations from a DataSource.

        :param source: DataSource instance
        :returns: recommendation dict
        """
        docs = []
        for i, doc in enumerate(source.iter_documents()):
            docs.append(doc)
            if i >= self.sample_size:
                break
        schema = source.discover_schema()
        return self.advise(schema, docs)

    def text_report(self, recommendations: dict[str, Any]) -> str:
        lines = ["AutoCacheAdvisor Report", "=" * 50, ""]
        for field, stats in recommendations.get("fields", {}).items():
            lines.append(
                f"  {field}: repetition_ratio={stats['repetition_ratio']:.2f} "
                f"unique={stats['unique']}/{stats['total']}"
            )
        lines.append("")
        lines.append(
            "Recommended fields: " + ", ".join(recommendations.get("recommended_fields", []))
        )
        return "\n".join(lines)
