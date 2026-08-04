"""Core IndexProfiler with context manager and step timers."""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any


class StepTimer:
    """Measures elapsed time for a single profiling step."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._start: float | None = None
        self._elapsed: float = 0.0
        self._count: int = 0

    def start(self) -> None:
        if self._start is None:
            self._start = time.perf_counter()

    def stop(self) -> float:
        if self._start is not None:
            delta = time.perf_counter() - self._start
            self._elapsed += delta
            self._count += 1
            self._start = None
            return delta
        return 0.0

    def reset(self) -> None:
        self._start = None
        self._elapsed = 0.0
        self._count = 0

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @property
    def count(self) -> int:
        return self._count

    def __enter__(self) -> StepTimer:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.stop()


class IndexProfiler:
    """Profiling context manager for Whoosh indexing pipelines.

    Measures elapsed time for each indexing step and produces
    a human-readable report.

    Example::

        with IndexProfiler() as profiler:
            with profiler.step("reading"):
                docs = list(source.iter_documents())
            with profiler.step("analyzing"):
                for doc in docs:
                    writer.add_document(**doc)

        print(profiler.report())
    """

    def __init__(self) -> None:
        self._steps: OrderedDict[str, StepTimer] = OrderedDict()
        self._active_step: StepTimer | None = None
        self._start_time: float | None = None
        self._end_time: float | None = None
        self._documents_indexed: int = 0

    def __enter__(self) -> IndexProfiler:
        self._start_time = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self._end_time = time.perf_counter()
        if self._active_step is not None:
            self._active_step.stop()
            self._active_step = None

    def step(self, name: str) -> StepTimer:
        """Start a named profiling step.

        Usage::

            with profiler.step("analyzing"):
                ...
        """
        if self._active_step is not None:
            self._active_step.stop()
        if name not in self._steps:
            self._steps[name] = StepTimer(name)
        self._active_step = self._steps[name]
        self._active_step.start()
        return self._active_step

    def add_documents(self, count: int) -> None:
        """Record the number of documents indexed."""
        self._documents_indexed += count

    @property
    def documents_indexed(self) -> int:
        return self._documents_indexed

    @property
    def total_time(self) -> float:
        if self._start_time is None:
            return 0.0
        end = self._end_time if self._end_time is not None else time.perf_counter()
        return end - self._start_time

    @property
    def docs_per_second(self) -> float:
        if self.total_time == 0:
            return 0.0
        return self._documents_indexed / self.total_time

    def report(self) -> str:
        """Return a human-readable profiling report."""
        lines: list[str] = []
        lines.append(f"Documents Indexed : {self._documents_indexed}")
        lines.append("")

        max_name_len = max((len(s.name) for s in self._steps.values()), default=0)
        max_time_len = 0
        for s in self._steps.values():
            time_len = len(f"{s.elapsed:.1f}s")
            if time_len > max_time_len:
                max_time_len = time_len

        for s in self._steps.values():
            pct = (s.elapsed / self.total_time * 100) if self.total_time > 0 else 0.0
            bar = "#" * int(pct / 2)
            lines.append(
                f"{s.name:<{max_name_len}} ... "
                f"{s.elapsed:>{max_time_len}.1f}s  "
                f"({pct:5.1f}%) {bar}"
            )

        lines.append("")
        lines.append(f"{'Total':<{max_name_len}} ... {self.total_time:>{max_time_len}.1f}s")
        lines.append(f"{'Throughput':<{max_name_len}} ... {self.docs_per_second:.1f} docs/s")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return profiling data as a dictionary."""
        return {
            "total_time": round(self.total_time, 3),
            "documents_indexed": self._documents_indexed,
            "docs_per_second": round(self.docs_per_second, 1),
            "steps": {
                name: {"elapsed": round(s.elapsed, 3), "count": s.count}
                for name, s in self._steps.items()
            },
        }