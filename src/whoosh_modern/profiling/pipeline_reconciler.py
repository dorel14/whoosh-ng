"""Pipeline reconciler for Whoosh-NG.

Reconciles measurements from:
- AnalyzerStepProfiler (analyzer only)
- IndexingPipelineProfiler (simulated pipeline)
- IndexingPathProfiler (actual indexing path)
- Real benchmark

Explains the gap between theoretical and real measurements.

Usage:
    from whoosh_modern.profiling import PipelineReconciler
    reconciler = PipelineReconciler()
    reconciler.add_measurement("analyzer", analyzer_time, analyzer_tokens)
    reconciler.add_measurement("simulated", simulated_time, simulated_tokens)
    reconciler.add_measurement("actual", actual_time, actual_tokens)
    reconciler.add_measurement("real_benchmark", real_time, real_tokens)
    print(reconciler.report())
"""

from __future__ import annotations

from typing import Any


class PipelineReconciler:
    """Reconcile pipeline measurements and explain gaps."""

    def __init__(self) -> None:
        self._measurements: dict[str, dict[str, Any]] = {}

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

    def report(self) -> str:
        """Generate a reconciliation report."""
        if not self._measurements:
            return "No measurements to reconcile."

        lines = ["Pipeline Reconciliation Report", "=" * 60, ""]

        # Table of measurements
        lines.append(
            f"{'Measurement':<25} {'Time (s)':>10} {'Tokens':>12} {'Docs':>10} "
            f"{'Tokens/s':>12} {'Docs/s':>12}"
        )
        lines.append("-" * 85)
        for name in sorted(self._measurements.keys()):
            m = self._measurements[name]
            lines.append(
                f"{name:<25} {m['time_s']:>10.3f} {m['tokens']:>12} {m['docs']:>10} "
                f"{m['tokens_per_second']:>12.0f} {m['docs_per_second']:>12.0f}"
            )

        lines.append("")

        # Gap analysis
        if "analyzer" in self._measurements and "real_benchmark" in self._measurements:
            analyzer_time = self._measurements["analyzer"]["time_s"]
            real_time = self._measurements["real_benchmark"]["time_s"]
            gap = real_time - analyzer_time
            gap_pct = gap / real_time * 100 if real_time > 0 else 0

            lines.append("Gap Analysis:")
            lines.append(f"  Analyzer only      : {analyzer_time:>10.3f}s")
            lines.append(f"  Real benchmark     : {real_time:>10.3f}s")
            lines.append(f"  Gap                : {gap:>10.3f}s ({gap_pct:.1f}% of real)")
            lines.append("")

        if "simulated" in self._measurements and "actual" in self._measurements:
            sim_time = self._measurements["simulated"]["time_s"]
            actual_time = self._measurements["actual"]["time_s"]
            gap = actual_time - sim_time
            gap_pct = gap / actual_time * 100 if actual_time > 0 else 0

            lines.append("Simulated vs Actual:")
            lines.append(f"  Simulated pipeline : {sim_time:>10.3f}s")
            lines.append(f"  Actual pipeline    : {actual_time:>10.3f}s")
            lines.append(f"  Gap                : {gap:>10.3f}s ({gap_pct:.1f}% of actual)")
            lines.append("")

        # Conclusions
        lines.append("Conclusions:")
        if "simulated" in self._measurements and "actual" in self._measurements:
            sim_time = self._measurements["simulated"]["time_s"]
            actual_time = self._measurements["actual"]["time_s"]
            gap = actual_time - sim_time
            gap_pct = gap / actual_time * 100 if actual_time > 0 else 0

            if gap > 0:
                lines.append(
                    f"  - The simulated pipeline underestimates by {gap:.3f}s ({gap_pct:.1f}%)"
                )
                lines.append(
                    "  - The missing time is in field transformation and "
                    "indexing pipeline feeding"
                )
                lines.append(
                    "  - Field conversion + PostingPool.add() + "
                    "perdocwriter operations account for the gap"
                )
            else:
                lines.append("  - The simulated pipeline matches or exceeds actual measurements")

        if "analyzer" in self._measurements and "actual" in self._measurements:
            analyzer_time = self._measurements["analyzer"]["time_s"]
            actual_time = self._measurements["actual"]["time_s"]
            analyzer_pct = analyzer_time / actual_time * 100 if actual_time > 0 else 0

            lines.append(f"  - Analyzer represents {analyzer_pct:.1f}% of actual indexing time")
            lines.append(
                f"  - Non-analyzer overhead represents "
                f"{100 - analyzer_pct:.1f}% of actual indexing time"
            )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        return {
            "measurements": self._measurements,
        }
