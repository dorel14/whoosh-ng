"""Segment profiler for Whoosh-NG.

Provides per-segment analysis to identify segmentation overhead:
timing of segment-level operations plus structural metrics such as
document counts, deleted document counts and on-disk size for each
segment of an index.

Example::

    profiler = SegmentProfiler()
    profiler.start_segment(0)
    ...  # inspect / analyze the segment
    profiler.stop_segment()
    print(profiler.report())
"""

from __future__ import annotations

import time
from typing import Any


class SegmentProfiler:
    """Profiler for per-segment indexing/analysis costs.

    Tracks time spent analyzing each segment, and optionally records
    structural metrics (document count, deleted document count, size
    on disk) to identify segmentation and merge overhead.

    Example::

        profiler = SegmentProfiler()
        for segment_id in segment_ids:
            profiler.start_segment(segment_id)
            ...  # analyze the segment
            profiler.stop_segment()
        print(profiler.report())
    """

    def __init__(self) -> None:
        self._segment_times: dict[Any, float] = {}
        self._segment_counts: dict[Any, int] = {}
        self._segment_doc_counts: dict[Any, int] = {}
        self._segment_deleted_counts: dict[Any, int] = {}
        self._segment_sizes: dict[Any, int] = {}
        self._order: list[Any] = []
        self._active_segment: Any | None = None
        self._active_start: float | None = None

    def _ensure_tracked(self, segment_id: Any) -> None:
        if segment_id not in self._segment_times:
            self._segment_times[segment_id] = 0.0
            self._segment_counts[segment_id] = 0
            self._order.append(segment_id)

    def start_segment(self, segment_id: Any) -> None:
        """Start timing analysis of the given segment.

        :param segment_id: an identifier for the segment (index, name, etc).
        """
        if self._active_segment is not None:
            self.stop_segment()
        self._ensure_tracked(segment_id)
        self._active_segment = segment_id
        self._active_start = time.perf_counter()

    def stop_segment(self) -> float:
        """Stop timing the active segment.

        :returns: elapsed time in seconds for this segment step.
        """
        if self._active_segment is None or self._active_start is None:
            return 0.0
        elapsed = time.perf_counter() - self._active_start
        self._segment_times[self._active_segment] += elapsed
        self._segment_counts[self._active_segment] += 1
        self._active_segment = None
        self._active_start = None
        return elapsed

    def record_segment_stats(
        self,
        segment_id: Any,
        doc_count: int = 0,
        deleted_count: int = 0,
        size_bytes: int = 0,
    ) -> None:
        """Record structural metrics for a segment.

        :param segment_id: an identifier for the segment.
        :param doc_count: number of (live) documents in the segment.
        :param deleted_count: number of deleted documents in the segment.
        :param size_bytes: on-disk size of the segment's files, in bytes.
        """
        self._ensure_tracked(segment_id)
        self._segment_doc_counts[segment_id] = doc_count
        self._segment_deleted_counts[segment_id] = deleted_count
        self._segment_sizes[segment_id] = size_bytes

    def analyze_index(self, ix: Any) -> None:
        """Populate structural metrics from a live index's segments.

        Times the inspection of each segment and records its document
        count, deleted document count, and on-disk size.

        :param ix: an open Whoosh index (e.g. from
            :func:`whoosh.index.open_dir` / :func:`whoosh.index.create_in`).
        """
        with ix.reader() as reader:
            storage = reader.storage()
            for segment in reader.segments():
                segment_id = segment.segment_id()
                self.start_segment(segment_id)
                doc_count = segment.doc_count()
                deleted_count = segment.deleted_count()
                size_bytes = 0
                for filename in segment.list_files(storage):
                    try:
                        size_bytes += storage.file_length(filename)
                    except OSError:
                        continue
                self.stop_segment()
                self.record_segment_stats(
                    segment_id,
                    doc_count=doc_count,
                    deleted_count=deleted_count,
                    size_bytes=size_bytes,
                )

    @property
    def segment_ids(self) -> list[Any]:
        """Return tracked segment identifiers in first-seen order."""
        return list(self._order)

    @property
    def total_time(self) -> float:
        return sum(self._segment_times.values())

    @property
    def total_segments(self) -> int:
        return len(self._order)

    @property
    def total_documents(self) -> int:
        return sum(self._segment_doc_counts.values())

    @property
    def total_deleted(self) -> int:
        return sum(self._segment_deleted_counts.values())

    @property
    def total_size_bytes(self) -> int:
        return sum(self._segment_sizes.values())

    def report(self) -> str:
        """Return a human-readable profiling report."""
        lines: list[str] = []
        lines.append("Segment Profiling")
        lines.append("=" * 60)

        total_time = self.total_time
        for segment_id in self._order:
            elapsed = self._segment_times.get(segment_id, 0.0)
            count = self._segment_counts.get(segment_id, 0)
            docs = self._segment_doc_counts.get(segment_id, 0)
            deleted = self._segment_deleted_counts.get(segment_id, 0)
            size_bytes = self._segment_sizes.get(segment_id, 0)
            pct = (elapsed / total_time * 100) if total_time > 0 else 0.0
            bar = "#" * int(pct / 2)
            lines.append(f"  {segment_id!s:<24} ... {elapsed:>8.3f}s  ({pct:5.1f}%) {bar}")
            lines.append(
                f"    docs={docs}, deleted={deleted}, "
                f"size={size_bytes / 1024:.1f}KB, visits={count}"
            )

        lines.append("-" * 60)
        lines.append(f"  Total segments: {self.total_segments}")
        lines.append(f"  Total documents: {self.total_documents}")
        lines.append(f"  Total deleted: {self.total_deleted}")
        lines.append(f"  Total size: {self.total_size_bytes / 1024 / 1024:.2f} MB")
        lines.append(f"  Total time: {total_time:.3f}s")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return profiling data as a dictionary."""
        return {
            "total_time": round(self.total_time, 3),
            "total_segments": self.total_segments,
            "total_documents": self.total_documents,
            "total_deleted": self.total_deleted,
            "total_size_bytes": self.total_size_bytes,
            "segments": [
                {
                    "segment_id": str(segment_id),
                    "elapsed": round(self._segment_times.get(segment_id, 0.0), 3),
                    "visits": self._segment_counts.get(segment_id, 0),
                    "doc_count": self._segment_doc_counts.get(segment_id, 0),
                    "deleted_count": self._segment_deleted_counts.get(segment_id, 0),
                    "size_bytes": self._segment_sizes.get(segment_id, 0),
                }
                for segment_id in self._order
            ],
        }
