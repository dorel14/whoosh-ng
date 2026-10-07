"""Hybrid search benchmark on real datasets (v5.0: FastCSVSource + native parallel embeddings).

Compares BM25, BM25 fuzzy, vector, hybrid weighted, and hybrid RRF search
with explicit ground truth relevance judgments.

Key features:
- ProviderPool: N FastEmbedProvider instances (legacy parallel path)
- EmbeddingBatchWriter : Thread-safe LRU cache, strict error handling
- Batch indexing via BatchIndexWriter
- Indexing profiling (reading/analyzing/committing + term stats)
- Auto ground truth from BM25 exact matches
- Configurable query set via --queries-file
- Model preloading (async/sync)

Usage:
    # With ProviderPool (recommended for 1M+ docs)
    python -m benchmark.hybrid_search_benchmark --dataset customers --upto 100000 --pool-size 4

    # Without pool (legacy mode)
    python -m benchmark.hybrid_search_benchmark --dataset reuters --upto 1000 --no-pool

    # Native FastEmbed parallel inference (preferred for throughput)
    python -m benchmark.hybrid_search_benchmark --dataset customers --upto 100000 --parallel 0

Author: dorel14
Version: 5.0.0 (FastCSVSource loading + native FastEmbed parallel)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import tempfile
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark import WhooshLikeSpec
from whoosh import fields
from whoosh.fields import Schema
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh.query import FuzzyTerm
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.embeddings.model_preload import preload_embedding_model
from whoosh_modern.embeddings.provider_pool import ProviderPool
from whoosh_modern.fields.vector import VECTOR
from whoosh_modern.indexing import BatchIndexWriter, EmbeddingBatchWriter
from whoosh_modern.profiling import CommitProfilerV2, IndexProfiler
from whoosh_modern.searching.hybrid import HybridSearcher
from whoosh_modern.vector.numpy_provider import NumpyProvider

REUTERS_PATH = Path(__file__).parent / "reuters21578.txt"
CUSTOMERS_PATH = Path(__file__).parent / "Datas" / "customers-2000000.csv"


def _build_body(doc: dict[str, Any]) -> str:
    """Concatenate all string field values into a single searchable body.

    Used to build the ``body`` field consumed by BM25 search and by the
    vector embedding step. Mirrors the behaviour of the previous manual
    CSV reader so hybrid retrieval quality is preserved.
    """
    return " ".join(str(v) for v in doc.values() if isinstance(v, str) and v)


@dataclass(frozen=True)
class QueryDefinition:
    """Explicit query with optional relevant document IDs for evaluation."""

    text: str
    relevant_ids: set[str] | None = None
    semantic_variant: str | None = None
    auto_ground_truth: bool = False


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    latency_ms: float
    recall_at_k: float
    precision_at_k: float
    mrr_at_k: float
    ndcg_at_k: float
    embed_ms: float | None = None
    search_ms: float | None = None


@dataclass(frozen=True)
class LatencyStats:
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float


class HybridSearchBenchmark(WhooshLikeSpec):
    name = "hybrid_search_benchmark"
    main_field = "body"
    headline_field = "headline"
    default_query = "trade"

    def __init__(self, options: Any, args: Any) -> None:
        super().__init__(options, args)
        self._dataset = getattr(options, "dataset", "reuters")
        self._queries_file = getattr(options, "queries_file", None)
        self._num_queries = int(getattr(options, "queries", 10))
        self._profile_indexing = bool(getattr(options, "profile_indexing", False))
        self._auto_ground_truth = bool(getattr(options, "auto_ground_truth", False))
        self._batch_size = int(getattr(options, "batch_size", 0))
        self._no_vector = bool(getattr(options, "no_vector", False))
        self._embedding_cache = getattr(options, "embedding_cache", None)
        self._pool_size = int(getattr(options, "pool_size", 4))  #  ProviderPool
        self._no_pool = bool(getattr(options, "no_pool", False))  #  fallback to single provider
        self._preload_models = bool(getattr(options, "preload_models", True))  #  async warmup
        self._parallel = getattr(options, "parallel", None)  #  native FastEmbed parallel workers
        self._fast_source = None
        if self._dataset == "customers":
            self._fast_source = FastCSVSource(
                path=str(CUSTOMERS_PATH),
                incremental_field=None,
                id_field="Customer Id",
            )
        self._vector_top_k_values = [5, 10, 20]
        self._provider: FastEmbedProvider | ProviderPool | None = None
        self._embedding_stats: dict[str, Any] = {}  #  track embedding metrics

    def _ensure_embedding_provider(self) -> FastEmbedProvider | ProviderPool:
        """Create embedding provider.

        Priority:
        1. ``--parallel N`` (native FastEmbed parallel workers) - preferred
           for throughput. Each worker is pinned to ``threads=1`` to avoid
           CPU oversubscription while FastEmbed distributes work across
           workers at the C++/ONNX layer.
        2. ProviderPool (legacy Python-thread pool) when ``--pool-size`` is
           set without ``--parallel``.
        3. Single sequential provider (``--no-pool``).
        """
        if self._provider is not None:
            return self._provider

        # Native FastEmbed parallel path (preferred)
        if self._parallel is not None:
            print(f"Creating FastEmbedProvider with native parallel={self._parallel}...")
            self._provider = FastEmbedProvider(
                model_name="BAAI/bge-small-en-v1.5",
                parallel=self._parallel,
                threads=1,  # pin each worker to a single thread
                lazy_load=bool(self._parallel),
            )
            print(
                f"[OK] Provider ready (dimension={self._provider.dimension}, "
                f"parallel={self._parallel})"
            )
            return self._provider

        # v4.0: Preload model if requested
        if self._preload_models:
            try:
                preload_embedding_model("BAAI/bge-small-en-v1.5", provider_type="fastembed")
                print("[OK] Model preloaded")
            except Exception as e:
                print(f"[WARN] Model preload failed: {e}")

        # v4.0: Use ProviderPool for parallel embedding
        if not self._no_pool:
            print(f"Creating ProviderPool with {self._pool_size} instances...")
            self._provider = ProviderPool(
                # threads=1 per provider avoids CPU oversubscription:
                # pool_size instances x ORT threads would exceed logical cores.
                provider_factory=lambda: FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5",
                                                            threads=1),
                pool_size=self._pool_size,
            )
            print(f"[OK] ProviderPool ready (dimension={self._provider.dimension})")
        else:
            # Legacy: Single provider instance
            print("Creating single FastEmbedProvider (legacy mode)...")
            self._provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
            print(f"[OK] Provider ready (dimension={self._provider.dimension})")

        return self._provider

    def whoosh_schema(self) -> Schema:
        if self._dataset == "customers" and self._fast_source is not None:
            base = self._fast_source.discover_schema()
            fields_dict: dict[str, Any] = {}
            for name in base.names():
                if name == "Customer_Id":
                    fields_dict[name] = fields.ID(stored=True, unique=True)
                else:
                    fields_dict[name] = fields.TEXT(stored=False)
            fields_dict["body"] = fields.TEXT(stored=True)
            if not self._no_vector:
                provider = self._ensure_embedding_provider()
                fields_dict["body_vector"] = VECTOR(dimension=provider.dimension)
            return Schema(**fields_dict)

        fields_dict = {
            "doc_id": fields.ID(stored=True, unique=True),
            "date": fields.TEXT(stored=True),
            "headline": fields.TEXT(stored=True),
            "body": fields.TEXT(stored=True),
        }
        if not self._no_vector:
            provider = self._ensure_embedding_provider()
            fields_dict["body_vector"] = VECTOR(dimension=provider.dimension)
        return Schema(**fields_dict)

    def documents(self) -> Iterator[dict[str, Any]]:
        if self._dataset == "customers" and self._fast_source is not None:
            for doc in self._fast_source.iter_documents():
                doc = dict(doc)
                doc["body"] = _build_body(doc)
                yield doc
        else:
            yield from self._iter_reuters()

    def _iter_customers(self) -> Iterator[dict[str, Any]]:
        count = 0
        with open(CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = " ".join(str(v) for v in row.values() if isinstance(v, str) and v)
                yield {
                    "customer_id": row["Customer Id"],
                    "first_name": row["First Name"],
                    "last_name": row["Last Name"],
                    "company": row["Company"],
                    "city": row["City"],
                    "country": row["Country"],
                    "email": row["Email"],
                    "subscription_date": row["Subscription Date"],
                    "website": row["Website"],
                    "body": text,
                }
                count += 1
                if self.options.upto and count >= int(self.options.upto):
                    break

    def _iter_reuters(self) -> Iterator[dict[str, Any]]:
        count = 0
        with open(REUTERS_PATH, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) < 2:
                    continue
                date = parts[0]
                body = parts[1]
                if body.endswith(" REUTER 3;"):
                    body = body[: -len(" REUTER 3;")]
                headline = body.split("\n")[0][:120] if body else ""
                yield {
                    "doc_id": f"REUT-{date}-{count}",
                    "date": date,
                    "headline": headline,
                    "body": body,
                }
                count += 1
                if self.options.upto and count >= int(self.options.upto):
                    break

    def batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        if self._dataset == "customers" and self._fast_source is not None:
            for batch in self._fast_source.stream_batches(batch_size=batch_size):
                for doc in batch:
                    doc["body"] = _build_body(doc)
                yield batch
            return
        batch: list[dict[str, Any]] = []
        for doc in self.documents():
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _default_queries(self) -> list[QueryDefinition]:
        if self._dataset == "customers":
            return [
                QueryDefinition("oyer Wang business", auto_ground_truth=True),
                QueryDefinition("Costa Rica client", auto_ground_truth=True),
                QueryDefinition("Michelle Blevins", auto_ground_truth=True),
                QueryDefinition("Shah Sons business", auto_ground_truth=True),
                QueryDefinition("faulkner kramer contact", auto_ground_truth=True),
                QueryDefinition("subscription year 2021", auto_ground_truth=True),
                QueryDefinition("Chagos Archipelago territory", auto_ground_truth=True),
                QueryDefinition("Patel Deleon business", auto_ground_truth=True),
                QueryDefinition("Gina Rocha", auto_ground_truth=True),
                QueryDefinition("nicholas faulkner contact", auto_ground_truth=True),
            ]
        return [
            QueryDefinition("trade", auto_ground_truth=True),
            QueryDefinition("interest rates", auto_ground_truth=True),
            QueryDefinition("oil prices", auto_ground_truth=True),
            QueryDefinition("bank merger", auto_ground_truth=True),
            QueryDefinition("currency exchange", auto_ground_truth=True),
            QueryDefinition("stock market", auto_ground_truth=True),
            QueryDefinition("trade deficit", auto_ground_truth=True),
            QueryDefinition("foreign investment", auto_ground_truth=True),
            QueryDefinition("commodity prices", auto_ground_truth=True),
            QueryDefinition("monetary policy", auto_ground_truth=True),
        ]

    def _load_queries(self) -> list[QueryDefinition]:
        if self._queries_file:
            path = Path(self._queries_file)
            if not path.exists():
                raise FileNotFoundError(f"Queries file not found: {path}")
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            queries = []
            for item in raw:
                q = QueryDefinition(
                    text=item["text"],
                    relevant_ids=set(item.get("relevant_ids", [])),
                    semantic_variant=item.get("semantic_variant"),
                    auto_ground_truth=bool(item.get("auto_ground_truth", False)),
                )
                queries.append(q)
            return queries
        queries = self._default_queries()
        if self._num_queries < len(queries):
            queries = queries[: self._num_queries]
        if self._auto_ground_truth:
            queries = [self._attach_auto_ground_truth(q) for q in queries]
        return queries

    def _attach_auto_ground_truth(self, qdef: QueryDefinition) -> QueryDefinition:
        if qdef.relevant_ids is not None:
            return qdef
        return QueryDefinition(
            text=qdef.text,
            relevant_ids=set(),
            semantic_variant=qdef.semantic_variant,
            auto_ground_truth=True,
        )

    def _doc_id(self, hit: Any) -> str:
        f = hit.fields()
        if self._dataset == "customers":
            return str(f.get("Customer_Id") or f.get("doc_id") or str(hit.docnum))
        return str(f.get("doc_id") or f.get("customer_id") or str(hit.docnum))

    def _auto_ground_truth_ids(self, searcher: Any, query_text: str) -> set[str]:
        parser = QueryParser(self.main_field, schema=searcher.schema)
        try:
            q = parser.parse(query_text)
        except Exception:
            return set()
        try:
            results = searcher.search(q, limit=10000)
        except Exception:
            return set()
        return {self._doc_id(hit) for hit in results}

    def _run_bm25(
        self, searcher: Any, query_text: str, limit: int
    ) -> tuple[list[tuple[str, float]], float]:
        parser = QueryParser(self.main_field, schema=searcher.schema)
        q = parser.parse(query_text)
        t0 = time.perf_counter()
        results = searcher.search(q, limit=limit)
        latency = (time.perf_counter() - t0) * 1000
        return [(self._doc_id(hit), float(hit.score)) for hit in results], latency

    def _run_bm25_fuzzy(
        self, searcher: Any, query_text: str, limit: int
    ) -> tuple[list[tuple[str, float]], float]:
        fuzzy_q = FuzzyTerm(self.main_field, query_text, maxdist=1, prefixlength=0)
        t0 = time.perf_counter()
        results = searcher.search(fuzzy_q, limit=limit)
        latency = (time.perf_counter() - t0) * 1000
        return [(self._doc_id(hit), float(hit.score)) for hit in results], latency

    def _profile_vector(
        self, provider: NumpyProvider, query_text: str, k: int
    ) -> tuple[list[tuple[str, float]], float, float]:
        embedding_provider = self._ensure_embedding_provider()
        t0 = time.perf_counter()
        vector = embedding_provider.embed(query_text)
        embed_ms = (time.perf_counter() - t0) * 1000
        t1 = time.perf_counter()
        hits = provider.search(vector, k=k)
        search_ms = (time.perf_counter() - t1) * 1000
        return [(hit.doc_id, hit.score) for hit in hits], embed_ms, search_ms

    def _run_hybrid(
        self,
        searcher: Any,
        provider: NumpyProvider,
        query_text: str,
        limit: int,
        method: str = "weighted",
        alpha: float = 0.5,
        vector_k: int = 10,
    ) -> tuple[list[tuple[str, float]], float]:
        parser = QueryParser(self.main_field, schema=searcher.schema)
        q = parser.parse(query_text)
        id_field = "doc_id" if self._dataset == "reuters" else "Customer_Id"
        hs = HybridSearcher(searcher, provider, id_field=id_field)
        t0 = time.perf_counter()
        results = hs.search(q, limit=limit, method=method, alpha=alpha, vector_k=vector_k)
        latency = (time.perf_counter() - t0) * 1000
        return [(r.doc_id, r.score) for r in results], latency

    def _dcg(self, scores: list[float], k: int) -> float:
        return sum(score / math.log2(i + 2) for i, score in enumerate(scores[:k]))

    def _ndcg(self, hit_scores: list[tuple[str, float]], relevant_ids: set[str], k: int) -> float:
        if not relevant_ids:
            return 0.0
        ideal = [1.0] * min(len(relevant_ids), k)
        actual = [1.0 if doc_id in relevant_ids else 0.0 for doc_id, _ in hit_scores[:k]]
        ideal_dcg = self._dcg(ideal, k)
        actual_dcg = self._dcg(actual, k)
        return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0

    def _mrr(self, hit_ids: list[str], relevant_ids: set[str], k: int) -> float:
        for i, doc_id in enumerate(hit_ids[:k]):
            if doc_id in relevant_ids:
                return 1.0 / (i + 1)
        return 0.0

    def _score_metrics(
        self,
        hits: list[tuple[str, float]],
        relevant_ids: set[str] | None = None,
        k: int = 10,
    ) -> tuple[float, float, float, float]:
        top = hits[:k]
        if not top:
            return 0.0, 0.0, 0.0, 0.0
        hit_ids = [doc_id for doc_id, _ in top]
        if not relevant_ids:
            precision = 0.0
            recall = 0.0
            mrr = 0.0
            ndcg = 0.0
        else:
            hits_set = set(hit_ids)
            intersection = hits_set & relevant_ids
            precision = len(intersection) / len(hits_set)
            recall = len(intersection) / len(relevant_ids)
            mrr = self._mrr(hit_ids, relevant_ids, k)
            ndcg = self._ndcg(top, relevant_ids, k)
        return recall, precision, mrr, ndcg

    def _percentile(self, values: Sequence[float], p: float) -> float:
        if not values:
            return 0.0
        s = sorted(values)
        k = (len(s) - 1) * p
        f = int(k)
        c = f + 1
        if c >= len(s):
            return s[f]
        d0 = s[f] * (c - k)
        d1 = s[c] * (k - f)
        return d0 + d1

    def _run_indexing(self, ix: Any, batch_size: int = 0) -> int:
        """Run indexing with optional vector embeddings ( ProviderPool).

        - ProviderPool for parallel embedding throughput
        - ThreadSafeLRUCache for embedding deduplication
        - Strict error handling with detailed logging
        - Performance metrics collection
        """
        if self._no_vector:
            return self._run_text_indexing(ix, batch_size)

        print("\n=== Indexing with embedded vectors ===")
        vector_provider = NumpyProvider()
        embedding_provider = self._ensure_embedding_provider()

        doc_count = 0
        t0_total = time.perf_counter()

        if batch_size > 0:
            #  EmbeddingBatchWriter with ProviderPool + ThreadSafeLRUCache
            print(
                f"Creating EmbeddingBatchWriter:\n"
                f"  - batch_size={batch_size}\n"
                f"  - embedding_batch_size=256\n"
                f"  - cache_size=8192\n"
                f"  - strict_errors=True\n"
                f"  - cache_path={self._embedding_cache}"
            )
            writer = EmbeddingBatchWriter(
                ix,
                embedding_provider=embedding_provider,
                text_field="body",
                vector_field="body_vector",
                batch_size=batch_size,
                embedding_batch_size=256,
                cache_size=8192,
                strict_errors=True,
                multisegment=True,
                cache_path=self._embedding_cache,
            )

            for batch_num, batch in enumerate(self.batches(batch_size), 1):
                if self.options.upto and doc_count >= int(self.options.upto):
                    break
                if doc_count + len(batch) > int(self.options.upto) and self.options.upto:
                    batch = batch[: int(self.options.upto) - doc_count]

                #  add_batch() automatically embeds and mutates doc["body_vector"]
                writer.add_batch(batch)
                doc_count += len(batch)

                # Collect vectors from batch for NumpyProvider (same vectors as embedded)
                for doc in batch:
                    doc_id = str(
                        doc.get("Customer_Id")
                        or doc.get("doc_id")
                        or doc.get("customer_id")
                        or ""
                    )
                    vector = doc.get("body_vector", [0.0] * embedding_provider.dimension)
                    if vector:
                        vector_provider.add([(doc_id, vector)])

                if batch_num % 5 == 0:
                    elapsed = time.perf_counter() - t0_total
                    rate = doc_count / elapsed if elapsed > 0 else 0
                    print(f"  [{batch_num}] {doc_count} docs ({rate:.0f} docs/sec) \
                        - time: {elapsed:.2f}s")

            #  Close writer and collect stats
            writer.close()
            stats = writer.get_stats()
            self._embedding_stats = stats
            print(
                f"\n[OK] Embedding stats:\n"
                f"  - Docs indexed: {stats['docs_added']}\n"
                f"  - Embeddings computed: {stats['embeddings_computed']}\n"
                f"  - Cache hit rate: {stats['cache']['hit_rate_percent']:.1f}%\n"
                f"  - Throughput: {stats['docs_per_second']:.0f} docs/sec\n"
                f"  - Errors: {stats['errors']}"
            )
        else:
            # Legacy: Per-document indexing (no batch)
            print("Indexing in per-document mode (no batching)...")
            writer = ix.writer()
            for doc in self.documents():
                text = doc.get("body", "") or doc.get("headline", "")
                doc_id = str(
                    doc.get("Customer_Id")
                    or doc.get("doc_id")
                    or doc.get("customer_id")
                    or ""
                )

                #  Embed single text (or use zero vector if empty)
                try:
                    if text:
                        vector = embedding_provider.embed(text)
                    else:
                        vector = [0.0] * embedding_provider.dimension
                except Exception as e:
                    print(f"[WARN] Embedding failed for {doc_id}: {e}")
                    vector = [0.0] * embedding_provider.dimension

                doc = dict(doc)
                doc["body_vector"] = vector
                writer.add_document(**doc)
                vector_provider.add([(doc_id, vector)])
                doc_count += 1

            writer.commit()

        idx_time = time.perf_counter() - t0_total
        print(
            f"\n[OK] Indexing completed:\n"
            f"  - Total docs: {doc_count}\n"
            f"  - Time: {idx_time:.1f}s\n"
            f"  - Throughput: {doc_count / idx_time:.0f} docs/sec"
        )
        return doc_count

    def _run_text_indexing(self, ix: Any, batch_size: int = 0) -> int:
        if self._profile_indexing:
            profiler = IndexProfiler()
            profiler.__enter__()
            commit_profiler = CommitProfilerV2(collect_term_stats=True)
            t0 = time.perf_counter()
            doc_count = 0
            if batch_size > 0:
                with profiler.step("reading"):
                    batches = list(self.batches(batch_size))
                writer = BatchIndexWriter(
                    ix,
                    batch_size=batch_size,
                    multisegment=True,
                )
                with profiler.step("analyzing"):
                    for batch in batches:
                        if self.options.upto and doc_count >= int(self.options.upto):
                            break
                        if doc_count + len(batch) > int(self.options.upto) and self.options.upto:
                            batch = batch[: int(self.options.upto) - doc_count]
                        writer.add_batch(batch)
                        doc_count += len(batch)
                with profiler.step("committing"):
                    if hasattr(writer, "_writer") and writer._writer is not None:
                        commit_profiler.profile(writer._writer)
                        writer._writer = None
                    else:
                        commit_profiler.profile(writer)
                if hasattr(writer, "close"):
                    writer.close()
            else:
                with profiler.step("reading"):
                    docs = list(self.documents())
                writer = ix.writer()
                with profiler.step("analyzing"):
                    for doc in docs:
                        writer.add_document(**doc)
                        doc_count += 1
                with profiler.step("committing"):
                    if hasattr(writer, "_writer") and writer._writer is not None:
                        commit_profiler.profile(writer._writer)
                        writer._writer = None
                    else:
                        commit_profiler.profile(writer)
            profiler.add_documents(doc_count)
            idx_time = time.perf_counter() - t0
            profiler.__exit__(None, None, None)
            print(
                f"Indexed {doc_count} docs in {idx_time:.3f}s ({doc_count / idx_time:.1f} docs/s)"
            )
            print(profiler.report())
            print(commit_profiler.report())
            return doc_count
        else:
            t0 = time.perf_counter()
            doc_count = 0
            if batch_size > 0:
                with BatchIndexWriter(ix, batch_size=batch_size, multisegment=True) as writer:
                    for batch in self.batches(batch_size):
                        if self.options.upto and doc_count >= int(self.options.upto):
                            break
                        if doc_count + len(batch) > int(self.options.upto) and self.options.upto:
                            batch = batch[: int(self.options.upto) - doc_count]
                        writer.add_batch(batch)
                        doc_count += len(batch)
            else:
                writer = ix.writer()
                for doc in self.documents():
                    writer.add_document(**doc)
                    doc_count += 1
                writer.commit()
            idx_time = time.perf_counter() - t0
            print(
                f"Indexed {doc_count} docs in {idx_time:.3f}s ({doc_count / idx_time:.1f} docs/s)"
            )
            return doc_count

    def run_hybrid_benchmark(
        self, limit: int = 10, queries: int = 10, batch_size: int = 0
    ) -> dict[str, Any]:
        tmp_dir = Path(tempfile.mkdtemp(prefix="hybrid_benchmark_"))
        idx_dir = tmp_dir / "index"
        idx_dir.mkdir()

        schema = self.whoosh_schema()
        ix = create_in(str(idx_dir), schema)

        doc_count, provider = self._run_indexing(ix, batch_size)
        query_defs = self._load_queries()

        mode_rows: dict[str, list[BenchmarkResult]] = {}
        latency_rows: dict[str, list[float]] = {}
        embed_rows: list[float] = []
        search_rows: list[float] = []

        try:
            with ix.searcher() as searcher:
                print(f"Running {len(query_defs)} queries...")
                for qdef in query_defs:
                    qtext = qdef.text
                    relevant_ids = qdef.relevant_ids or set()
                    if qdef.auto_ground_truth and not relevant_ids:
                        relevant_ids = self._auto_ground_truth_ids(searcher, qtext)

                    # BM25
                    bm25_hits, bm25_lat = self._run_bm25(searcher, qtext, limit)
                    bm25_rec, bm25_prec, bm25_mrr, bm25_ndcg = self._score_metrics(
                        bm25_hits, relevant_ids, limit
                    )
                    self._append(
                        mode_rows,
                        latency_rows,
                        "bm25",
                        bm25_lat,
                        bm25_rec,
                        bm25_prec,
                        bm25_mrr,
                        bm25_ndcg,
                    )

                    # BM25 fuzzy
                    fuzzy_hits, fuzzy_lat = self._run_bm25_fuzzy(searcher, qtext, limit)
                    fuzzy_rec, fuzzy_prec, fuzzy_mrr, fuzzy_ndcg = self._score_metrics(
                        fuzzy_hits, relevant_ids, limit
                    )
                    self._append(
                        mode_rows,
                        latency_rows,
                        "bm25_fuzzy",
                        fuzzy_lat,
                        fuzzy_rec,
                        fuzzy_prec,
                        fuzzy_mrr,
                        fuzzy_ndcg,
                    )

                    if not self._no_vector and provider is not None:
                        # Vector (profiled)
                        vec_hits, embed_ms, vec_search_ms = self._profile_vector(
                            provider, qtext, limit
                        )
                        vec_rec, vec_prec, vec_mrr, vec_ndcg = self._score_metrics(
                            vec_hits, relevant_ids, limit
                        )
                        self._append(
                            mode_rows,
                            latency_rows,
                            "vector",
                            embed_ms + vec_search_ms,
                            vec_rec,
                            vec_prec,
                            vec_mrr,
                            vec_ndcg,
                        )
                        embed_rows.append(embed_ms)
                        search_rows.append(vec_search_ms)

                        # Hybrid variants over multiple vector top-K values
                        for vk in self._vector_top_k_values:
                            for method_name, method in [
                                ("hybrid_weighted", "weighted"),
                                ("hybrid_rrf", "rrf"),
                            ]:
                                hyb_hits, hyb_lat = self._run_hybrid(
                                    searcher, provider, qtext, limit, method=method, vector_k=vk
                                )
                                hyb_rec, hyb_prec, hyb_mrr, hyb_ndcg = self._score_metrics(
                                    hyb_hits, relevant_ids, limit
                                )
                                mode_key = f"{method_name}_k{vk}"
                                self._append(
                                    mode_rows,
                                    latency_rows,
                                    mode_key,
                                    hyb_lat,
                                    hyb_rec,
                                    hyb_prec,
                                    hyb_mrr,
                                    hyb_ndcg,
                                )

                    # Semantic variant if available
                    if qdef.semantic_variant:
                        sem_hits, sem_lat = self._run_bm25(searcher, qdef.semantic_variant, limit)
                        sem_rec, sem_prec, sem_mrr, sem_ndcg = self._score_metrics(
                            sem_hits, relevant_ids, limit
                        )
                        self._append(
                            mode_rows,
                            latency_rows,
                            "bm25_semantic_variant",
                            sem_lat,
                            sem_rec,
                            sem_prec,
                            sem_mrr,
                            sem_ndcg,
                        )
        finally:
            ix.close()
            import shutil

            shutil.rmtree(tmp_dir, ignore_errors=True)

        return {
            "mode_rows": mode_rows,
            "latency_rows": latency_rows,
            "embed_ms": embed_rows,
            "vector_search_ms": search_rows,
            "doc_count": doc_count,
            "query_count": len(query_defs),
            "indexing_profile": {},
        }

    def _append(
        self,
        mode_rows: dict[str, list[BenchmarkResult]],
        latency_rows: dict[str, list[float]],
        mode: str,
        latency_ms: float,
        recall: float,
        precision: float,
        mrr: float,
        ndcg: float,
    ) -> None:
        mode_rows.setdefault(mode, []).append(
            BenchmarkResult(mode, latency_ms, recall, precision, mrr, ndcg)
        )
        latency_rows.setdefault(mode, []).append(latency_ms)

    def _latency_stats(self, values: Sequence[float]) -> LatencyStats:
        return LatencyStats(
            p50_ms=self._percentile(values, 0.5),
            p95_ms=self._percentile(values, 0.95),
            p99_ms=self._percentile(values, 0.99),
            mean_ms=statistics.mean(values) if values else 0.0,
        )

    def print_report(self, run_data: dict[str, Any]) -> None:
        """Print comprehensive benchmark report ( includes embedding metrics)."""
        mode_rows = run_data["mode_rows"]
        latency_rows = run_data["latency_rows"]

        #  Embedding indexing metrics
        if self._embedding_stats:
            print("\n" + "=" * 70)
            print("EMBEDDING PERFORMANCE METRICS")
            print("=" * 70)
            print(f"Documents indexed:        {self._embedding_stats.get('docs_added', 0):>12}")
            print(f"Embeddings computed:      \
                {self._embedding_stats.get('embeddings_computed', 0):>12}")
            cache_stats = self._embedding_stats.get("cache", {})
            print(f"Cache hits:               {cache_stats.get('hits', 0):>12}")
            print(f"Cache misses:             {cache_stats.get('misses', 0):>12}")
            print(f"Cache hit rate:           {cache_stats.get('hit_rate_percent', 0):>12.1f}%")
            print(f"Disk cache entries:  {self._embedding_stats.get('disk_cache_size', 0):>12}")
            print(f"Indexing throughput:     \
                {self._embedding_stats.get('docs_per_second', 0):>12.0f} docs/sec")
            print(f"Total time:              \
                {self._embedding_stats.get('elapsed_seconds', 0):>12.1f}s")
            print(f"Errors:                   {self._embedding_stats.get('errors', 0):>12}")
            if self._pool_size > 1 and not self._no_pool:
                print(f"Provider pool size:       {self._pool_size:>12}")
            print("=" * 70)

        print("\n=== Retrieval quality @ K ===")
        header = f"{'mode':<24} {'recall':>10} {'precision':>10} {'mrr':>10} {'ndcg':>10}"
        print(header)
        print("-" * 66)
        for mode in [
            "bm25",
            "bm25_fuzzy",
            "vector",
            "hybrid_weighted_k10",
            "hybrid_rrf_k10",
        ]:
            rows = mode_rows.get(mode, [])
            if not rows:
                continue
            recall = statistics.mean(r.recall_at_k for r in rows)
            precision = statistics.mean(r.precision_at_k for r in rows)
            mrr = statistics.mean(r.mrr_at_k for r in rows)
            ndcg = statistics.mean(r.ndcg_at_k for r in rows)
            print(f"{mode:<24} {recall:>10.3f} {precision:>10.3f} {mrr:>10.3f} {ndcg:>10.3f}")

        print("\n=== Latency (ms) ===")
        header = f"{'mode':<24} {'p50':>10} {'p95':>10} {'p99':>10} {'mean':>10}"
        print(header)
        print("-" * 66)
        for mode in [
            "bm25",
            "bm25_fuzzy",
            "vector",
            "hybrid_weighted_k10",
            "hybrid_rrf_k10",
        ]:
            values = latency_rows.get(mode, [])
            stats = self._latency_stats(values)
            print(
                f"{mode:<24} {stats.p50_ms:>10.3f} {stats.p95_ms:>10.3f} "
                f"{stats.p99_ms:>10.3f} {stats.mean_ms:>10.3f}"
            )

        embed = run_data.get("embed_ms", [])
        vec_search = run_data.get("vector_search_ms", [])
        if embed and vec_search:
            print("\n=== Vector profiling (ms) ===")
            print(
                f"query embedding   p50={self._percentile(embed, 0.5):.3f}  "
                f"p95={self._percentile(embed, 0.95):.3f}  "
                f"mean={statistics.mean(embed):.3f}"
            )
            print(
                f"vector search     p50={self._percentile(vec_search, 0.5):.3f}  "
                f"p95={self._percentile(vec_search, 0.95):.3f}  "
                f"mean={statistics.mean(vec_search):.3f}"
            )

        print("\n=== Hybrid sensitivity: vector top-K ===")
        header = f"{'mode':<24} {'recall':>10} {'precision':>10} {'latency_mean':>14}"
        print(header)
        print("-" * 66)
        for vk in [5, 10, 20]:
            for method_name in ["hybrid_weighted", "hybrid_rrf"]:
                mode_key = f"{method_name}_k{vk}"
                rows = mode_rows.get(mode_key, [])
                if not rows:
                    continue
                recall = statistics.mean(r.recall_at_k for r in rows)
                precision = statistics.mean(r.precision_at_k for r in rows)
                lat = statistics.mean(latency_rows.get(mode_key, []))
                print(f"{mode_key:<24} {recall:>10.3f} {precision:>10.3f} {lat:>14.3f}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Hybrid search real-world benchmark \
                                    (ProviderPool)")
    parser.add_argument("--dataset", choices=["reuters", "customers"], default="reuters")
    parser.add_argument("--upto", type=int, default=0, help="Max docs to index (0=all)")
    parser.add_argument("--limit", type=int, default=10, help="Max search results")
    parser.add_argument("--queries", type=int, default=10, help="Number of queries to run")
    parser.add_argument("--queries-file", default=None, help="JSON file with explicit queries")
    parser.add_argument(
        "--profile-indexing", action="store_true", help="Enable detailed indexing profiling"
    )
    parser.add_argument(
        "--auto-ground-truth",
        action="store_true",
        help="Auto-generate ground truth from exact BM25 matches",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for indexing (0=disable batch indexing)",
    )
    parser.add_argument(
        "--no-vector",
        action="store_true",
        help="Disable vector and hybrid search (BM25 only)",
    )
    parser.add_argument(
        "--embedding-cache",
        default=None,
        help="Path to numpy npz cache for embeddings",
    )
    #  ProviderPool options
    parser.add_argument(
        "--pool-size",
        type=int,
        default=4,
        help="Number of embedding provider instances in pool (default=4 for parallel embedding)",
    )
    parser.add_argument(
        "--no-pool",
        action="store_true",
        help="Disable ProviderPool and use single FastEmbedProvider (legacy mode)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=None,
        help="Enable FastEmbed native parallel inference. 0=auto-detect CPU cores, "
            "N>=1=exact worker count. Combines with threads=1 per worker "
            "(preferred over ProviderPool for throughput).",
    )
    parser.add_argument(
        "--no-preload",
        action="store_true",
        help="Disable model preloading at startup",
    )
    args = parser.parse_args()

    benchmark = HybridSearchBenchmark(
        argparse.Namespace(
            dir=str(Path(__file__).parent),
            limit=args.limit,
            upto=args.upto,
            dataset=args.dataset,
            queries=args.queries,
            queries_file=args.queries_file,
            profile_indexing=args.profile_indexing,
            auto_ground_truth=args.auto_ground_truth,
            batch_size=args.batch_size,
            no_vector=args.no_vector,
            embedding_cache=args.embedding_cache,
            #  New options
            pool_size=args.pool_size,
            no_pool=args.no_pool,
            parallel=args.parallel,
            preload_models=not args.no_preload,
            merge=1,
            procs=0,
            limitmb=128,
            progress_every=0,
            skip=1,
            profile=False,
            termfile=None,
        ),
        [],
    )

    run_data = benchmark.run_hybrid_benchmark(
        limit=args.limit, queries=args.queries, batch_size=args.batch_size
    )
    benchmark.print_report(run_data)

    return 0


if __name__ == "__main__":
    sys.exit(main())


