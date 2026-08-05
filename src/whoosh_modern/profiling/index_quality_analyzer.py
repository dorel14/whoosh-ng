"""Analyze rare terms and index quality metrics.

Measures:
- Singleton terms
- Low-frequency terms
- Long tail distribution
- Index size breakdown (index, postings, terms)

Usage:
    from whoosh_modern.profiling import IndexQualityAnalyzer
    analyzer = IndexQualityAnalyzer(idx_dir)
    report = analyzer.analyze()
    print(report)
"""

from __future__ import annotations

import os
from typing import Any

from whoosh import index
from whoosh.codec.whoosh3 import W3Segment


class IndexQualityAnalyzer:
    """Analyze index quality metrics."""

    def __init__(self, idx_dir: str) -> None:
        self._idx_dir = idx_dir
        self._ix = index.open_dir(idx_dir)

    def analyze(self) -> dict[str, Any]:
        """Analyze the index and return quality metrics."""
        results: dict[str, Any] = {
            "singletons": 0,
            "low_frequency": 0,
            "medium_frequency": 0,
            "high_frequency": 0,
            "total_terms": 0,
            "total_postings": 0,
            "total_docs": 0,
            "avg_postings_per_term": 0.0,
            "p50_postings_per_term": 0,
            "p95_postings_per_term": 0,
            "p99_postings_per_term": 0,
            "max_postings_per_term": 0,
            "term_frequency_distribution": {},
            "size_mb": 0.0,
        }

        with self._ix.searcher() as s:
            reader = s.reader()
            results["total_docs"] = reader.doc_count()

            posting_counts = []
            freq_dist = {}
            for fieldname, text in reader.all_terms():
                ti = reader.term_info(fieldname, text)
                df = ti.doc_frequency()
                posting_counts.append(df)
                freq_dist[df] = freq_dist.get(df, 0) + 1
                results["total_terms"] += 1
                results["total_postings"] += df

                if df == 1:
                    results["singletons"] += 1
                elif df <= 10:
                    results["low_frequency"] += 1
                elif df <= 100:
                    results["medium_frequency"] += 1
                else:
                    results["high_frequency"] += 1

            if posting_counts:
                posting_counts.sort()
                results["avg_postings_per_term"] = sum(posting_counts) / len(posting_counts)
                results["p50_postings_per_term"] = posting_counts[len(posting_counts) // 2]
                results["p95_postings_per_term"] = posting_counts[int(len(posting_counts) * 0.95)]
                results["p99_postings_per_term"] = posting_counts[int(len(posting_counts) * 0.99)]
                results["max_postings_per_term"] = posting_counts[-1]

            results["term_frequency_distribution"] = dict(sorted(freq_dist.items())[:20])

        # Measure index size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self._idx_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        results["size_mb"] = total_size / (1024 * 1024)

        return results

    def report(self) -> str:
        """Generate a human-readable report."""
        metrics = self.analyze()
        lines = ["Index Quality Report", "=" * 50, ""]
        lines.append(f"Total documents: {metrics['total_docs']}")
        lines.append(f"Total terms: {metrics['total_terms']}")
        lines.append(f"Total postings: {metrics['total_postings']}")
        lines.append(f"Index size: {metrics['size_mb']:.2f} MB")
        lines.append("")
        lines.append("Term frequency distribution:")
        lines.append(
            f"  Singletons (df=1)      : {metrics['singletons']:>8} ({metrics['singletons'] / max(metrics['total_terms'], 1) * 100:5.1f}%)"
        )
        lines.append(
            f"  Low freq (2-10)        : {metrics['low_frequency']:>8} ({metrics['low_frequency'] / max(metrics['total_terms'], 1) * 100:5.1f}%)"
        )
        lines.append(
            f"  Medium freq (11-100)   : {metrics['medium_frequency']:>8} ({metrics['medium_frequency'] / max(metrics['total_terms'], 1) * 100:5.1f}%)"
        )
        lines.append(
            f"  High freq (100+)       : {metrics['high_frequency']:>8} ({metrics['high_frequency'] / max(metrics['total_terms'], 1) * 100:5.1f}%)"
        )
        lines.append("")
        lines.append("Postings per term:")
        lines.append(f"  avg: {metrics['avg_postings_per_term']:.1f}")
        lines.append(f"  p50: {metrics['p50_postings_per_term']}")
        lines.append(f"  p95: {metrics['p95_postings_per_term']}")
        lines.append(f"  p99: {metrics['p99_postings_per_term']}")
        lines.append(f"  max: {metrics['max_postings_per_term']}")
        lines.append("")
        lines.append("Top term frequencies:")
        for df, count in sorted(metrics["term_frequency_distribution"].items())[:10]:
            lines.append(f"  df={df:>4}: {count:>6} terms")

        return "\n".join(lines)
