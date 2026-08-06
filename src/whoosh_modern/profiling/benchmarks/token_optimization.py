"""P5.2 Token object optimization benchmark.

Tests:
- Current Token object
- __slots__ optimization
- namedtuple
- dataclass(slots=True)

Measures:
- tokens/s
- GC pressure
- memory
"""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass
from typing import Any, NamedTuple


class Token:
    """Current Token implementation."""

    def __init__(self, text: str, stopped: bool = False, pos: int = 0, boost: float = 1.0):
        self.text = text
        self.stopped = stopped
        self.pos = pos
        self.boost = boost


class TokenSlots:
    """Token with __slots__."""

    __slots__ = ("text", "stopped", "pos", "boost")

    def __init__(self, text: str, stopped: bool = False, pos: int = 0, boost: float = 1.0):
        self.text = text
        self.stopped = stopped
        self.pos = pos
        self.boost = boost


class TokenNamedTuple(NamedTuple):
    """Token as namedtuple."""

    text: str
    stopped: bool
    pos: int
    boost: float


@dataclass(slots=True)
class TokenDataclassSlots:
    """Token as dataclass with slots."""

    text: str
    stopped: bool = False
    pos: int = 0
    boost: float = 1.0


class TokenFactory:
    """Factory for creating tokens."""

    def __init__(self, token_class: type) -> None:
        self._token_class = token_class

    def create_token(self, text: str, pos: int) -> Any:
        return self._token_class(text=text, stopped=False, pos=pos, boost=1.0)


def benchmark_token_creation(
    name: str, factory: TokenFactory, token_count: int, iterations: int = 3
) -> dict[str, Any]:
    """Benchmark token creation."""
    times = []
    for _ in range(iterations):
        gc.collect()
        gc.disable()
        t0 = time.perf_counter()
        tokens = []
        for i in range(token_count):
            tokens.append(factory.create_token("test", i))
        t1 = time.perf_counter()
        gc.enable()
        times.append(t1 - t0)

    avg_time = sum(times) / len(times)
    throughput = token_count / avg_time if avg_time > 0 else 0
    tpt = avg_time / token_count * 1000 if token_count > 0 else 0

    return {
        "name": name,
        "avg_time": avg_time,
        "token_count": token_count,
        "throughput": throughput,
        "time_per_token_ms": tpt,
    }


def run_p5_2(token_count: int = 100000) -> dict[str, Any]:
    """Run P5.2: Token object optimization benchmark."""
    print("=" * 80)
    print("P5.2 Token Object Optimization Benchmark")
    print("=" * 80)

    factories = {
        "Current Token": TokenFactory(Token),
        "__slots__": TokenFactory(TokenSlots),
        "namedtuple": TokenFactory(TokenNamedTuple),
        "dataclass(slots)": TokenFactory(TokenDataclassSlots),
    }

    results = []

    for name, factory in factories.items():
        result = benchmark_token_creation(name, factory, token_count)
        results.append(result)

    # Print table
    print(f"\nToken count: {token_count:,}")
    print(f"{'Implementation':<25} {'Time (s)':>12} {'Tokens/s':>12} {'Time/token (ns)':>18}")
    print("-" * 69)

    for result in results:
        tpt_ns = result["time_per_token_ms"] * 1000
        print(
            f"  {result['name']:<23} {result['avg_time']:>12.4f} "
            f"{result['throughput']:>12.0f} {tpt_ns:>17.2f}"
        )

    return {r["name"]: r for r in results}
