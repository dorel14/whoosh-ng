"""Benchmark comparing BM25, vector, and hybrid search across scales.

Measures latency and ranking-quality metrics using real embeddings from
:class:`LibEmbeddingProvider` stored in a native ``VECTOR`` column.

Scales:
- 5K, 10K, 50K, 100K documents

Metrics:
- per-phase latency (embedding docs, indexing, embedding queries, search)
- search latency percentiles: p50 / p95 / p99 (ms), excluding embedding
- Recall@K / Precision@K
- MRR@K (Mean Reciprocal Rank)
- NDCG@K (Normalized Discounted Cumulative Gain)

Ground truth is constructed independently from the search engines.

Corpus modes:
- ``synthetic``: topic-based generated documents with known relevance.
- ``stock``: real French company data from parquet file with ground truth
  from exact name/activity matches.

Tuning modes:
- ``TUNE_HYBRID``: sweep rrf_k / vector_k / alpha and report best config.
- ``TUNE_EMBEDDING``: sweep batch_size/threads/parallel for embedding throughput.

Author: dorel14
Version: 7.0.0
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import psutil
from cpuinfo import get_cpu_info

from whoosh.fields import TEXT, Schema
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.embeddings.libembedding_provider import LibEmbeddingProvider
from whoosh_modern.fields.vector import VECTOR
from whoosh_modern.indexing import ModernIndexBuilder
from whoosh_modern.searching.hybrid import HybridSearcher
from whoosh_modern.searching.vector_searcher import VectorSearcher

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCALES = [5000, 10000, 50000, 100000]
K = 20
BM25_K = 20
PROVIDER_MODEL = "arctic-embed-s"

TOPIC_WORDS_MIN = 8
TOPIC_WORDS_MAX = 22
RELEVANT_FRACTION = 0.10

TUNE_HYBRID = False
TUNE_EMBEDDING = False

RRF_K_SWEEP = [10, 30, 60, 100]
VECTOR_K_SWEEP = [10, 20, 50]
ALPHA_SWEEP = [0.3, 0.5, 0.7]
EMBEDDING_BATCH_SWEEP = [32, 64, 128, 256]
THREADS_SWEEP = [1, 2, 4, 8]
PARALLEL_SWEEP = [1, 2, 4]


def _create_provider(
    provider_type: str, model_name: str
) -> LibEmbeddingProvider | FastEmbedProvider:
    """Create an embedding provider based on the requested type.

    Args:
        provider_type: ``"libembedding"`` for LibEmbeddingProvider or
            ``"fastembed"`` for FastEmbedProvider.
        model_name: Model preset or identifier forwarded to the provider.

    Returns:
        An embedding provider instance implementing the common interface.

    Raises:
        ValueError: If ``provider_type`` is not recognized.
    """
    if provider_type == "fastembed":
        return FastEmbedProvider(model_name=model_name)
    if provider_type == "libembedding":
        return LibEmbeddingProvider(model_name=model_name)
    raise ValueError(f"Unknown provider type: {provider_type!r}")


@dataclass(frozen=True)
class ResourceSnapshot:
    """Resource usage captured at a point in time."""

    cpu_percent: float
    ram_mb: float


def _current_snapshot() -> ResourceSnapshot:
    """Capture the current CPU and memory usage for the current process.

    Returns:
        A ``ResourceSnapshot`` with CPU percentage and RSS in MB.
    """
    proc = psutil.Process(os.getpid())
    cpu = proc.cpu_percent(interval=None)
    mem = proc.memory_info().rss / (1024 * 1024)
    return ResourceSnapshot(cpu_percent=cpu, ram_mb=mem)


@dataclass(frozen=True)
class ProviderComparisonResult:
    """Aggregated results for one provider in a comparison run."""

    provider_type: str
    model_name: str
    total_s: float
    embed_docs_s: float
    index_s: float
    embed_queries_s: float
    search_s: float
    cpu_percent: float
    ram_mb: float
    scale: int
    recall: float
    precision: float
    mrr: float
    ndcg: float


def _compare_providers(
    documents: list[dict[str, str]],
    queries: list[str],
    ground_truth: dict[str, set[str]],
    model_name: str,
    scale: int,
    k: int = 20,
    bm25_k: int = 20,
    index_mode: str = "modern",
) -> tuple[ProviderComparisonResult, ProviderComparisonResult]:
    """Run the benchmark with both providers and return comparison results.

    Both providers are evaluated on the same documents, queries, index,
    and timing/resource windows so the comparison is fair.

    Args:
        documents: Documents to index and search.
        queries: Query texts to evaluate.
        ground_truth: Mapping from query text to relevant document IDs.
        model_name: Model identifier shared by both providers.
        scale: Number of documents, for reporting only.
        k: Evaluation cutoff.
        bm25_k: BM25 result set size.
        index_mode: Indexing mode forwarded to the search benchmark.

    Returns:
        ``(libembedding_result, fastembed_result)``.
    """
    results: dict[str, ProviderComparisonResult] = {}

    _current_snapshot()  # baseline for CPU measurement
    for provider_type in ("libembedding", "fastembed"):
        print(
            f"\n{'=' * 90}\n"
            f"  Provider: {provider_type} | model={model_name} | scale={scale:,}\n"
            f"{'=' * 90}"
        )

        provider = _create_provider(provider_type=provider_type, model_name=model_name)
        print(f"Provider instance: {provider}")
        print(f"Embedding dimension: {provider.dimension}")

        import tempfile

        tmp_path = (
            Path(tempfile.gettempdir())
            / f"benchmark_compare_{provider_type}_{int(time.time())}"
        )
        if tmp_path.exists():
            import shutil

            shutil.rmtree(tmp_path)
        tmp_path.mkdir(parents=True, exist_ok=True)

        snap_before = _current_snapshot()
        t0_total = time.perf_counter()

        query_metrics, phase_times = run_benchmark(
            tmp_path=tmp_path,
            documents=documents,
            queries=queries,
            ground_truth=ground_truth,
            provider=provider,
            k=k,
            bm25_k=bm25_k,
            index_mode=index_mode,
        )
        total_s = time.perf_counter() - t0_total
        snap_after = _current_snapshot()

        scale_results = _aggregate_scale(query_metrics, scale=scale)
        main_mode = next(
            (sr for sr in scale_results if sr.mode == "hybrid_rrf"),
            scale_results[0] if scale_results else None,
        )

        results[provider_type] = ProviderComparisonResult(
            provider_type=provider_type,
            model_name=model_name,
            total_s=total_s,
            embed_docs_s=phase_times.get("embed_docs_s", 0.0),
            index_s=phase_times.get("index_s", 0.0),
            embed_queries_s=phase_times.get("embed_queries_s", 0.0),
            search_s=sum(m.latency_ms for m in query_metrics) / 1000.0 if query_metrics else 0.0,
            cpu_percent=snap_after.cpu_percent,
            ram_mb=snap_after.ram_mb - snap_before.ram_mb,
            scale=scale,
            recall=main_mode.recall if main_mode else 0.0,
            precision=main_mode.precision if main_mode else 0.0,
            mrr=main_mode.mrr if main_mode else 0.0,
            ndcg=main_mode.ndcg if main_mode else 0.0,
        )

    return results["libembedding"], results["fastembed"]


def print_provider_comparison(
    lib_result: ProviderComparisonResult,
    fast_result: ProviderComparisonResult,
) -> None:
    """Print a side-by-side comparison of the two providers."""
    print(f"\n{'=' * 100}")
    print("  PROVIDER COMPARISON")
    print(f"{'=' * 100}")
    print(f"  Model : {lib_result.model_name}")
    print(f"  Scale : {lib_result.scale:,} documents")
    print(f"  CPU   : {get_cpu_info()['brand_raw']}")
    print(f"{'=' * 100}")

    rows = [
        ("Total run (s)", f"{lib_result.total_s:.2f}", f"{fast_result.total_s:.2f}"),
        (
            "Document embedding (s)",
            f"{lib_result.embed_docs_s:.2f}",
            f"{fast_result.embed_docs_s:.2f}",
        ),
        ("Indexing + commit (s)", f"{lib_result.index_s:.2f}", f"{fast_result.index_s:.2f}"),
        (
            "Query embedding (s)",
            f"{lib_result.embed_queries_s:.2f}",
            f"{fast_result.embed_queries_s:.2f}",
        ),
        ("Search total (s)", f"{lib_result.search_s:.2f}", f"{fast_result.search_s:.2f}"),
        ("CPU %", f"{lib_result.cpu_percent:.1f}", f"{fast_result.cpu_percent:.1f}"),
        ("RAM delta (MB)", f"{lib_result.ram_mb:.1f}", f"{fast_result.ram_mb:.1f}"),
        ("recall@K", f"{lib_result.recall:.3f}", f"{fast_result.recall:.3f}"),
        ("precision@K", f"{lib_result.precision:.3f}", f"{fast_result.precision:.3f}"),
        ("mrr@K", f"{lib_result.mrr:.3f}", f"{fast_result.mrr:.3f}"),
        ("ndcg@K", f"{lib_result.ndcg:.3f}", f"{fast_result.ndcg:.3f}"),
    ]

    header = f"{'Metric':<28} {'libembedding':>14} {'fastembed':>14} {'delta':>12}"
    print(header)
    print("-" * len(header))
    for label, lib_val, fast_val in rows:
        try:
            lib_num = float(lib_val)
            fast_num = float(fast_val)
            delta = f"{(fast_num - lib_num) / lib_num:+.1%}" if lib_num > 0 else "N/A"
        except ValueError:
            delta = "N/A"
        print(f"{label:<28} {lib_val:>14} {fast_val:>14} {delta:>12}")

    print(f"{'=' * 100}")


# ---------------------------------------------------------------------------
# Topic-based document generation
# ---------------------------------------------------------------------------
TOPICS: dict[str, list[str]] = {
    "search": [
        "search", "engine", "query", "retrieval", "ranking", "index",
        "document", "relevance", "result", "inverted index", "full text",
    ],
    "vector": [
        "vector", "embedding", "dimension", "cosine", "similarity",
        "nearest neighbor", "hnsw", "faiss", "numpy", "matrix",
    ],
    "ml": [
        "machine", "learning", "model", "training", "neural", "network",
        "classification", "regression", "prediction", "accuracy",
    ],
    "data": [
        "data", "processing", "pipeline", "etl", "dataset", "schema",
        "database", "storage", "column", "analytics", "streaming",
    ],
    "semantic": [
        "semantic", "meaning", "language", "nlp", "token", "embedding",
        "context", "transformer", "attention", "similarity",
    ],
    "python": [
        "python", "framework", "library", "asyncio", "pydantic",
        "fastapi", "package", "module", "import", "type hint",
    ],
    "optimization": [
        "optimization", "index", "cache", "performance", "benchmark",
        "latency", "throughput", "memory", "profiling", "tuning",
    ],
    "distributed": [
        "cloud", "distributed", "scalable", "service", "api", "rest",
        "endpoint", "cluster", "node", "shard", "replication",
    ],
}

QUERIES: list[tuple[str, set[str]]] = [
    ("search engine", {"search"}),
    ("vector embedding", {"vector"}),
    ("machine learning model", {"ml"}),
    ("data processing pipeline", {"data"}),
    ("semantic similarity", {"semantic"}),
    ("python framework", {"python"}),
    ("database index optimization", {"optimization", "search"}),
    ("neural network training", {"ml"}),
    ("content retrieval system", {"search", "semantic"}),
    ("analytics benchmark", {"optimization", "data"}),
]


def _build_documents(
    n_docs: int, seed: int = 42
) -> tuple[list[dict[str, str]], dict[str, set[str]]]:
    """Generate synthetic documents from topics with known relevance."""
    rng = random.Random(seed)
    all_words = [w for words in TOPICS.values() for w in words]

    n_topics = len(TOPICS)
    topic_names = list(TOPICS.keys())
    docs_per_topic = max(1, int(n_docs * RELEVANT_FRACTION) // n_topics)

    documents: list[dict[str, str]] = []
    ground_truth: dict[str, set[str]] = {q: set() for q, _ in QUERIES}

    doc_index = 0

    for topic_name in topic_names:
        words = TOPICS[topic_name]
        for _ in range(docs_per_topic):
            length = rng.randint(TOPIC_WORDS_MIN, TOPIC_WORDS_MAX)
            text_words = [rng.choice(words) for _ in range(int(length * 0.7))]
            text_words += [rng.choice(all_words) for _ in range(length - len(text_words))]
            rng.shuffle(text_words)
            text = " ".join(text_words)
            doc_id = f"doc-{doc_index:05d}"
            documents.append({
                "id": doc_id,
                "title": f"Document {doc_index}",
                "content": text,
                "_topic": topic_name,
            })
            doc_index += 1

    while len(documents) < n_docs:
        length = rng.randint(TOPIC_WORDS_MIN, TOPIC_WORDS_MAX)
        text = " ".join(rng.choice(all_words) for _ in range(length))
        doc_id = f"doc-{doc_index:05d}"
        documents.append({
            "id": doc_id,
            "title": f"Document {doc_index}",
            "content": text,
            "_topic": "noise",
        })
        doc_index += 1

    rng.shuffle(documents)

    for query_text, topics in QUERIES:
        for doc in documents:
            if doc["_topic"] in topics:
                ground_truth[query_text].add(doc["id"])

    for doc in documents:
        doc.pop("_topic", None)

    return documents, ground_truth


def _build_documents_stock(
    n_docs: int,
    seed: int = 42,
    parquet_path: str = "benchmark/Datas/stock-stockunitelegale-parquet.parquet",
) -> tuple[list[dict[str, str]], dict[str, set[str]]]:
    """Sample real French company documents from a parquet file.

    Reads the stock parquet and samples ``n_docs`` rows. Constructs
    ground truth from exact name matches and activity code matches.

    Args:
        n_docs: Number of documents to sample.
        seed: Random seed for reproducibility.
        parquet_path: Path to the parquet file.

    Returns:
        ``(documents, ground_truth)`` where ``ground_truth[query]`` is the
        set of relevant document IDs for that query.
    """
    rng = random.Random(seed)

    cols = [
        "siren",
        "nomUniteLegale",
        "denominationUsuelle1UniteLegale",
        "activitePrincipaleUniteLegale",
        "categorieJuridiqueUniteLegale",
        "dateCreationUniteLegale",
    ]
    df = pd.read_parquet(parquet_path, columns=cols)

    df = df[df["nomUniteLegale"].notna() | df["activitePrincipaleUniteLegale"].notna()].copy()
    df = df.reset_index(drop=True)

    if len(df) == 0:
        raise RuntimeError(f"No usable documents in {parquet_path}")

    sampled = df.sample(n=min(n_docs, len(df)), random_state=seed).reset_index(drop=True)

    documents: list[dict[str, str]] = []
    ground_truth: dict[str, set[str]] = {}

    for idx, row in sampled.iterrows():
        siren = str(row["siren"]).strip()
        nom = str(row["nomUniteLegale"]).strip() if pd.notna(row["nomUniteLegale"]) else ""
        denomination = (
            str(row["denominationUsuelle1UniteLegale"]).strip()
            if pd.notna(row["denominationUsuelle1UniteLegale"])
            else ""
        )
        activite = (
            str(row["activitePrincipaleUniteLegale"]).strip()
            if pd.notna(row["activitePrincipaleUniteLegale"])
            else ""
        )
        categorie = (
            str(row["categorieJuridiqueUniteLegale"]).strip()
            if pd.notna(row["categorieJuridiqueUniteLegale"])
            else ""
        )

        text_parts = [p for p in [nom, denomination, activite, categorie] if p]
        content = " ".join(text_parts) if text_parts else nom

        doc_id = f"stock-{idx:06d}"
        documents.append({
            "id": doc_id,
            "title": nom or denomination or siren,
            "content": content,
            "siren": siren,
        })

    name_candidates = [
        (i, row["nomUniteLegale"])
        for i, row in sampled.iterrows()
        if pd.notna(row["nomUniteLegale"]) and len(str(row["nomUniteLegale"]).strip()) >= 3
    ]
    rng.shuffle(name_candidates)

    activity_codes = sampled["activitePrincipaleUniteLegale"].dropna().unique().tolist()
    rng.shuffle(activity_codes)

    categories = sampled["categorieJuridiqueUniteLegale"].dropna().unique().tolist()
    rng.shuffle(categories)

    queries: list[tuple[str, set[str]]] = []

    for _, name in name_candidates[:5]:
        if len(queries) >= 8:
            break
        name = str(name).strip()
        if not name or len(name) < 3:
            continue
        relevant = {
            documents[int(i)]["id"]  # type: ignore[index]
            for i, row in sampled.iterrows()  # type: ignore[attr-defined]
            if pd.notna(row["nomUniteLegale"]) and str(row["nomUniteLegale"]).strip() == name
        }
        if len(relevant) >= 1 and len(relevant) <= max(20, n_docs // 10):
            queries.append((name, relevant))

    for code in activity_codes[:5]:
        if len(queries) >= 10:
            break
        code = str(code).strip()
        if not code:
            continue
        relevant = {
            documents[int(i)]["id"]  # type: ignore[index]
            for i, row in sampled.iterrows()  # type: ignore[attr-defined]
            if pd.notna(row["activitePrincipaleUniteLegale"])
            and str(row["activitePrincipaleUniteLegale"]).strip() == code
        }
        if len(relevant) >= 2 and len(relevant) <= max(20, n_docs // 5):
            queries.append((code, relevant))

    for cat in categories[:3]:
        if len(queries) >= 10:
            break
        cat = str(cat).strip()
        if not cat:
            continue
        relevant = {
            documents[int(i)]["id"]  # type: ignore[index]
            for i, row in sampled.iterrows()  # type: ignore[attr-defined]
            if pd.notna(row["categorieJuridiqueUniteLegale"])
            and str(row["categorieJuridiqueUniteLegale"]).strip() == cat
        }
        if len(relevant) >= 2 and len(relevant) <= max(50, n_docs // 2):
            queries.append((cat, relevant))

    while len(queries) < 5 and name_candidates:
        idx, name = name_candidates.pop(0)
        name = str(name).strip()
        if not name or len(name) < 3:
            continue
        relevant = {
            documents[int(i)]["id"]  # type: ignore[index]
            for i, row in sampled.iterrows()  # type: ignore[attr-defined]
            if pd.notna(row["nomUniteLegale"]) and str(row["nomUniteLegale"]).strip() == name
        }
        if len(relevant) >= 1:
            queries.append((name, relevant))

    if not queries:
        for i in range(min(5, len(documents))):
            doc = documents[i]
            queries.append((doc["title"], {doc["id"]}))

    ground_truth = {q: gt for q, gt in queries}
    return documents, ground_truth


def _build_documents_gouv_local(
    n_docs: int,
    seed: int = 42,
    json_path: str = "benchmark/Datas/all_latest/2026-07-31_053230-data.gouv_local.json",
) -> tuple[list[dict[str, str]], dict[str, set[str]]]:
    """Sample real French public services from a gouv_local JSON file.

    The dataset contains ~86K services (mairies, bibliothèques, etc.)
    with names, addresses, opening hours, categories, and INSEE codes.
    Ground truth is built from exact name, category, type, and commune matches.

    Args:
        n_docs: Number of documents to sample.
        seed: Random seed for reproducibility.
        json_path: Path to the gouv_local JSON file.

    Returns:
        ``(documents, ground_truth)`` where ``ground_truth[query]`` is the
        set of relevant document IDs for that query.
    """
    rng = random.Random(seed)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    services = data.get("service", [])
    if not services:
        raise RuntimeError(f"No services found in {json_path}")

    # Filter services with at least a name
    valid = [s for s in services if s.get("nom")]
    if not valid:
        raise RuntimeError(f"No valid services with 'nom' in {json_path}")

    # Sample n_docs services
    sampled = rng.sample(valid, min(n_docs, len(valid)))

    documents: list[dict[str, str]] = []
    # Index by various fields for ground truth construction
    by_name: dict[str, list[int]] = {}
    by_category: dict[str, list[int]] = {}
    by_type: dict[str, list[int]] = {}
    by_commune: dict[str, list[int]] = {}
    by_pivot_type: dict[str, list[int]] = {}

    for idx, svc in enumerate(sampled):
        nom = str(svc.get("nom", "")).strip()
        categorie = str(svc.get("categorie", "")).strip().upper()
        type_org = str(svc.get("type_organisme", "")).strip().lower()
        code_insee = str(svc.get("code_insee_commune", "")).strip()
        pivot = svc.get("pivot", [])
        pivot_type = ""
        if isinstance(pivot, list) and pivot:
            pivot_type = str(pivot[0].get("type_service_local", "")).strip().lower()

        # Build searchable text
        text_parts = [nom]
        if categorie and categorie != "NONE":
            text_parts.append(f"categorie {categorie}")
        if type_org:
            text_parts.append(f"type {type_org}")
        if code_insee:
            text_parts.append(f"commune {code_insee}")
        if pivot_type:
            text_parts.append(f"service {pivot_type}")

        # Add address if present
        adresse = svc.get("adresse", [])
        if isinstance(adresse, list) and adresse:
            addr = adresse[0]
            addr_parts = []
            if addr.get("numero_voie"):
                addr_parts.append(str(addr["numero_voie"]))
            if addr.get("type_voie"):
                addr_parts.append(str(addr["type_voie"]))
            if addr.get("nom_voie"):
                addr_parts.append(str(addr["nom_voie"]))
            if addr.get("code_postal"):
                addr_parts.append(str(addr["code_postal"]))
            if addr.get("nom_commune"):
                addr_parts.append(str(addr["nom_commune"]))
            if addr_parts:
                text_parts.append("adresse " + " ".join(addr_parts))

        # Add mission if present
        mission = svc.get("mission", "")
        if mission:
            text_parts.append(str(mission).strip())

        content = " ".join(text_parts)

        doc_id = f"gouv-{idx:06d}"
        documents.append({
            "id": doc_id,
            "title": nom,
            "content": content,
            "nom": nom,
            "categorie": categorie,
            "type_organisme": type_org,
            "code_insee": code_insee,
            "pivot_type": pivot_type,
        })

        # Build lookup indexes
        by_name.setdefault(nom.lower(), []).append(idx)
        if categorie and categorie != "NONE":
            by_category.setdefault(categorie, []).append(idx)
        if type_org:
            by_type.setdefault(type_org, []).append(idx)
        if code_insee:
            by_commune.setdefault(code_insee, []).append(idx)
        if pivot_type:
            by_pivot_type.setdefault(pivot_type, []).append(idx)

    # Build queries from the sampled data with 3 difficulty levels
    queries: list[tuple[str, set[str]]] = []

    def _add_query(
        query_text: str,
        relevant_indices: list[int],
        min_rel: int = 1,
        max_rel: int | None = None,
    ) -> None:
        if len(queries) >= 20:
            return
        rel = set(relevant_indices)
        if len(rel) < min_rel:
            return
        if max_rel is not None and len(rel) > max_rel:
            return
        queries.append((query_text, {documents[i]["id"] for i in rel}))

    # Level 1: Exact queries (baseline)
    for nom_lower, indices in list(by_name.items())[:4]:
        if len(queries) >= 20:
            break
        if len(nom_lower) < 3:
            continue
        _add_query(nom_lower, indices, min_rel=1, max_rel=max(10, n_docs // 10))

    # Level 2: Abbreviated / partial queries
    for nom_lower, indices in list(by_name.items())[4:8]:
        if len(queries) >= 20:
            break
        if len(nom_lower) < 3:
            continue
        words = nom_lower.split()
        if len(words) >= 2:
            abbreviated = " ".join(words[:2])
            _add_query(abbreviated, indices, min_rel=1, max_rel=max(20, n_docs // 8))
        if len(words) >= 3:
            abbreviated = " ".join(words[:3])
            _add_query(abbreviated, indices, min_rel=1, max_rel=max(20, n_docs // 8))

    # Level 3: Semantic queries (paraphrases, different wording)
    def _semantic_template_1(nom: str) -> str:
        return (
            "services publics "
            + nom.replace("mairie", "municipal")
            .replace("police municipale", "police locale")
        )

    def _semantic_template_2(nom: str) -> str:
        return "administration " + (nom.split()[0] if nom.split() else nom)

    def _semantic_template_3(nom: str) -> str:
        return "organisme " + (nom.split()[0] if nom.split() else nom)

    semantic_templates = [
        _semantic_template_1,
        _semantic_template_2,
        _semantic_template_3,
        lambda nom: f"etablissement public {nom}",
        lambda nom: f"service public {nom}",
    ]

    for nom_lower, indices in list(by_name.items())[:10]:
        if len(queries) >= 20:
            break
        if len(nom_lower) < 4:
            continue
        for template in semantic_templates[:2]:
            query_text = template(nom_lower)
            if query_text != nom_lower:
                _add_query(query_text, indices, min_rel=1, max_rel=max(30, n_docs // 6))

    # Category queries at different specificity levels
    for cat, indices in list(by_category.items())[:5]:
        if len(queries) >= 20:
            break
        _add_query(cat, indices, min_rel=2, max_rel=max(50, n_docs // 4))

    # Commune INSEE queries
    for insee, indices in list(by_commune.items())[:4]:
        if len(queries) >= 20:
            break
        _add_query(insee, indices, min_rel=2, max_rel=max(100, n_docs // 2))

    # Type organisme queries
    for type_org, indices in list(by_type.items())[:3]:
        if len(queries) >= 20:
            break
        _add_query(type_org, indices, min_rel=2, max_rel=max(50, n_docs // 4))

    # Fallback: ensure we have at least some queries
    if len(queries) < 5:
        for nom_lower, indices in list(by_name.items())[:5]:
            if nom_lower not in [q for q, _ in queries]:
                queries.append((nom_lower, {documents[i]["id"] for i in indices}))

    ground_truth = {q: gt for q, gt in queries}
    return documents, ground_truth


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------
class _ListSource:
    """Minimal DataSource adapter for an in-memory list of document dicts."""

    name = "list"

    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._docs = documents

    def discover_schema(self) -> Schema:
        raise NotImplementedError("Schema must be provided externally for _ListSource")

    def iter_documents(self) -> Any:
        yield from self._docs

    def stream_batches(self, batch_size: int = 1000) -> Any:
        batch: list[dict[str, Any]] = []
        for doc in self._docs:
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def health_check(self) -> bool:
        return bool(self._docs)


def _build_index(
    tmp_path: Path,
    documents: list[dict[str, str]],
    embeddings: list[list[float]],
    dimension: int,
    index_mode: str = "legacy",
) -> tuple[Any, Schema]:
    """Build a Whoosh index with a native VECTOR column.

    Args:
        tmp_path: Temporary directory for the index.
        documents: Indexed documents.
        embeddings: One embedding vector per document.
        dimension: Embedding dimensionality.
        index_mode: ``"legacy"`` for raw ``ix.writer()``, ``"modern"``
            for :class:`ModernIndexBuilder`, or ``"parallel"`` for
            :class:`ParallelIndexBuilder`.

    Returns:
        (index, schema) tuple.
    """
    idx_dir = tmp_path / "index"
    idx_dir.mkdir()
    schema = Schema(
        id=TEXT(stored=True),
        title=TEXT(stored=True),
        content=TEXT,
        vector=VECTOR(dimension=dimension, normalized=True),
    )

    if index_mode == "modern":
        from whoosh_modern.indexing.batch_writer import BatchIndexWriter

        ix = create_in(str(idx_dir), schema)
        with BatchIndexWriter(ix, batch_size=5000, limitmb=512, multisegment=True) as writer:
            for doc, embedding in zip(documents, embeddings, strict=False):
                writer.add_batch([{
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "vector": embedding,
                }])
        return ix, schema

    if index_mode == "parallel":
        from whoosh_modern.indexing import ParallelIndexBuilder

        batches: list[list[dict[str, Any]]] = []
        batch: list[dict[str, Any]] = []
        for doc, embedding in zip(documents, embeddings, strict=False):
            batch.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "vector": embedding,
            })
            if len(batch) >= 5000:
                batches.append(batch)
                batch = []
        if batch:
            batches.append(batch)
        ParallelIndexBuilder(
            schema=schema,
            index_path=str(idx_dir),
            workers=4,
            batch_size=10000,
        ).build(iter(batches))
        ix = open_dir(str(idx_dir))
        return ix, schema

    ix = create_in(str(idx_dir), schema)
    writer = ix.writer()
    for doc, embedding in zip(documents, embeddings, strict=False):
        writer.add_document(
            id=doc["id"],
            title=doc["title"],
            content=doc["content"],
            vector=embedding,
        )
    writer.commit()
    return ix, schema


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------
def _doc_id_for(searcher: Any, docnum: int) -> str | None:
    """Resolve a docnum to its stored ``id`` field value."""
    fields = searcher.stored_fields(docnum)
    if fields:
        doc_id = fields.get("id")
        if doc_id is not None:
            return str(doc_id)
    return None


def _bm25_search(
    searcher: Any,
    parser: QueryParser,
    query_text: str,
    limit: int = 10,
) -> list[tuple[str, float]]:
    """Run a BM25 search and return (doc_id, score) pairs."""
    q = parser.parse(query_text)
    results = searcher.search(q, limit=limit)
    hits: list[tuple[str, float]] = []
    for hit in results:
        doc_id = hit.fields().get("id")
        if doc_id is not None:
            hits.append((str(doc_id), float(hit.score)))
    return hits


def _vector_search_native(
    vector_searcher: VectorSearcher,
    searcher: Any,
    query_vector: list[float],
    k: int = 10,
) -> list[tuple[str, float]]:
    """Run a native vector search and resolve docnums to doc_ids."""
    hits = vector_searcher.search(query_vector, k=k)
    resolved: list[tuple[str, float]] = []
    for docnum, score in hits:
        doc_id = _doc_id_for(searcher, docnum)
        if doc_id is not None:
            resolved.append((doc_id, float(score)))
    return resolved


def _hybrid_search_native(
    hybrid_searcher: HybridSearcher,
    query_text: str,
    query_vector: list[float],
    limit: int = 10,
    method: str = "weighted",
    alpha: float = 0.5,
    rrf_k: int = 60,
    vector_k: int = 10,
) -> list[tuple[str, float]]:
    """Run hybrid search using a pre-built HybridSearcher."""
    results = hybrid_searcher.search(
        query_text,
        query_vector=query_vector,
        limit=limit,
        method=method,
        alpha=alpha,
        rrf_k=rrf_k,
        vector_k=vector_k,
    )
    return [(r.doc_id, float(r.score)) for r in results]


def _print_score_distribution(
    bm25_hits: list[tuple[str, float]],
    vec_hits: list[tuple[str, float]],
) -> None:
    """Print min/max/mean/stddev and percentiles for BM25 and vector scores."""
    bm25_scores = [s for _, s in bm25_hits]
    vec_scores = [s for _, s in vec_hits]

    def _stats(scores: list[float], label: str) -> str:
        if not scores:
            return f"{label}: n/a"
        mean = statistics.mean(scores)
        stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0
        p50 = _percentile(scores, 50)
        p90 = _percentile(scores, 90)
        p95 = _percentile(scores, 95)
        p99 = _percentile(scores, 99)
        return (
            f"{label}: min={min(scores):.4f} p50={p50:.4f} p90={p90:.4f} "
            f"p95={p95:.4f} p99={p99:.4f} max={max(scores):.4f} "
            f"mean={mean:.4f} std={stdev:.4f}"
        )

    print(f"    {_stats(bm25_scores, 'BM25')}")
    print(f"    {_stats(vec_scores, 'VECTOR')}")


# ---------------------------------------------------------------------------
# Ranking metrics
# ---------------------------------------------------------------------------
def _precision_at_k(hit_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Compute Precision@K."""
    top = hit_ids[:k]
    if not top:
        return 0.0
    return sum(1 for doc_id in top if doc_id in relevant_ids) / len(top)


