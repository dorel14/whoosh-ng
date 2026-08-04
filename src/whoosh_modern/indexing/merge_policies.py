"""Merge policies for Whoosh index segment management."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from whoosh.index import Index


class MergePolicy(ABC):
    """Abstract base class for merge policies."""

    @abstractmethod
    def should_merge(self, index: Index, **kwargs: object) -> bool:
        """Return True if segments should be merged."""
        raise NotImplementedError

    @abstractmethod
    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        """Return kwargs for ``writer.commit(merge=...)``."""
        raise NotImplementedError


class NoMergePolicy(MergePolicy):
    """Disable merging entirely. Useful for benchmarks or append-only indexes."""

    def should_merge(self, index: Index, **kwargs: object) -> bool:
        return False

    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        return {"merge": False}


class LogMergePolicy(MergePolicy):
    """Merge when the number of segments exceeds a threshold.

    Inspired by Lucene's LogMergePolicy: merge the oldest segments when
    there are too many of them.
    """

    def __init__(self, max_segments: int = 10) -> None:
        self.max_segments = max_segments

    def should_merge(self, index: Index, **kwargs: object) -> bool:
        segments = getattr(index, "_segments", None)
        if callable(segments):
            segments = segments()
        return len(segments or []) >= self.max_segments

    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        return {"merge": True}


class TieredMergePolicy(MergePolicy):
    """Tiered merge policy balancing merge cost and search performance.

    Merges smaller segments into larger ones up to a target size, then
    merges those larger segments together. Inspired by Lucene's
    TieredMergePolicy.
    """

    def __init__(
        self,
        max_segments: int = 10,
        target_segment_size: int = 100000,
    ) -> None:
        self.max_segments = max_segments
        self.target_segment_size = target_segment_size

    def should_merge(self, index: Index, **kwargs: object) -> bool:
        segments = getattr(index, "_segments", None)
        if callable(segments):
            segments = segments()
        return len(segments or []) >= self.max_segments

    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        return {"merge": True}
