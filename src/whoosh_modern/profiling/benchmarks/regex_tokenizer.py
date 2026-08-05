"""P5.1 Fast RegexTokenizer benchmark.

Tests:
- Current regex
- Compiled global regex
- Manual Python tokenizer
- C extension (if available)

Measures:
- tokens/s
- time/token
- allocations/token
"""

from __future__ import annotations

import re
import sys
import time
from typing import Any, Callable, Dict, List, Tuple


class FastRegexTokenizer:
    """Optimized regex tokenizer using compiled global regex."""

    _compiled = re.compile(r"\w+(\.?\w+)*", re.UNICODE)

    def __call__(self, text: str, **kwargs: Any) -> List[Any]:
        return list(self._compiled.finditer(text))


class ManualTokenizer:
    """Manual Python tokenizer without regex."""

    def __call__(self, text: str, **kwargs: Any) -> List[Any]:
        tokens = []
        current = []
        for char in text:
            if char.isalnum() or char == ".":
                current.append(char)
            else:
                if current:
                    tokens.append("".join(current))
                    current = []
        if current:
            tokens.append("".join(current))
        return tokens


def benchmark_tokenizer(name: str, tokenizer: Callable, texts: List[str], iterations: int = 3) -> Dict[str, Any]:
    """Benchmark a tokenizer on given texts."""
    times = []
    token_counts = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        total_tokens = 0
        for text in texts:
            tokens = list(tokenizer(text))
            total_tokens += len(tokens)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        token_counts.append(total_tokens)

    avg_time = sum(times) / len(times)
    avg_tokens = sum(token_counts) / len(times)
    throughput = avg_tokens / avg_time if avg_time > 0 else 0
    tpt = avg_time / avg_tokens * 1000 if avg_tokens > 0 else 0

    return {
        "name": name,
        "avg_time": avg_time,
        "avg_tokens": avg_tokens,
        "throughput": throughput,
        "time_per_token_ms": tpt,
    }


def run_p5_1(datasets: Dict[str, List[str]]) -> Dict[str, Any]:
    """Run P5.1: Fast RegexTokenizer benchmark."""
    print("=" * 80)
    print("P5.1 Fast RegexTokenizer Benchmark")
    print("=" * 80)

    results = {}

    for dataset_name, texts in datasets.items():
        print(f"\n--- Dataset {dataset_name} ({len(texts)} texts) ---")
        dataset_results = []

        # Current regex (whoosh default)
        from whoosh.analysis.tokenizers import RegexTokenizer
        current_tokenizer = RegexTokenizer()
        dataset_results.append(benchmark_tokenizer("Current Regex", current_tokenizer, texts))

        # Compiled global regex
        dataset_results.append(benchmark_tokenizer("Compiled Global", FastRegexTokenizer(), texts))

        # Manual Python tokenizer
        dataset_results.append(benchmark_tokenizer("Manual Python", ManualTokenizer(), texts))

        # Try C extension
        try:
            import re2
            class Re2Tokenizer:
                def __call__(self, text: str, **kwargs: Any) -> List[Any]:
                    return list(re2.findall(r"\w+(\.?\w+)*", text))
            dataset_results.append(benchmark_tokenizer("C Extension (re2)", Re2Tokenizer(), texts))
        except ImportError:
            print("  C Extension (re2): not available")

        # Print table
        print(f"{'Tokenizer':<25} {'Time (s)':>12} {'Tokens':>12} {'Tokens/s':>12} {'Time/token (ms)':>18}")
        print("-" * 81)

        for result in dataset_results:
            print(f"  {result['name']:<23} {result['avg_time']:>12.4f} {result['avg_tokens']:>12.0f} {result['throughput']:>12.0f} {result['time_per_token_ms']:>17.4f}")

        results[dataset_name] = dataset_results

    return results