def _recall_at_k(hit_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Compute Recall@K."""
    if not relevant_ids:
        return 0.0
    top = set(hit_ids[:k])
    return len(top & relevant_ids) / len(relevant_ids)


def _mrr_at_k(hit_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Compute MRR@K."""
    for rank, doc_id in enumerate(hit_ids[:k], start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def _ndcg_at_k(hit_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Compute NDCG@K with binary relevance."""
    top = hit_ids[:k]
    if not top or not relevant_ids:
        return 0.0

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, doc_id in enumerate(top, start=2)
        if doc_id in relevant_ids
    )
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(2, ideal_hits + 2))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def _percentile(values: list[float], p: float) -> float:
    """Compute the p-th percentile of a list of values."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n == 1:
        return s[0]
    idx = (p / 100.0) * (n - 1)
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    if lower == upper:
        return s[lower]
    frac = idx - lower
    return s[lower] * (1.0 - frac) + s[upper] * frac


@dataclass(frozen=True)
class QueryMetrics:
    """Per-query ranking metrics for one search mode."""

    query: str
    mode: str
    latency_ms: float
    recall: float
    precision: float
    mrr: float
    ndcg: float


@dataclass(frozen=True)
class ScaleResult:
    """Aggregated results for one corpus scale."""

    scale: int
    mode: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    recall: float
    precision: float
    mrr: float
    ndcg: float


@dataclass(frozen=True)
class HybridTuningResult:
    """Result for one hybrid parameter combination."""

    rrf_k: int
    vector_k: int
    alpha: float
    method: str
    p50_ms: float
    recall: float
    precision: float
    mrr: float
    ndcg: float


@dataclass(frozen=True)
class EmbeddingTuningResult:
    """Result for one embedding configuration."""

    batch_size: int
    threads: int | None
    parallel: int | None
    docs_per_second: float
    ms_per_doc: float
    total_s: float


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------
def run_benchmark(
    tmp_path: Path,
    documents: list[dict[str, str]],
    queries: list[str],
    ground_truth: dict[str, set[str]],
    provider: LibEmbeddingProvider,
    k: int = 20,
    bm25_k: int = 20,
    show_score_dist: bool = False,
    index_mode: str = "legacy",
) -> tuple[list[QueryMetrics], dict[str, float]]:
    """Run the full benchmark with explicit phase timing.

    Returns:
        ``(results, phase_times)``
    """
    phase_times: dict[str, float] = {}

    # --- Phase 1: document embedding ---
    t0 = time.perf_counter()
    doc_texts = [doc["content"] for doc in documents]
    doc_embeddings = provider.embed_batch(doc_texts)
    dimension = provider.dimension
    phase_times["embed_docs_s"] = time.perf_counter() - t0

    # --- Phase 2: VECTOR indexing ---
    t0 = time.perf_counter()
    ix, schema = _build_index(tmp_path, documents, doc_embeddings, dimension, index_mode=index_mode)
    phase_times["index_s"] = time.perf_counter() - t0

    # --- Phase 3: query embedding ---
    t0 = time.perf_counter()
    query_embeddings = provider.embed_batch(queries)
    phase_times["embed_queries_s"] = time.perf_counter() - t0

    results: list[QueryMetrics] = []
    try:
        with ix.searcher() as searcher:
            vector_searcher = VectorSearcher(searcher.reader(), "vector")
            hybrid_searcher = HybridSearcher(
                searcher, id_field="id", vector_column="vector"
            )
            parser = QueryParser(schema.names()[0], schema)

            for query_text, query_vector in zip(queries, query_embeddings, strict=False):
                relevant_ids = ground_truth.get(query_text, set())

                # --- BM25 ---
                t0 = time.perf_counter()
                bm25_hits = _bm25_search(searcher, parser, query_text, limit=bm25_k)
                bm25_ms = (time.perf_counter() - t0) * 1000
                bm25_ids = [doc_id for doc_id, _ in bm25_hits]

                # --- Vector (native column) ---
                t0 = time.perf_counter()
                vec_hits = _vector_search_native(
                    vector_searcher, searcher, query_vector, k=k
                )
                vec_ms = (time.perf_counter() - t0) * 1000
                vec_ids = [doc_id for doc_id, _ in vec_hits]

                if show_score_dist:
                    _print_score_distribution(bm25_hits, vec_hits)

                # --- Hybrid weighted ---
                t0 = time.perf_counter()
                hyb_w_hits = _hybrid_search_native(
                    hybrid_searcher, query_text, query_vector, limit=k, method="weighted"
                )
                hyb_w_ms = (time.perf_counter() - t0) * 1000
                hyb_w_ids = [doc_id for doc_id, _ in hyb_w_hits]

                # --- Hybrid RRF ---
                t0 = time.perf_counter()
                hyb_r_hits = _hybrid_search_native(
                    hybrid_searcher, query_text, query_vector, limit=k, method="rrf"
                )
                hyb_r_ms = (time.perf_counter() - t0) * 1000
                hyb_r_ids = [doc_id for doc_id, _ in hyb_r_hits]

                for mode, hit_ids, latency_ms in [
                    ("bm25", bm25_ids, bm25_ms),
                    ("vector", vec_ids, vec_ms),
                    ("hybrid_weighted", hyb_w_ids, hyb_w_ms),
                    ("hybrid_rrf", hyb_r_ids, hyb_r_ms),
                ]:
                    results.append(
                        QueryMetrics(
                            query=query_text,
                            mode=mode,
                            latency_ms=latency_ms,
                            recall=_recall_at_k(hit_ids, relevant_ids, k),
                            precision=_precision_at_k(hit_ids, relevant_ids, k),
                            mrr=_mrr_at_k(hit_ids, relevant_ids, k),
                            ndcg=_ndcg_at_k(hit_ids, relevant_ids, k),
                        )
                    )
    finally:
        ix.close()

    return results, phase_times


# ---------------------------------------------------------------------------
# HybridSearcher tuning
# ---------------------------------------------------------------------------
def _tune_hybrid(
    documents: list[dict[str, str]],
    queries: list[str],
    ground_truth: dict[str, set[str]],
    provider: LibEmbeddingProvider,
    k: int = 20,
    bm25_k: int = 20,
) -> list[HybridTuningResult]:
    """Sweep hybrid parameters and return all results sorted by NDCG desc."""
    doc_texts = [doc["content"] for doc in documents]
    doc_embeddings = provider.embed_batch(doc_texts)
    dimension = provider.dimension

    tmp_path = Path("benchmark") / "indexes" / "hybrid_tune"
    if tmp_path.exists():
        import shutil
        shutil.rmtree(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)

    ix, schema = _build_index(tmp_path, documents, doc_embeddings, dimension, index_mode="legacy")
    query_embeddings = provider.embed_batch(queries)

    tuning_results: list[HybridTuningResult] = []
    try:
        with ix.searcher() as searcher:
            vector_searcher = VectorSearcher(searcher.reader(), "vector")
            hybrid_searcher = HybridSearcher(
                searcher, id_field="id", vector_column="vector"
            )
            parser = QueryParser(schema.names()[0], schema)

            for query_text, query_vector in zip(queries, query_embeddings, strict=False):
                relevant_ids = ground_truth.get(query_text, set())

                bm25_hits = _bm25_search(searcher, parser, query_text, limit=bm25_k)
                bm25_ids = [doc_id for doc_id, _ in bm25_hits]

                vec_hits = _vector_search_native(
                    vector_searcher, searcher, query_vector, k=k
                )
                vec_ids = [doc_id for doc_id, _ in vec_hits]

                print(f"  Query {query_text!r}")
                print(
                    f"    baseline  BM25={_recall_at_k(bm25_ids, relevant_ids, k):.3f} "
                    f"VECTOR={_recall_at_k(vec_ids, relevant_ids, k):.3f}"
                )
                _print_score_distribution(bm25_hits, vec_hits)

                for rrf_k in RRF_K_SWEEP:
                    for vector_k in VECTOR_K_SWEEP:
                        for alpha in ALPHA_SWEEP:
                            for method in ("rrf", "weighted"):
                                t0 = time.perf_counter()
                                hyb_hits = _hybrid_search_native(
                                    hybrid_searcher,
                                    query_text,
                                    query_vector,
                                    limit=k,
                                    method=method,
                                    alpha=alpha,
                                    rrf_k=rrf_k,
                                    vector_k=vector_k,
                                )
                                latency_ms = (time.perf_counter() - t0) * 1000
                                hyb_ids = [doc_id for doc_id, _ in hyb_hits]
                                tuning_results.append(
                                    HybridTuningResult(
                                        rrf_k=rrf_k,
                                        vector_k=vector_k,
                                        alpha=alpha,
                                        method=method,
                                        p50_ms=latency_ms,
                                        recall=_recall_at_k(hyb_ids, relevant_ids, k),
                                        precision=_precision_at_k(hyb_ids, relevant_ids, k),
                                        mrr=_mrr_at_k(hyb_ids, relevant_ids, k),
                                        ndcg=_ndcg_at_k(hyb_ids, relevant_ids, k),
                                    )
                                )
    finally:
        ix.close()
        import shutil
        if tmp_path.exists():
            shutil.rmtree(tmp_path, ignore_errors=True)

    return tuning_results


def _print_hybrid_tuning(results: list[HybridTuningResult]) -> None:
    """Print hybrid tuning sweep summary."""
    if not results:
        return

    print(f"\n{'=' * 100}")
    print("  HybridSearcher tuning sweep")
    print(f"{'=' * 100}")

    # Group by (rrf_k, vector_k, method) and average over alpha
    groups: dict[tuple[int, int, str], list[HybridTuningResult]] = {}
    for r in results:
        key = (r.rrf_k, r.vector_k, r.method)
        groups.setdefault(key, []).append(r)

    print(
        f"{'method':<10} {'rrf_k':>6} {'vec_k':>6} {'alpha':>6} "
        f"{'p50_ms':>10} {'recall':>8} {'prec':>8} {'mrr':>8} {'ndcg':>8}"
    )
    print("-" * 100)

    # Print a few representative configs
    shown = 0
    for (rrf_k, vector_k, method), items in sorted(groups.items()):
        for alpha_val in ALPHA_SWEEP:
            matching = [r for r in items if abs(r.alpha - alpha_val) < 1e-9]
            if not matching:
                continue
            r = matching[0]
            print(
                f"{method:<10} {rrf_k:>6} {vector_k:>6} {alpha_val:>6.1f} "
                f"{r.p50_ms:>10.3f} {r.recall:>8.3f} {r.precision:>8.3f} "
                f"{r.mrr:>8.3f} {r.ndcg:>8.3f}"
            )
            shown += 1
            if shown >= 20:
                break
        if shown >= 20:
            break

    # Best by NDCG
    best_ndcg = max(results, key=lambda r: r.ndcg)
    print(f"\nBest NDCG: {best_ndcg.ndcg:.3f}")
    print(
        f"  method={best_ndcg.method} rrf_k={best_ndcg.rrf_k} "
        f"vector_k={best_ndcg.vector_k} alpha={best_ndcg.alpha:.1f}"
    )

    # Best by latency (among top-5 NDCG)
    top_ndcg = sorted(results, key=lambda r: r.ndcg, reverse=True)[:5]
    best_latency = min(top_ndcg, key=lambda r: r.p50_ms)
    print(f"\nBest latency (among top-5 NDCG): {best_latency.p50_ms:.3f} ms")
    print(
        f"  method={best_latency.method} rrf_k={best_latency.rrf_k} "
        f"vector_k={best_latency.vector_k} alpha={best_latency.alpha:.1f} "
        f"NDCG={best_latency.ndcg:.3f}"
    )


# ---------------------------------------------------------------------------
# Embedding tuning
# ---------------------------------------------------------------------------
def _tune_embedding(
    documents: list[dict[str, str]],
    model_name: str = "arctic-embed-s",
    provider_type: str = "libembedding",
) -> list[EmbeddingTuningResult]:
    """Sweep embedding parameters and report throughput.

    Sweeps over:
    - batch_size: EMBEDDING_BATCH_SWEEP
    - threads: THREADS_SWEEP (FastEmbed only)
    - parallel: PARALLEL_SWEEP (FastEmbed only)

    For ``libembedding``, only ``batch_size`` is varied; ``threads`` and
    ``parallel`` are fixed at their default values and printed as ``"-"``.
    """
    doc_texts = [doc["content"] for doc in documents]
    results: list[EmbeddingTuningResult] = []

    if provider_type == "fastembed":
        configs = []
        for batch_size in EMBEDDING_BATCH_SWEEP:
            for threads in THREADS_SWEEP:
                for parallel in PARALLEL_SWEEP:
                    configs.append((batch_size, threads, parallel))

        for batch_size, threads, parallel in configs:
            provider = FastEmbedProvider(
                model_name=model_name,
                threads=threads,
                parallel=parallel,
                batch_size=batch_size,
            )
            t0 = time.perf_counter()
            provider.embed_batch(doc_texts)
            total_s = time.perf_counter() - t0

            n = len(doc_texts)
            results.append(
                EmbeddingTuningResult(
                    batch_size=batch_size,
                    threads=threads,
                    parallel=parallel,
                    docs_per_second=n / total_s if total_s > 0 else 0.0,
                    ms_per_doc=(total_s / n) * 1000 if n > 0 else 0.0,
                    total_s=total_s,
                )
            )
            print(
                f"  batch={batch_size:>3d} threads={threads} parallel={parallel}  "
                f"{n / total_s:>8.1f} docs/s  "
                f"{(total_s / n) * 1000:>8.2f} ms/doc  "
                f"total={total_s:>8.2f} s"
            )
    else:
        for batch_size in EMBEDDING_BATCH_SWEEP:
            provider = LibEmbeddingProvider(
                model_name=model_name,
                batch_size=batch_size,
            )
            t0 = time.perf_counter()
            provider.embed_batch(doc_texts)
            total_s = time.perf_counter() - t0

            n = len(doc_texts)
            results.append(
                EmbeddingTuningResult(
                    batch_size=batch_size,
                    threads=None,
                    parallel=None,
                    docs_per_second=n / total_s if total_s > 0 else 0.0,
                    ms_per_doc=(total_s / n) * 1000 if n > 0 else 0.0,
                    total_s=total_s,
                )
            )
            print(
                f"  batch={batch_size:>3d}  "
                f"{n / total_s:>8.1f} docs/s  "
                f"{(total_s / n) * 1000:>8.2f} ms/doc  "
                f"total={total_s:>8.2f} s"
            )

    return results


def _print_embedding_tuning(results: list[EmbeddingTuningResult]) -> None:
    """Print embedding tuning summary."""
    if not results:
        return

    print(f"\n{'=' * 100}")
    print("  Embedding tuning")
    print(f"{'=' * 100}")
    header = (
        f"{'batch':>6} {'threads':>8} {'parallel':>8} "
        f"{'docs/s':>10} {'ms/doc':>10} {'total_s':>10}"
    )
    print(header)
    print("-" * 100)
    for r in results:
        threads_str = str(r.threads) if r.threads is not None else "-"
        parallel_str = str(r.parallel) if r.parallel is not None else "-"
        print(
            f"{r.batch_size:>6} {threads_str:>8} {parallel_str:>8} "
            f"{r.docs_per_second:>10.1f} {r.ms_per_doc:>10.2f} {r.total_s:>10.2f}"
        )

    best = max(results, key=lambda r: r.docs_per_second)
    threads_str = str(best.threads) if best.threads is not None else "-"
    parallel_str = str(best.parallel) if best.parallel is not None else "-"
    print(
        f"\nBest throughput: {best.docs_per_second:.1f} docs/s "
        f"at batch={best.batch_size} threads={threads_str} parallel={parallel_str}"
    )


# ---------------------------------------------------------------------------
# Aggregation and printing
# ---------------------------------------------------------------------------
def _aggregate_scale(
    results: list[QueryMetrics],
    scale: int = 0,
) -> list[ScaleResult]:
    """Aggregate per-query results into per-mode scale summaries."""
    groups: dict[str, list[QueryMetrics]] = {}
    for r in results:
        groups.setdefault(r.mode, []).append(r)

    scale_results: list[ScaleResult] = []
    for mode in ("bm25", "vector", "hybrid_weighted", "hybrid_rrf"):
        items = groups.get(mode, [])
        if not items:
            continue
        latencies = [item.latency_ms for item in items]
        scale_results.append(
            ScaleResult(
                scale=scale,
                mode=mode,
                p50_ms=_percentile(latencies, 50),
                p95_ms=_percentile(latencies, 95),
                p99_ms=_percentile(latencies, 99),
                recall=statistics.mean(item.recall for item in items),
                precision=statistics.mean(item.precision for item in items),
                mrr=statistics.mean(item.mrr for item in items),
                ndcg=statistics.mean(item.ndcg for item in items),
            )
        )
    return scale_results


def _print_scale_summary(scale_results: list[ScaleResult], n_docs: int) -> None:
    """Print the comparative summary table for one scale."""
    print(f"\n{'=' * 90}")
    print(f"  Scale: {n_docs:,} documents  |  K={K}  |  model={PROVIDER_MODEL}")
    print(f"{'=' * 90}")
    header = (
        f"{'mode':<20} {'p50_ms':>10} {'p95_ms':>10} {'p99_ms':>10} "
        f"{'recall@' + str(K):>10} {'prec@' + str(K):>10} "
        f"{'mrr@' + str(K):>10} {'ndcg@' + str(K):>10}"
    )
    print(header)
    print("-" * len(header))
    for sr in scale_results:
        print(
            f"{sr.mode:<20} "
            f"{sr.p50_ms:>10.3f} {sr.p95_ms:>10.3f} {sr.p99_ms:>10.3f} "
            f"{sr.recall:>10.3f} {sr.precision:>10.3f} "
            f"{sr.mrr:>10.3f} {sr.ndcg:>10.3f}"
        )


def _print_comparative_table(all_results: dict[int, list[ScaleResult]], scales: list[int]) -> None:
    """Print a comparative table of p50 latency across the requested scales."""
    print(f"\n{'=' * 90}")
    print("  Comparative table: search latency p50 (ms)")
    print(f"{'=' * 90}")
    header = (
        f"{'mode':<20} "
        + " ".join(f"{n:>10}" for n in scales)
    )
    print(header)
    print("-" * len(header))
    for mode in ("bm25", "vector", "hybrid_weighted", "hybrid_rrf"):
        row = f"{mode:<20}"
        for n in scales:
            srs = all_results.get(n, [])
            sr = next((s for s in srs if s.mode == mode), None)
            if sr is not None:
                row += f"{sr.p50_ms:>10.3f}"
            else:
                row += f"{'N/A':>10}"
        print(row)


def _print_phase_times(phase_times: dict[str, float], index_mode: str = "legacy") -> None:
    """Print per-phase timing breakdown."""
    print("\n=== Phase timing ===")
    labels = {
        "embed_docs_s": "Document embedding",
        "index_s": f"VECTOR indexing + commit ({index_mode})",
        "embed_queries_s": "Query embedding",
    }
    for key, label in labels.items():
        if key in phase_times:
            print(f"  {label:<30s} {phase_times[key]:>8.3f} s")
    total = sum(phase_times.get(k, 0) for k in labels)
    print(f"  {'Total preparation':<30s} {total:>8.3f} s")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """Run the multi-scale hybrid search benchmark with optional tuning."""
    parser = argparse.ArgumentParser(
        description="Hybrid search benchmark with optional tuning sweeps"
    )
    parser.add_argument(
        "--scales",
        type=str,
        default="5000,10000,50000,100000",
        help="Comma-separated corpus sizes",
    )
    parser.add_argument(
        "--model",
        default=PROVIDER_MODEL,
        help="Embedding model preset or identifier",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="libembedding",
        choices=["libembedding", "fastembed"],
        help="Embedding provider backend: libembedding or fastembed",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=K,
        help="Evaluation cutoff",
    )
    parser.add_argument(
        "--bm25-k",
        type=int,
        default=BM25_K,
        help="BM25 result set size",
    )
    parser.add_argument(
        "--tune-hybrid",
        action="store_true",
        help="Run HybridSearcher parameter sweep (rrf_k, vector_k, alpha)",
    )
    parser.add_argument(
        "--tune-embedding",
        action="store_true",
        help="Run embedding batch_size sweep",
    )
    parser.add_argument(
        "--score-dist",
        action="store_true",
        help="Print BM25/vector score distributions per query",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help=(
            "Save results to a file (csv or json, inferred from extension)"
        ),
    )
    parser.add_argument(
        "--corpus",
        type=str,
        default="synthetic",
        choices=["synthetic", "stock", "gouv_local"],
        help=(
            "Corpus mode: synthetic (topic-based), stock (real French "
            "companies), or gouv_local (French public services)"
        ),
    )
    parser.add_argument(
        "--index-mode",
        type=str,
        default="legacy",
        choices=["legacy", "modern", "parallel"],
        help=(
            "Indexing mode: legacy (ix.writer), modern (ModernIndexBuilder), "
            "or parallel (ParallelIndexBuilder)"
        ),
    )
    parser.add_argument(
        "--compare-providers",
        action="store_true",
        help=(
            "Compare libembedding vs fastembed on the same model "
            "(--model must be a shared model like BAAI/bge-small-en-v1.5)"
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    scales = [int(x.strip()) for x in args.scales.split(",") if x.strip()]
    model_name = args.model
    provider_type = args.provider
    k = args.k
    bm25_k = args.bm25_k
    corpus = args.corpus
    index_mode = args.index_mode

    if args.compare_providers:
        compare_model = "BAAI/bge-small-en-v1.5"
        compare_scale = scales[0] if scales else 100
        print(
            f"\nProvider comparison mode: model={compare_model}, "
            f"scale={compare_scale}, corpus={corpus}, index_mode={index_mode}"
        )

        if corpus == "gouv_local":
            documents, ground_truth = _build_documents_gouv_local(compare_scale)
        elif corpus == "stock":
            documents, ground_truth = _build_documents_stock(compare_scale)
        else:
            documents, ground_truth = _build_documents(compare_scale)
        query_texts = list(ground_truth.keys())

        lib_result, fast_result = _compare_providers(
            documents=documents,
            queries=query_texts,
            ground_truth=ground_truth,
            model_name=compare_model,
            scale=compare_scale,
            k=k,
            bm25_k=bm25_k,
            index_mode=index_mode,
        )
        print_provider_comparison(lib_result, fast_result)
        return 0

    provider = _create_provider(provider_type=provider_type, model_name=model_name)
    print(f"Provider type: {provider_type}")
    print(f"Provider: {provider}")
    print(f"Embedding dimension: {provider.dimension}")
    print(f"Scales: {scales}")
    print(f"K={k}, BM25_K={bm25_k}")
    print(f"Corpus: {corpus}")
    print(f"Index mode: {index_mode}")
    print(f"Tune hybrid: {args.tune_hybrid}")
    print(f"Tune embedding: {args.tune_embedding}")

    all_results: dict[int, list[ScaleResult]] = {}
    last_phase_times: dict[str, float] = {}

    # --- Embedding tuning (before search benchmark) ---
    if args.tune_embedding:
        print(f"\n{'#' * 80}")
        print("  Embedding tuning")
        print(f"{'#' * 80}")
        # Use 1K docs for fast embedding tuning
        if corpus == "gouv_local":
            tune_docs, _ = _build_documents_gouv_local(1000)
        elif corpus == "stock":
            tune_docs, _ = _build_documents_stock(1000)
        else:
            tune_docs, _ = _build_documents(1000)
        tune_results = _tune_embedding(
            tune_docs,
            model_name=model_name,
            provider_type=provider_type,
        )
        _print_embedding_tuning(tune_results)

    # --- Search benchmark across scales ---
    for n_docs in scales:
        print(f"\n{'#' * 90}")
        print(f"  Scale: {n_docs:,} documents")
        print(f"{'#' * 90}")

        tmp_path = Path("benchmark") / "indexes" / f"hybrid_{n_docs}"
        if tmp_path.exists():
            import shutil
            shutil.rmtree(tmp_path)
        tmp_path.mkdir(parents=True, exist_ok=True)

        if corpus == "gouv_local":
            print(f"Sampling {n_docs:,} real public services from gouv_local...")
            documents, ground_truth = _build_documents_gouv_local(n_docs)
            query_texts = list(ground_truth.keys())
        elif corpus == "stock":
            print(f"Sampling {n_docs:,} real company documents from parquet...")
            documents, ground_truth = _build_documents_stock(n_docs)
            query_texts = list(ground_truth.keys())
        else:
            print(f"Generating {n_docs:,} topic-based documents...")
            documents, ground_truth = _build_documents(n_docs)
            query_texts = [q for q, _ in QUERIES]

        print("Ground truth sizes:")
        for q in query_texts:
            gt = ground_truth.get(q, set())
            print(f"  {q!r:30s}  {len(gt):>5d} relevant docs")

        t0_total = time.perf_counter()
        try:
            results, phase_times = run_benchmark(
                tmp_path, documents, query_texts, ground_truth,
                provider, k=k, bm25_k=bm25_k,
                show_score_dist=args.score_dist,
                index_mode=index_mode,
            )
            total_ms = (time.perf_counter() - t0_total) * 1000

            print(f"\nTotal run: {total_ms:.1f} ms")
            _print_phase_times(phase_times, index_mode=index_mode)
            last_phase_times = phase_times

            scale_results = _aggregate_scale(results, scale=n_docs)
            all_results[n_docs] = scale_results

            _print_scale_summary(scale_results, n_docs)

            print("\nPer-query raw results:")
            for r in results:
                print(
                    f"  [{r.mode:<20}] {r.query!r:25s} "
                    f"{r.latency_ms:8.3f} ms  "
                    f"recall={r.recall:.3f} prec={r.precision:.3f} "
                    f"mrr={r.mrr:.3f} ndcg={r.ndcg:.3f}"
                )
        finally:
            import shutil
            if tmp_path.exists():
                shutil.rmtree(tmp_path, ignore_errors=True)

    # --- Hybrid tuning (after search benchmark, on smallest scale) ---
    if args.tune_hybrid and scales:
        print(f"\n{'#' * 100}")
        print("  HybridSearcher tuning")
        print(f"{'#' * 100}")

        n_docs = scales[0]
        print(f"Using {n_docs:,} documents for tuning...")
        if corpus == "gouv_local":
            documents, ground_truth = _build_documents_gouv_local(n_docs)
        elif corpus == "stock":
            documents, ground_truth = _build_documents_stock(n_docs)
        else:
            documents, ground_truth = _build_documents(n_docs)
        query_texts = list(ground_truth.keys())
        tuning_results = _tune_hybrid(
            documents, query_texts, ground_truth, provider, k=k
        )
        _print_hybrid_tuning(tuning_results)

    _print_comparative_table(all_results, scales)

    if args.output:
        _save_results(args.output, all_results, last_phase_times)

    return 0


def _save_results(
    output_path: str,
    all_results: dict[int, list[ScaleResult]],
    phase_times: dict[str, float],
) -> None:
    """Save benchmark results to a file.

    Supports CSV and JSON formats, inferred from the file extension.

    Args:
        output_path: Path to the output file.
        all_results: Dictionary mapping scale to list of ScaleResult objects.
        phase_times: Dictionary of phase timing information.
    """
    import csv
    import json

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".json":
        data = {
            "scales": {
                str(n): [_scale_result_to_dict(sr) for sr in srs]
                for n, srs in all_results.items()
            },
            "phase_times": phase_times,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"\nResults saved to {path}")
    elif path.suffix.lower() == ".csv":
        rows = [_scale_result_to_dict(sr) for srs in all_results.values() for sr in srs]
        if not rows:
            print("No results to save.")
            return
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResults saved to {path}")
    else:
        print(f"Unsupported output format: {path.suffix}. Use .csv or .json")


def _scale_result_to_dict(sr: ScaleResult) -> dict[str, Any]:
    """Convert a ScaleResult to a dictionary."""
    return {
        "scale": sr.scale,
        "mode": sr.mode,
        "p50_ms": round(sr.p50_ms, 4),
        "p95_ms": round(sr.p95_ms, 4),
        "p99_ms": round(sr.p99_ms, 4),
        "recall": round(sr.recall, 4),
        "precision": round(sr.precision, 4),
        "mrr": round(sr.mrr, 4),
        "ndcg": round(sr.ndcg, 4),
    }


if __name__ == "__main__":
    raise SystemExit(main())
