"""Index profiling utilities for Whoosh-NG.

Author: dorel14
Version: 3.2.0
"""

from __future__ import annotations

from whoosh_modern.profiling.auto_cache_advisor import AutoCacheAdvisor
from whoosh_modern.profiling.batch_memory_profiler import BatchMemoryProfiler
from whoosh_modern.profiling.cache_analyzer import BatchSizeOptimizer, CacheAnalyzer
from whoosh_modern.profiling.commit import (
    CommitProfilerV2,
    PipelineReconciler,
    PipelineReconcilerV2,
    profile_commit,
)
from whoosh_modern.profiling.core import IndexProfiler
from whoosh_modern.profiling.field import (
    AnalyzerCache,
    AnalyzerComparator,
    AnalyzerStepProfiler,
    FieldAnalyzerCache,
    FieldConversionProfiler,
    FieldIndexProfiler,
    FieldProfiler,
    FieldTransformationProfiler,
)
from whoosh_modern.profiling.index import (
    IndexQualityAnalyzer,
    PerDocWriterProfiler,
    PostingPoolProfiler,
    SegmentProfiler,
)
from whoosh_modern.profiling.memory import MemoryProfiler
from whoosh_modern.profiling.metrics import MetricsCollector
from whoosh_modern.profiling.ngram_profiler import NgramProfiler, NgramProfilerReport
from whoosh_modern.profiling.pipeline import (
    IndexingPathProfiler,
    IndexingPipelineProfiler,
    UnifiedPipelineProfiler,
)
from whoosh_modern.profiling.stemmer_benchmark import StemmerBenchmark
from whoosh_modern.profiling.stemmer_profiler import StemmerProfiler, StemmerProfilerReport
from whoosh_modern.profiling.synthetic_datasets import SyntheticDatasetGenerator

__all__ = [
    "AnalyzerCache",
    "AnalyzerComparator",
    "AnalyzerStepProfiler",
    "AutoCacheAdvisor",
    "BatchMemoryProfiler",
    "BatchSizeOptimizer",
    "CacheAnalyzer",
    "CommitProfilerV2",
    "FieldAnalyzerCache",
    "FieldConversionProfiler",
    "FieldIndexProfiler",
    "FieldProfiler",
    "FieldTransformationProfiler",
    "IndexProfiler",
    "IndexQualityAnalyzer",
    "IndexingPathProfiler",
    "IndexingPipelineProfiler",
    "MemoryProfiler",
    "MetricsCollector",
    "NgramProfiler",
    "NgramProfilerReport",
    "PerDocWriterProfiler",
    "PipelineReconciler",
    "PipelineReconcilerV2",
    "PostingPoolProfiler",
    "SegmentProfiler",
    "StemmerBenchmark",
    "StemmerProfiler",
    "StemmerProfilerReport",
    "UnifiedPipelineProfiler",
    "profile_commit",
]
