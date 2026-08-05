"""High-level indexing utilities for Whoosh-NG.

Provides batch writing, parallel segment building, and merge policies.
"""

from whoosh_modern.indexing.batch_writer import BatchIndexWriter
from whoosh_modern.indexing.compiler import BatchAnalyzer, CompiledDataSource
from whoosh_modern.indexing.merge_policies import (
    LogMergePolicy,
    MergePolicy,
    NoMergePolicy,
    TieredMergePolicy,
)
from whoosh_modern.indexing.modern_builder import ModernIndexBuilder
from whoosh_modern.indexing.parallel_builder import ParallelIndexBuilder

__all__ = [
    "BatchAnalyzer",
    "BatchIndexWriter",
    "CompiledDataSource",
    "MergePolicy",
    "NoMergePolicy",
    "LogMergePolicy",
    "TieredMergePolicy",
    "ModernIndexBuilder",
    "ParallelIndexBuilder",
]
