"""Advanced metrics collection for index profiling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepMetrics:
    """Metrics for a single indexing step."""

    name: str
    time_seconds: float = 0.0
    cpu_time_seconds: float = 0.0
    memory_start_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_end_mb: float = 0.0
    documents_processed: int = 0
    tokens_generated: int = 0
    bytes_written: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects detailed metrics for each indexing step.

    Tracks time, memory, document counts, token counts,
    and arbitrary extra data per step.
    """

    def __init__(self) -> None:
        self._steps: dict[str, StepMetrics] = {}
        self._current: StepMetrics | None = None

    def start_step(self, name: str) -> StepMetrics:
        """Begin recording metrics for a step."""
        if name not in self._steps:
            self._steps[name] = StepMetrics(name=name)
        self._current = self._steps[name]
        return self._current

    def stop_step(self) -> StepMetrics | None:
        """Stop recording the current step."""
        step = self._current
        self._current = None
        return step

    def record_documents(self, count: int) -> None:
        if self._current is not None:
            self._current.documents_processed += count

    def record_tokens(self, count: int) -> None:
        if self._current is not None:
            self._current.tokens_generated += count

    def record_bytes(self, count: int) -> None:
        if self._current is not None:
            self._current.bytes_written += count

    def record_memory(self, start_mb: float, peak_mb: float, end_mb: float) -> None:
        if self._current is not None:
            self._current.memory_start_mb = start_mb
            self._current.memory_peak_mb = peak_mb
            self._current.memory_end_mb = end_mb

    def record_extra(self, key: str, value: Any) -> None:
        if self._current is not None:
            self._current.extra[key] = value

    def get_report(self) -> str:
        """Return a formatted metrics report."""
        lines: list[str] = []
        for step in self._steps.values():
            lines.append(f"--- {step.name} ---")
            lines.append(f"  Time           : {step.time_seconds:.3f}s")
            lines.append(f"  Documents      : {step.documents_processed}")
            lines.append(f"  Tokens         : {step.tokens_generated}")
            lines.append(f"  Bytes Written  : {step.bytes_written}")
            lines.append(f"  Memory Start   : {step.memory_start_mb:.1f} MB")
            lines.append(f"  Memory Peak    : {step.memory_peak_mb:.1f} MB")
            lines.append(f"  Memory End     : {step.memory_end_mb:.1f} MB")
            if step.extra:
                for k, v in step.extra.items():
                    lines.append(f"  {k} : {v}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            name: {
                "time_seconds": s.time_seconds,
                "documents_processed": s.documents_processed,
                "tokens_generated": s.tokens_generated,
                "bytes_written": s.bytes_written,
                "memory_start_mb": s.memory_start_mb,
                "memory_peak_mb": s.memory_peak_mb,
                "memory_end_mb": s.memory_end_mb,
                "extra": s.extra,
            }
            for name, s in self._steps.items()
        }
