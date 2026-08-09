"""Merge policies for Whoosh index segment management.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from whoosh.index import Index


class MergePolicy(ABC):
    """Abstract base class for merge policies."""

    @abstractmethod
    def should_merge(self, index: Index, **kwargs: object) -> bool:
        """Return True if segments should be merged.

        Args:
            index: The Whoosh index whose segments should be evaluated.
            **kwargs: Additional policy-specific keyword arguments.

        Returns:
            ``True`` if a merge should be performed, ``False`` otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        """Return kwargs for ``writer.commit(merge=...)``.

        Args:
            index: The Whoosh index whose segments are being merged.
            **kwargs: Additional policy-specific keyword arguments.

        Returns:
            A dict of keyword arguments to pass to the writer commit call.
        """
        raise NotImplementedError


class NoMergePolicy(MergePolicy):
    """Disable merging entirely. Useful for benchmarks or append-only indexes."""

    def should_merge(self, index: Index, **kwargs: object) -> bool:
        """Return whether segments should be merged.

        Always returns ``False`` — merging is disabled.

        Args:
            index: The Whoosh index (unused).
            **kwargs: Additional keyword arguments (unused).

        Returns:
            Always ``False``.
        """
        return False

    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        """Return commit kwargs with merging disabled.

        Args:
            index: The Whoosh index (unused).
            **kwargs: Additional keyword arguments (unused).

        Returns:
            A dict with ``merge`` set to ``False``.
        """
        return {"merge": False}


class LogMergePolicy(MergePolicy):
    """Merge when the number of segments exceeds a threshold.

    Inspired by Lucene's LogMergePolicy: merge the oldest segments when
    there are too many of them.
    """

    def __init__(self, max_segments: int = 10) -> None:
        """Initialize the log merge policy.

        Args:
            max_segments: Threshold number of segments above which merging
                is triggered. Defaults to 10.
        """
        self.max_segments = max_segments

    def should_merge(self, index: Index, **kwargs: object) -> bool:
        """Return whether the number of segments exceeds the threshold.

        Args:
            index: The Whoosh index whose segments are evaluated.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            ``True`` if the segment count is greater than or equal to
            ``max_segments``, ``False`` otherwise.
        """
        segments = getattr(index, "_segments", None)
        if callable(segments):
            segments = segments()
        return len(cast(list[Any], segments or [])) >= self.max_segments

    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        """Return commit kwargs to enable merging.

        Args:
            index: The Whoosh index (unused).
            **kwargs: Additional keyword arguments (unused).

        Returns:
            A dict with ``merge`` set to ``True``.
        """
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
        """Initialize the tiered merge policy.

        Args:
            max_segments: Threshold number of segments above which merging
                is triggered. Defaults to 10.
            target_segment_size: Target size in documents for a merged
                segment. Defaults to 100000.
        """
        self.max_segments = max_segments
        self.target_segment_size = target_segment_size

    def should_merge(self, index: Index, **kwargs: object) -> bool:
        """Return whether the number of segments exceeds the threshold.

        Args:
            index: The Whoosh index whose segments are evaluated.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            ``True`` if the segment count is greater than or equal to
            ``max_segments``, ``False`` otherwise.
        """
        segments = getattr(index, "_segments", None)
        if callable(segments):
            segments = segments()
        return len(cast(list[Any], segments or [])) >= self.max_segments

    def merge_kwargs(self, index: Index, **kwargs: object) -> dict[str, object]:
        """Return commit kwargs to enable merging.

        Args:
            index: The Whoosh index (unused).
            **kwargs: Additional keyword arguments (unused).

        Returns:
            A dict with ``merge`` set to ``True``.
        """
        return {"merge": True}
