# Benchmark reporting module for Whoosh-NG
# Generates CSV/JSON reports from benchmark results.

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    name: str
    category: str  # indexing, querying, ranking
    metric: str  # docs_per_sec, queries_per_sec, p95_latency, peak_rss_mb
    value: float
    unit: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BenchmarkReport:
    """Collects benchmark results and writes them to CSV/JSON."""

    def __init__(self, title: str = "whoosh-benchmark") -> None:
        self.title = title
        self.results: list[BenchmarkResult] = []

    def add(self, result: BenchmarkResult) -> None:
        self.results.append(result)

    def to_csv(self, path: str) -> None:
        if not self.results:
            return
        fieldnames = ["name", "category", "metric", "value", "unit", "extra"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.results:
                row = r.to_dict()
                row["extra"] = json.dumps(row.get("extra", {}), ensure_ascii=False)
                writer.writerow(row)

    def to_json(self, path: str) -> None:
        payload = {
            "title": self.title,
            "results": [r.to_dict() for r in self.results],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def summary(self) -> str:
        lines = [f"Benchmark report: {self.title}"]
        for r in self.results:
            lines.append(f"  [{r.category}] {r.metric}: {r.value:.3f} {r.unit} ({r.name})")
        return "\n".join(lines)
