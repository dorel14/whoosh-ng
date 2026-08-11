"""High-level indexing utilities for Whoosh-NG.

Provides batch writing, parallel segment building, and merge policies.

Author: dorel14
Version: 3.0.0
"""

from whoosh_modern.indexing.batch_writer import BatchIndexWriter
from whoosh_modern.indexing.compiler import BatchAnalyzer, CompiledDataSource
from whoosh_modern.indexing.modern_builder import ModernIndexBuilder
from whoosh_modern.indexing.parallel_builder import ParallelIndexBuilder

__all__ = [
    "BatchAnalyzer",
    "BatchIndexWriter",
    "CompiledDataSource",
    "ModernIndexBuilder",
    "ParallelIndexBuilder",
]
