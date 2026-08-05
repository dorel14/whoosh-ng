"""Synthetic datasets for micro-benchmarks.

Generates controlled texts with known token counts:
- Dataset A: ~2 tokens
- Dataset B: ~50 tokens
- Dataset C: ~500 tokens
- Dataset D: ~1000+ tokens

Usage:
    from whoosh_modern.profiling import SyntheticDatasetGenerator
    gen = SyntheticDatasetGenerator()
    dataset_a = gen.generate_a(count=10000)
"""

from __future__ import annotations

import random
import string
from typing import Any


class SyntheticDatasetGenerator:
    """Generate synthetic texts with controlled token counts."""

    def __init__(self, seed: int = 42) -> None:
        self._random = random.Random(seed)
        self._words = [
            "alpha",
            "bravo",
            "charlie",
            "delta",
            "echo",
            "foxtrot",
            "golf",
            "hotel",
            "india",
            "juliett",
            "kilo",
            "lima",
            "mike",
            "november",
            "oscar",
            "papa",
            "quebec",
            "romeo",
            "sierra",
            "tango",
            "uniform",
            "victor",
            "whiskey",
            "xray",
            "yankee",
            "zulu",
            "quick",
            "brown",
            "fox",
            "jumps",
            "over",
            "lazy",
            "dog",
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "have",
            "would",
            "could",
            "should",
        ]

    def _random_text(self, target_tokens: int) -> str:
        """Generate random text with approximately target_tokens tokens."""
        if target_tokens <= 0:
            return ""
        words = self._random.choices(self._words, k=target_tokens)
        return " ".join(words)

    def generate_a(self, count: int = 10000) -> list[str]:
        """Dataset A: ~2 tokens per text."""
        return [self._random_text(2) for _ in range(count)]

    def generate_b(self, count: int = 10000) -> list[str]:
        """Dataset B: ~50 tokens per text."""
        return [self._random_text(50) for _ in range(count)]

    def generate_c(self, count: int = 10000) -> list[str]:
        """Dataset C: ~500 tokens per text."""
        return [self._random_text(500) for _ in range(count)]

    def generate_d(self, count: int = 10000) -> list[str]:
        """Dataset D: ~1000+ tokens per text."""
        return [self._random_text(1200) for _ in range(count)]

    def generate_all(self, count: int = 10000) -> dict[str, list[str]]:
        """Generate all datasets.

        :returns: dict with keys A, B, C, D
        """
        return {
            "A": self.generate_a(count),
            "B": self.generate_b(count),
            "C": self.generate_c(count),
            "D": self.generate_d(count),
        }

    def report(self, datasets: dict[str, list[str]]) -> str:
        """Report token counts per dataset."""
        lines = ["Synthetic Dataset Report", "=" * 50, ""]
        for name, texts in datasets.items():
            total_tokens = sum(len(text.split()) for text in texts)
            avg_tokens = total_tokens / len(texts) if texts else 0
            lines.append(f"Dataset {name}: {len(texts)} texts, avg {avg_tokens:.1f} tokens/text")
        return "\n".join(lines)
