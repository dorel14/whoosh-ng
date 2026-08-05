"""CommitProfiler V2 for Whoosh-NG.

Uses the non-invasive ``callback`` hook of ``SegmentWriter.commit()``
to measure commit substeps, and optional monkey-patching of internal
methods for finer granularity:

- segment_merge
- flush
- write_postings
  - add_posting
  - write_block
  - finish_postings
- write_terms
- write_vectors
- toc_update
- finish

Term statistics can be collected alongside timing when
``collect_term_stats=True``.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable, Sequence
from typing import Any


class TermStatistics:
    """Collected statistics about posting lists and blocks.

    This is used to distinguish normal data-driven fragmentation from
    a storage-strategy issue before changing the index format.
    """

    def __init__(self) -> None:
        self.terms: int = 0
        self.posting_lists: int = 0
        self.postings: int = 0
        self.blocks: int = 0
        self._lengths: list[int] = []
        self._blocks_per_term: list[int] = []
        self._size_buckets: dict[str, int] = {
            "1": 0,
            "2-4": 0,
            "5-8": 0,
            "9-16": 0,
            "17-32": 0,
            "33-64": 0,
            "65-128": 0,
            "129+": 0,
        }
        self._size_bucket_blocks: dict[str, int] = {
            "1": 0,
            "2-4": 0,
            "5-8": 0,
            "9-16": 0,
            "17-32": 0,
            "33-64": 0,
            "65-128": 0,
            "129+": 0,
        }

    def record_term(self, posting_count: int, block_count: int) -> None:
        self.terms += 1
        self.postings += posting_count
        self.blocks += block_count
        self._lengths.append(posting_count)
        self._blocks_per_term.append(block_count)

        if posting_count == 1:
            bucket = "1"
        elif posting_count <= 4:
            bucket = "2-4"
        elif posting_count <= 8:
            bucket = "5-8"
        elif posting_count <= 16:
            bucket = "9-16"
        elif posting_count <= 32:
            bucket = "17-32"
        elif posting_count <= 64:
            bucket = "33-64"
        elif posting_count <= 128:
            bucket = "65-128"
        else:
            bucket = "129+"
        self._size_buckets[bucket] += 1
        self._size_bucket_blocks[bucket] += block_count

    @property
    def avg_postings_per_term(self) -> float:
        if not self.terms:
            return 0.0
        return self.postings / self.terms

    @property
    def avg_blocks_per_term(self) -> float:
        if not self.terms:
            return 0.0
        return self.blocks / self.terms

    def percentile(self, q: float) -> int:
        if not self._lengths:
            return 0
        s = sorted(self._lengths)
        k = int(len(s) * q)
        if k >= len(s):
            return s[-1]
        return s[k]

    def report(self) -> str:
        lines: list[str] = []
        lines.append("TERM STATISTICS")
        lines.append("===============")
        lines.append(f"unique terms       : {self.terms}")
        lines.append(f"posting lists      : {self.posting_lists}")
        lines.append(f"postings           : {self.postings}")
        lines.append(f"blocks             : {self.blocks}")
        lines.append(f"avg postings/term  : {self.avg_postings_per_term:.1f}")
        lines.append(f"p50 postings/term  : {self.percentile(0.5)}")
        lines.append(f"p95 postings/term  : {self.percentile(0.95)}")
        lines.append(f"p99 postings/term  : {self.percentile(0.99)}")
        lines.append(f"max postings/term  : {self.percentile(1.0)}")
        lines.append(f"avg blocks/term    : {self.avg_blocks_per_term:.1f}")
        lines.append("")
        lines.append("POSTING LIST SIZE DISTRIBUTION")
        lines.append("------------------------------")
        for bucket, label in (
            ("1", "1 posting"),
            ("2-4", "2-4 postings"),
            ("5-8", "5-8 postings"),
            ("9-16", "9-16 postings"),
            ("17-32", "17-32 postings"),
            ("33-64", "33-64 postings"),
            ("65-128", "65-128 postings"),
            ("129+", "129+ postings"),
        ):
            count = self._size_buckets[bucket]
            pct = (count / self.terms * 100) if self.terms else 0.0
            lines.append(f"  {label:<16} : {count:>8} ({pct:5.1f}%)")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "terms": self.terms,
            "posting_lists": self.posting_lists,
            "postings": self.postings,
            "blocks": self.blocks,
            "avg_postings_per_term": round(self.avg_postings_per_term, 2),
            "p50_postings_per_term": self.percentile(0.5),
            "p95_postings_per_term": self.percentile(0.95),
            "p99_postings_per_term": self.percentile(0.99),
            "max_postings_per_term": self.percentile(1.0),
            "avg_blocks_per_term": round(self.avg_blocks_per_term, 2),
            "size_buckets": dict(self._size_buckets),
            "size_bucket_blocks": dict(self._size_bucket_blocks),
        }


class _CommitStep:
    __slots__ = ("name", "_start", "_elapsed", "_count")

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

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @property
    def count(self) -> int:
        return self._count


class CommitProfilerV2:
    """Detailed commit profiler using the writer ``callback`` hook.

    Example::

        profiler = CommitProfilerV2()
        writer.commit(callback=profiler.callback)
        print(profiler.report())
    """

    def __init__(self, collect_term_stats: bool = False) -> None:
        self._steps: OrderedDict[str, _CommitStep] = OrderedDict()
        self._active: _CommitStep | None = None
        self._segment_count: int = 0
        self._bytes_written: int = 0
        self.collect_term_stats = collect_term_stats
        self.term_stats = TermStatistics() if collect_term_stats else None
        self.add_posting_count: int = 0
        self.write_block_count: int = 0
        self.finish_postings_count: int = 0

    def _step(self, name: str) -> _CommitStep:
        if self._active is not None:
            self._active.stop()
        if name not in self._steps:
            self._steps[name] = _CommitStep(name)
        self._active = self._steps[name]
        self._active.start()
        return self._active

    def callback(self, stage: str, **kwargs: Any) -> None:
        """Callback compatible with ``SegmentWriter.commit(callback=...)``."""
        if stage == "merge":
            self._step("segment_merge")
        elif stage == "segment" and kwargs.get("started"):
            self._step("flush")
        elif stage == "toc" and kwargs.get("started"):
            self._step("toc_update")
        elif stage in ("segment", "toc", "finish"):
            pass
        else:
            self._step(stage)

    def record_segment(self, size_bytes: int) -> None:
        self._segment_count += 1
        self._bytes_written += size_bytes

    def profile(self, writer: Any) -> None:
        """Profile a commit on the given writer.

        Uses ``_TimedSegmentWriter`` to instrument internal methods
        and the writer ``callback`` hook.
        """
        ctx = _TimedSegmentWriter(writer, self)
        with ctx:
            writer.commit(callback=self.callback)
        self.stop_active()

    def stop_active(self) -> None:
        if self._active is not None:
            self._active.stop()
            self._active = None

    @property
    def total_time(self) -> float:
        return sum(s.elapsed for s in self._steps.values())

    @property
    def segment_count(self) -> int:
        return self._segment_count

    @property
    def bytes_written(self) -> int:
        return self._bytes_written

    @property
    def bytes_per_second(self) -> float:
        if self.total_time > 0:
            return self._bytes_written / self.total_time
        return 0.0

    def report(self) -> str:
        lines: list[str] = []
        lines.append("Commit Profiling V2")
        lines.append("=" * 55)

        total_time = self.total_time
        preferred_order = [
            "segment_merge",
            "flush",
            "write_postings",
            "add_posting",
            "write_block",
            "finish_postings",
            "write_terms",
            "write_vectors",
            "toc_update",
            "finish",
        ]
        ordered_names = [n for n in preferred_order if n in self._steps]
        ordered_names += [n for n in self._steps if n not in preferred_order]

        for name in ordered_names:
            step = self._steps[name]
            pct = (step.elapsed / total_time * 100) if total_time > 0 else 0.0
            bar = "#" * int(pct / 2)
            suffix = f" x{step.count}" if step.count > 1 else ""
            lines.append(f"  {name:<20} ... {step.elapsed:>8.3f}s  ({pct:5.1f}%){suffix} {bar}")

        lines.append("-" * 55)
        lines.append(f"  {'Total':<20} ... {total_time:>8.3f}s")
        lines.append(f"  Segments: {self._segment_count}")
        lines.append(f"  Bytes written: {self._bytes_written / 1024 / 1024:.1f} MB")
        lines.append(f"  Write speed: {self.bytes_per_second / 1024 / 1024:.1f} MB/s")
        lines.append(f"  add_posting calls: {self.add_posting_count}")
        lines.append(f"  write_block calls: {self.write_block_count}")
        lines.append(f"  finish_postings calls: {self.finish_postings_count}")
        if self.term_stats is not None:
            lines.append("")
            lines.append(self.term_stats.report())
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "total_time": round(self.total_time, 3),
            "segment_count": self._segment_count,
            "bytes_written": self._bytes_written,
            "bytes_per_second": round(self.bytes_per_second, 1),
            "add_posting_count": self.add_posting_count,
            "write_block_count": self.write_block_count,
            "finish_postings_count": self.finish_postings_count,
            "steps": {
                name: {
                    "elapsed": round(s.elapsed, 3),
                    "count": s.count,
                }
                for name, s in self._steps.items()
            },
        }
        if self.term_stats is not None:
            data["term_stats"] = self.term_stats.to_dict()
        return data


class _TimedSegmentWriter:
    """Wrapper around a segment writer that adds fine-grained commit timing.

    Wraps ``_flush_segment`` and ``_assemble_segment`` to measure:
    - flush / per-doc close
    - postings write
      - add_posting
      - write_block
      - finish_postings
    - terms write
    - vectors / compound assembly

    When ``collect_term_stats`` is enabled on the profiler, it also wraps
    the underlying postings writer to collect term-level statistics.
    """

    def __init__(self, writer: Any, profiler: CommitProfilerV2) -> None:
        self._writer = writer
        self._profiler = profiler
        self._orig_flush = writer._flush_segment
        self._orig_assemble = writer._assemble_segment
        self._orig_close_segment = writer._close_segment
        self._orig_start_field = None

    def __enter__(self) -> _TimedSegmentWriter:
        self._patch()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self._unpatch()

    def _patch_postings_writer(self, postwriter: Any) -> None:
        """Instrument a postings writer for term stats and sub-step timing."""
        profiler = self._profiler
        term_stats = profiler.term_stats

        orig_start_postings = postwriter.start_postings
        orig_add_posting = postwriter.add_posting
        orig_write_block = postwriter._write_block
        orig_finish_postings = postwriter.finish_postings

        state: dict[str, Any] = {
            "current_postings": 0,
            "current_blocks": 0,
        }

        def start_postings(format_, terminfo):
            state["current_postings"] = 0
            state["current_blocks"] = 0
            return orig_start_postings(format_, terminfo)

        def add_posting(id_, weight, vbytes, length=None):
            state["current_postings"] += 1
            if len(postwriter._ids) >= postwriter._blocklimit - 1:
                state["current_blocks"] += 1
            profiler.add_posting_count += 1
            return orig_add_posting(id_, weight, vbytes, length)

        def write_block(last=False):
            state["current_blocks"] += 1
            profiler.write_block_count += 1
            return orig_write_block(last=last)

        def finish_postings():
            posting_count = state["current_postings"]
            block_count = state["current_blocks"] or 1
            if term_stats is not None:
                term_stats.record_term(posting_count, block_count)
            profiler.finish_postings_count += 1
            state["current_postings"] = 0
            state["current_blocks"] = 0
            return orig_finish_postings()

        postwriter.start_postings = start_postings
        postwriter.add_posting = add_posting
        postwriter._write_block = write_block
        postwriter.finish_postings = finish_postings

    def _patch(self) -> None:
        writer = self._writer
        profiler = self._profiler
        orig_flush = self._orig_flush
        orig_assemble = self._orig_assemble
        codec_length_stats = getattr(writer.codec, "length_stats", False)

        if profiler.collect_term_stats:
            orig_start_field = writer.fieldwriter.start_field

            def start_field(fieldname, fieldobj):
                r = orig_start_field(fieldname, fieldobj)
                postwriter = getattr(writer.fieldwriter, "_postwriter", None)
                if (
                    postwriter is not None
                    and getattr(postwriter, "_profiling_patched", False) is False
                ):
                    postwriter._profiling_patched = True
                    self._patch_postings_writer(postwriter)
                return r

            writer.fieldwriter.start_field = start_field
            self._orig_start_field = orig_start_field
        else:
            self._orig_start_field = None

        def _timed_flush() -> None:
            profiler._step("flush")
            writer.perdocwriter.close()
            profiler.stop_active()

            if codec_length_stats:
                profiler._step("perdoc_reader")
                pdr = writer.per_document_reader()
                profiler.stop_active()
            else:
                pdr = None

            profiler._step("write_postings")
            postings = writer.pool.iter_postings()
            writer.fieldwriter.add_postings(writer.schema, pdr, postings)
            profiler.stop_active()

            profiler._step("write_terms")
            writer.fieldwriter.close()
            profiler.stop_active()

            if pdr is not None:
                profiler._step("perdoc_reader_close")
                pdr.close()
                profiler.stop_active()

            profiler._step("pool_cleanup")
            writer.pool.cleanup()
            profiler.stop_active()

        def _timed_assemble() -> None:
            profiler._step("write_vectors")
            orig_assemble()
            profiler.stop_active()

        writer._flush_segment = _timed_flush
        writer._assemble_segment = _timed_assemble

    def _unpatch(self) -> None:
        writer = self._writer
        writer._flush_segment = self._orig_flush
        writer._assemble_segment = self._orig_assemble
        writer._close_segment = self._orig_close_segment

        if getattr(self, "_orig_start_field", None) is not None:
            writer.fieldwriter.start_field = self._orig_start_field


def profile_commit(
    writer: Any,
    collect_term_stats: bool = False,
) -> CommitProfilerV2:
    """Profile a single commit call on a segment writer.

    Uses both the built-in ``callback`` hook and, when available,
    fine-grained wrapping of internal methods.

    :param writer: ``SegmentWriter`` or compatible writer.
    :param collect_term_stats: if ``True``, instrument the underlying
        postings writer to collect term-level statistics.
    :returns: populated ``CommitProfilerV2``.
    """
    profiler = CommitProfilerV2(collect_term_stats=collect_term_stats)

    def callback(stage: str, **kwargs: Any) -> None:
        profiler.callback(stage, **kwargs)

    ctx = _TimedSegmentWriter(writer, profiler)
    with ctx:
        writer.commit(callback=callback)

    profiler.stop_active()
    return profiler
