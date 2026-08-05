"""P4 Field Index Profiling benchmark - Complete data tables.

P4.1 Decompose field.index() into sub-steps
P4.2 Measure per token: time, allocations, objects
P4.3 Compare analyzers on A/B/C/D
P4.4 Test stemmers on millions of tokens

Usage:
    uv run python src/whoosh_modern/profiling/benchmarks/p4_field_index_profiling.py
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List, Tuple

sys.path.insert(0, "src")

from whoosh.analysis import LanguageAnalyzer, StandardAnalyzer, StemmingAnalyzer
from whoosh.fields import TEXT, Schema
from whoosh_modern.profiling.analyzer_profiler import AnalyzerStepProfiler
from whoosh_modern.profiling.field_index_profiler import FieldIndexProfiler
from whoosh_modern.profiling.stemmer_benchmark import StemmerBenchmark
from whoosh_modern.profiling.synthetic_datasets import SyntheticDatasetGenerator


def run_p4_1_2(schema: Schema, datasets: dict[str, list[str]]) -> dict[str, Any]:
    """P4.1/P4.2: Field index breakdown with per-token metrics."""
    print("=" * 80)
    print("P4.1/P4.2 Field Index Profiling - Breakdown by sub-step")
    print("=" * 80)

    field = schema["City"]
    results: dict[str, Any] = {}

    for dataset_name, texts in datasets.items():
        print(f"\n--- Dataset {dataset_name} ({len(texts)} texts) ---")
        profiler = FieldIndexProfiler(field)

        total_tokens = 0
        total_time = 0.0
        step_timings: dict[str, float] = defaultdict(float)
        step_counts: dict[str, int] = defaultdict(int)

        for text in texts:
            items = profiler.profile_index(text)
            total_tokens += len(items)

        # Aggregate results
        for step, t in profiler._timings.items():
            step_timings[step] += t
        for step, c in profiler._counts.items():
            step_counts[step] += c

        total_time = step_timings.get("total", 0.0)

        # Print table
        print(f"{'Step':<25} {'Time (s)':>12} {'%':>8} {'Tokens':>10} {'Time/token (ms)':>18}")
        print("-" * 77)

        for step_name in sorted(step_timings.keys()):
            if step_name == "total":
                continue
            t = step_timings[step_name]
            count = step_counts.get(step_name, 0)
            pct = t / total_time * 100 if total_time > 0 else 0.0
            tpt = t / count * 1000 if count > 0 else 0.0
            print(f"  {step_name:<23} {t:>12.4f} {pct:>7.1f}% {count:>10} {tpt:>17.4f}")

        print("-" * 77)
        tpt_total = total_time / total_tokens * 1000 if total_tokens > 0 else 0.0
        print(
            f"  {'Total':<23} {total_time:>12.4f} {'100.0':>8}% {total_tokens:>10} {tpt_total:>17.4f}"
        )

        results[dataset_name] = {
            "total_tokens": total_tokens,
            "total_time": total_time,
            "time_per_token_ms": tpt_total,
            "steps": {
                step: {
                    "time": step_timings.get(step, 0.0),
                    "count": step_counts.get(step, 0),
                    "pct": step_timings.get(step, 0.0) / total_time * 100
                    if total_time > 0
                    else 0.0,
                    "time_per_token_ms": step_timings.get(step, 0.0)
                    / step_counts.get(step, 1)
                    * 1000,
                }
                for step in step_timings
                if step != "total"
            },
        }

    return results


def run_p4_3(schema: Schema, datasets: dict[str, list[str]]) -> dict[str, Any]:
    """P4.3: Compare analyzers on A/B/C/D."""
    print("\n" + "=" * 80)
    print("P4.3 Analyzer Comparison on A/B/C/D")
    print("=" * 80)

    analyzers = {
        "StandardAnalyzer": StandardAnalyzer(),
        "StemmingAnalyzer": StemmingAnalyzer(),
        "LanguageAnalyzer": LanguageAnalyzer(lang="en"),
    }

    results: dict[str, Any] = {}

    for analyzer_name, analyzer in analyzers.items():
        print(f"\n--- {analyzer_name} ---")
        profiler = AnalyzerStepProfiler(analyzer)
        analyzer_results: dict[str, dict[str, Any]] = {}

        for dataset_name, texts in datasets.items():
            profiler._reset()
            for text in texts:
                profiler.profile_text(text)
            result = profiler.to_dict()
            total_time = result["total_time"]
            token_count = result["token_count"]
            throughput = token_count / total_time if total_time > 0 else 0
            tpt = total_time / token_count * 1000 if token_count > 0 else 0

            print(
                f"  Dataset {dataset_name}: {total_time:.4f}s, {token_count} tokens, {throughput:.0f} tokens/s, {tpt:.4f} ms/token"
            )

            analyzer_results[dataset_name] = {
                "total_time": total_time,
                "token_count": token_count,
                "throughput": throughput,
                "time_per_token_ms": tpt,
                "steps": result.get("steps", {}),
            }

        results[analyzer_name] = analyzer_results

    return results


def run_p4_4(datasets: dict[str, list[str]]) -> dict[str, Any]:
    """P4.4: Test stemmers on millions of tokens."""
    print("\n" + "=" * 80)
    print("P4.4 Stemmer Benchmark on millions of tokens")
    print("=" * 80)

    bench = StemmerBenchmark()

    # Use all datasets for a large corpus
    all_texts = []
    for texts in datasets.values():
        all_texts.extend(texts)

    # Run on 2 million tokens worth of text
    target_tokens = 2_000_000
    collected = []
    token_count = 0
    for text in all_texts:
        collected.append(text)
        token_count += len(text.split())
        if token_count >= target_tokens:
            break

    print(f"\nRunning on {token_count:,} tokens...")
    bench.run(collected, warmup=True)
    print(bench.report())

    return bench.to_dict()


def main() -> dict[str, Any]:
    """Run all P4 benchmarks and return results."""
    print("Generating synthetic datasets...")
    gen = SyntheticDatasetGenerator(seed=42)
    datasets = gen.generate_all(count=50000)  # 50k texts per dataset
    print(gen.report(datasets))

    # Create a simple schema for profiling
    schema = Schema(
        City=TEXT(stored=True),
        Company=TEXT(stored=True),
        Country=TEXT(stored=True),
    )

    results: dict[str, Any] = {}

    # Run P4.1/P4.2
    results["p4_1_2"] = run_p4_1_2(schema, datasets)

    # Run P4.3
    results["p4_3"] = run_p4_3(schema, datasets)

    # Run P4.4
    results["p4_4"] = run_p4_4(datasets)

    # Save results to JSON
    output_path = "benchmark_results_p4.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    return results


if __name__ == "__main__":
    main()
