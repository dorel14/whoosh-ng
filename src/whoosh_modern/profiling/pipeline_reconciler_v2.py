"""End-to-end pipeline reconciler for Whoosh-NG.

Combines profiling from:
- AnalyzerStepProfiler
- FieldTransformationProfiler
- PostingPoolProfiler
- PerDocWriterProfiler
- Real benchmark

Produces a reconciled report with percentages.

Usage:
    from whoosh_modern.profiling import PipelineReconcilerV2
    reconciler = PipelineReconcilerV2()
    reconciler.add_measurement("analyzer", analyzer_time, analyzer_tokens)
    reconciler.add_measurement("field_transformation", field_time, field_tokens)
    reconciler.add_measurement("posting_pool", pool_time, pool_tokens)
    reconciler.add_measurement("perdoc_writer", perdoc_time, perdoc_tokens)
    reconciler.add_measurement("real_benchmark", real_time, real_tokens)
    print(reconciler.report())
"""

from __future__ import annotations

from typing import Any


class PipelineReconcilerV2:
    """Reconcile pipeline measurements and produce a unified report."""

    def __init__(self) -> None:
        self._measurements: dict[str, dict[str, Any]] = {}
        self._real_time: float = 0.0

    def add_measurement(self, name: str, time_s: float, tokens: int = 0, docs: int = 0) -> None:
        """Add a measurement.

        :param name: measurement name
        :param time_s: total time in seconds
        :param tokens: total tokens processed
        :param docs: total documents processed
        """
        self._measurements[name] = {
            "time_s": time_s,
            "tokens": tokens,
            "docs": docs,
            "tokens_per_second": tokens / time_s if time_s > 0 else 0,
            "docs_per_second": docs / time_s if time_s > 0 else 0,
        }
        if name == "real_benchmark":
            self._real_time = time_s

    def report(self) -> str:
        """Generate a reconciliation report."""
        if not self._measurements:
            return "No measurements to reconcile."

        lines = ["Pipeline Reconciliation Report (V2)", "=" * 60, ""]

        # Calculate categories
        categories = {
            "Analyzer": self._measurements.get("analyzer", {}).get("time_s", 0.0),
            "Field conversion": self._measurements.get("field_transformation", {}).get(
                "time_s", 0.0
            ),
            "PostingPool": self._measurements.get("posting_pool", {}).get("time_s", 0.0),
            "PerDocWriter": self._measurements.get("perdoc_writer", {}).get("time_s", 0.0),
        }

        # Calculate other time
        measured_total = sum(categories.values())
        other_time = self._real_time - measured_total if self._real_time > measured_total else 0.0
        categories["Other"] = other_time

        # Calculate percentages
        total = self._real_time if self._real_time > 0 else measured_total
        percentages = {k: v / total * 100 if total > 0 else 0.0 for k, v in categories.items()}

        # Table of measurements
        lines.append(f"{'Category':<25} {'Time (s)':>10} {'%':>8}")
        lines.append("-" * 45)
        for name in ["Analyzer", "Field conversion", "PostingPool", "PerDocWriter", "Other"]:
            t = categories.get(name, 0.0)
            pct = percentages.get(name, 0.0)
            lines.append(f"{name:<25} {t:>10.3f} {pct:>7.1f}%")

        lines.append("-" * 45)
        lines.append(f"{'Total':<25} {total:>10.3f} {'100.0':>8}%")

        lines.append("")

        # Detailed breakdown
        lines.append("Detailed measurements:")
        for name in sorted(self._measurements.keys()):
            m = self._measurements[name]
            lines.append(f"  {name:<25} {m['time_s']:>10.3f}s")

        lines.append("")

        # Reconciliation
        if self._real_time > 0:
            explained = measured_total
            unexplained = other_time
            explained_pct = explained / self._real_time * 100
            unexplained_pct = unexplained / self._real_time * 100

            lines.append("Reconciliation:")
            lines.append(f"  Real benchmark time   : {self._real_time:>10.3f}s")
            lines.append(f"  Explained time        : {explained:>10.3f}s ({explained_pct:.1f}%)")
            lines.append(
                f"  Unexplained time      : {unexplained:>10.3f}s ({unexplained_pct:.1f}%)"
            )
            lines.append("")

            if unexplained_pct < 5:
                lines.append("  [OK] Pipeline fully reconciled (>95% explained)")
            else:
                lines.append(f"  [WARN] {unexplained_pct:.1f}% of time still unexplained")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        categories = {
            "Analyzer": self._measurements.get("analyzer", {}).get("time_s", 0.0),
            "Field conversion": self._measurements.get("field_transformation", {}).get(
                "time_s", 0.0
            ),
            "PostingPool": self._measurements.get("posting_pool", {}).get("time_s", 0.0),
            "PerDocWriter": self._measurements.get("perdoc_writer", {}).get("time_s", 0.0),
        }
        measured_total = sum(categories.values())
        other_time = self._real_time - measured_total if self._real_time > measured_total else 0.0
        categories["Other"] = other_time
        total = self._real_time if self._real_time > 0 else measured_total

        return {
            "categories": categories,
            "percentages": {
                k: v / total * 100 if total > 0 else 0.0 for k, v in categories.items()
            },
            "real_time": self._real_time,
            "explained_time": measured_total,
            "unexplained_time": other_time,
            "explained_pct": measured_total / self._real_time * 100 if self._real_time > 0 else 0.0,
        }
