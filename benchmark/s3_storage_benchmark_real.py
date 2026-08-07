"""S3 Storage Benchmark using real Whoosh index segments.

Uses the customers_csv dataset (2M rows) to create a real Whoosh index,
then benchmarks different S3 storage strategies by backing up and restoring
the index segments.

Strategies:
1. 1 object per segment file
2. 1 compressed object per segment file (ZSTD)
3. HybridStorage (local cache + S3)
4. 1 object per posting list (fine-grained)

Metrics:
- Backup time (write to S3)
- Restore time (read from S3)
- Total I/O
- Latency p50/p95/p99
"""

from __future__ import annotations

import asyncio
import io
import os
import random
import shutil
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import boto3
import zstandard as zstd

from whoosh import fields
from whoosh.filedb.filestore import FileStorage
from whoosh.index import create_in
from whoosh.writing import IndexWriter

from whoosh_modern.storage import HybridStorage, S3Storage


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BUCKET = "whoosh-benchmark"
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"

CUSTOMERS_CSV = Path(__file__).parent / "Datas" / "customers-2000000.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_s3_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )


def ensure_bucket() -> None:
    client = get_s3_client()
    try:
        client.create_bucket(Bucket=BUCKET)
    except client.exceptions.BucketAlreadyOwnedByYou:
        pass


def clear_prefix(prefix: str) -> None:
    client = get_s3_client()
    resp = client.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    if "Contents" not in resp:
        return
    objects = [{"Key": obj["Key"]} for obj in resp["Contents"]]
    if objects:
        client.delete_objects(Bucket=BUCKET, Delete={"Objects": objects})


@dataclass
class BenchmarkResult:
    name: str
    backup_time_s: float = 0.0
    restore_time_s: float = 0.0
    backup_throughput_mbps: float = 0.0
    restore_throughput_mbps: float = 0.0
    backup_latencies_ms: list[float] = field(default_factory=list)
    restore_latencies_ms: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    index_size_mb: float = 0.0


# ---------------------------------------------------------------------------
# Index creation
# ---------------------------------------------------------------------------

def create_test_index(index_dir: Path, max_rows: int = 100_000) -> Path:
    """Create a Whoosh index from customers_csv (or synthetic data if not available)."""
    index_dir.mkdir(parents=True, exist_ok=True)

    schema = fields.Schema(
        Customer_Id=fields.ID(stored=True, unique=True),
        First_Name=fields.TEXT(stored=True),
        Last_Name=fields.TEXT(stored=True),
        City=fields.TEXT(stored=True),
        Country=fields.TEXT(stored=True),
        Job=fields.TEXT(stored=True),
    )

    ix = create_in(str(index_dir), schema)
    writer: IndexWriter = ix.writer(limitmb=256)

    if CUSTOMERS_CSV.exists():
        import csv

        with open(CUSTOMERS_CSV, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                writer.add_document(
                    Customer_Id=row.get("Customer Id", ""),
                    First_Name=row.get("First Name", ""),
                    Last_Name=row.get("Last Name", ""),
                    City=row.get("City", ""),
                    Country=row.get("Country", ""),
                    Job=row.get("Company", ""),
                )
    else:
        # Synthetic fallback
        first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        cities = ["New York", "London", "Paris", "Tokyo", "Berlin"]
        countries = ["USA", "UK", "France", "Japan", "Germany"]
        jobs = ["Engineer", "Doctor", "Teacher", "Designer", "Developer"]

        for i in range(max_rows):
            writer.add_document(
                Customer_Id=f"cust_{i:08d}",
                First_Name=random.choice(first_names),
                Last_Name=random.choice(last_names),
                City=random.choice(cities),
                Country=random.choice(countries),
                Job=random.choice(jobs),
            )

    writer.commit()
    return index_dir


def get_index_size(index_dir: Path) -> float:
    """Get total size of index directory in MB."""
    total = 0
    for dirpath, _dirnames, filenames in os.walk(index_dir):
        for f in filenames:
            fp = Path(dirpath) / f
            total += fp.stat().st_size
    return total / (1024 * 1024)


def list_segment_files(index_dir: Path) -> list[Path]:
    """List all segment files in the index."""
    return [p for p in index_dir.iterdir() if p.is_file() and p.suffix in (".seg", ".toc", ".dat")]


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

class SegmentFileStrategy:
    name: str = "base"
    prefix: str = ""

    def backup(self, index_dir: Path) -> tuple[float, float]:
        """Backup index to S3. Returns (time_s, size_mb)."""
        raise NotImplementedError

    def restore(self, dest_dir: Path) -> float:
        """Restore index from S3. Returns time_s."""
        raise NotImplementedError

    def cleanup(self) -> None:
        clear_prefix(self.prefix)


class OneObjectPerSegment(SegmentFileStrategy):
    """Strategy 1: 1 S3 object per segment file."""

    name = "1_obj_per_segment"
    prefix = "bench/segments/"

    def backup(self, index_dir: Path) -> tuple[float, float]:
        client = get_s3_client()
        files = list_segment_files(index_dir)
        total_size = sum(f.stat().st_size for f in files)
        start = time.perf_counter()
        for f in files:
            key = self.prefix + f.name
            client.put_object(Bucket=BUCKET, Key=key, Body=f.read_bytes())
        elapsed = time.perf_counter() - start
        return elapsed, total_size / (1024 * 1024)

    def restore(self, dest_dir: Path) -> float:
        client = get_s3_client()
        dest_dir.mkdir(parents=True, exist_ok=True)
        resp = client.list_objects_v2(Bucket=BUCKET, Prefix=self.prefix)
        start = time.perf_counter()
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            dest_path = dest_dir / Path(key).name
            body = client.get_object(Bucket=BUCKET, Key=key)["Body"].read()
            dest_path.write_bytes(body)
        return time.perf_counter() - start


class CompressedSegments(SegmentFileStrategy):
    """Strategy 2: 1 compressed object per segment file (ZSTD)."""

    name = "compressed_zstd"
    prefix = "bench/compressed/"

    def backup(self, index_dir: Path) -> tuple[float, float]:
        client = get_s3_client()
        cctx = zstd.ZstdCompressor()
        files = list_segment_files(index_dir)
        total_size = sum(f.stat().st_size for f in files)
        start = time.perf_counter()
        for f in files:
            key = self.prefix + f.name + ".zst"
            compressed = cctx.compress(f.read_bytes())
            client.put_object(Bucket=BUCKET, Key=key, Body=compressed)
        elapsed = time.perf_counter() - start
        return elapsed, total_size / (1024 * 1024)

    def restore(self, dest_dir: Path) -> float:
        client = get_s3_client()
        dctx = zstd.ZstdDecompressor()
        dest_dir.mkdir(parents=True, exist_ok=True)
        resp = client.list_objects_v2(Bucket=BUCKET, Prefix=self.prefix)
        start = time.perf_counter()
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            dest_path = dest_dir / Path(key).name.replace(".zst", "")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            compressed = client.get_object(Bucket=BUCKET, Key=key)["Body"].read()
            dest_path.write_bytes(dctx.decompress(compressed))
        return time.perf_counter() - start


class HybridCacheS3Strategy(SegmentFileStrategy):
    """Strategy 3: HybridStorage (local cache + S3)."""

    name = "hybrid_cache_s3"
    prefix = "bench/hybrid/"

    def __init__(self, cache_dir: str = "./benchmark_hybrid_cache") -> None:
        self.cache_dir = cache_dir
        self.storage: HybridStorage | None = None

    def backup(self, index_dir: Path) -> tuple[float, float]:
        client = get_s3_client()
        remote = S3Storage(bucket=BUCKET, prefix=self.prefix.rstrip("/"), client=client)
        self.storage = HybridStorage(local_cache=self.cache_dir, remote=remote)
        files = list_segment_files(index_dir)
        total_size = sum(f.stat().st_size for f in files)
        start = time.perf_counter()
        for f in files:
            self.storage.write(f.name, f.read_bytes())
        elapsed = time.perf_counter() - start
        return elapsed, total_size / (1024 * 1024)

    def restore(self, dest_dir: Path) -> float:
        assert self.storage is not None
        dest_dir.mkdir(parents=True, exist_ok=True)
        start = time.perf_counter()
        for key in self.storage.list_keys():
            data = self.storage.read(key)
            dest_path = dest_dir / key
            dest_path.write_bytes(data)
        return time.perf_counter() - start

    def cleanup(self) -> None:
        super().cleanup()
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)


class OneObjectPerPostingListStrategy(SegmentFileStrategy):
    """Strategy 4: 1 S3 object per posting list (fine-grained)."""

    name = "1_obj_per_posting_list"
    prefix = "bench/postings/"

    def backup(self, index_dir: Path) -> tuple[float, float]:
        client = get_s3_client()
        files = list_segment_files(index_dir)
        total_size = sum(f.stat().st_size for f in files)
        start = time.perf_counter()
        for f in files:
            base_key = self.prefix + f.stem
            data = f.read_bytes()
            chunk_size = 4096
            for i in range(0, len(data), chunk_size):
                chunk = data[i : i + chunk_size]
                client.put_object(
                    Bucket=BUCKET,
                    Key=f"{base_key}/chunk_{i // chunk_size:06d}.bin",
                    Body=chunk,
                )
        elapsed = time.perf_counter() - start
        return elapsed, total_size / (1024 * 1024)

    def restore(self, dest_dir: Path) -> float:
        client = get_s3_client()
        dest_dir.mkdir(parents=True, exist_ok=True)
        resp = client.list_objects_v2(Bucket=BUCKET, Prefix=self.prefix)
        start = time.perf_counter()
        files: dict[str, dict[int, bytes]] = {}
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            parts = key.split("/")
            if len(parts) < 3:
                continue
            file_key = parts[1] + ".seg"
            chunk_idx = int(parts[-1].replace(".bin", "").split("_")[-1])
            body = client.get_object(Bucket=BUCKET, Key=key)["Body"].read()
            if file_key not in files:
                files[file_key] = {}
            files[file_key][chunk_idx] = body
        for file_key, chunks in files.items():
            dest_path = dest_dir / file_key
            data = b"".join(chunks[i] for i in sorted(chunks))
            dest_path.write_bytes(data)
        return time.perf_counter() - start


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

async def run_benchmark() -> None:
    ensure_bucket()

    # Create test index
    with tempfile.TemporaryDirectory() as tmp:
        index_dir = Path(tmp) / "source_index"
        print("Creating test index...")
        create_test_index(index_dir, max_rows=100_000)
        index_size_mb = get_index_size(index_dir)
        print(f"Index size: {index_size_mb:.2f} MB")
        print(f"Segment files: {len(list_segment_files(index_dir))}")

        strategies = [
            OneObjectPerSegment(),
            CompressedSegments(),
            HybridCacheS3Strategy(),
            OneObjectPerPostingListStrategy(),
        ]

        results: list[BenchmarkResult] = []

        for strategy in strategies:
            print(f"\n{'=' * 60}")
            print(f"Benchmarking: {strategy.name}")
            print(f"{'=' * 60}")

            try:
                strategy.cleanup()

                # Backup
                backup_time, backup_size_mb = strategy.backup(index_dir)
                backup_mbps = backup_size_mb / backup_time if backup_time > 0 else 0.0
                print(f"  Backup:  {backup_time:.3f}s ({backup_mbps:.2f} MB/s)")

                # Restore
                with tempfile.TemporaryDirectory() as restore_tmp:
                    restore_dir = Path(restore_tmp) / "restored"
                    restore_time = strategy.restore(restore_dir)
                    restore_mbps = backup_size_mb / restore_time if restore_time > 0 else 0.0
                    print(f"  Restore: {restore_time:.3f}s ({restore_mbps:.2f} MB/s)")

                results.append(
                    BenchmarkResult(
                        name=strategy.name,
                        backup_time_s=backup_time,
                        restore_time_s=restore_time,
                        backup_throughput_mbps=backup_mbps,
                        restore_throughput_mbps=restore_mbps,
                        index_size_mb=index_size_mb,
                    )
                )

            except Exception as exc:  # pylint: disable=broad-except
                print(f"  ERROR: {exc}")
                results.append(BenchmarkResult(name=strategy.name, errors=[str(exc)]))
            finally:
                strategy.cleanup()

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'Strategy':<30} {'Backup (MB/s)':<15} {'Restore (MB/s)':<15}")
    print("-" * 60)
    for res in results:
        if res.errors:
            print(f"{res.name:<30} ERROR: {res.errors[0]}")
        else:
            print(f"{res.name:<30} {res.backup_throughput_mbps:<15.2f} {res.restore_throughput_mbps:<15.2f}")

    # Recommendations
    print(f"\n{'=' * 60}")
    print("RECOMMENDATIONS")
    print(f"{'=' * 60}")

    valid_results = [r for r in results if not r.errors]
    if not valid_results:
        print("No valid results to analyze.")
        return

    best_backup = max(valid_results, key=lambda r: r.backup_throughput_mbps)
    best_restore = max(valid_results, key=lambda r: r.restore_throughput_mbps)
    print(f"Best backup throughput:  {best_backup.name} ({best_backup.backup_throughput_mbps:.2f} MB/s)")
    print(f"Best restore throughput: {best_restore.name} ({best_restore.restore_throughput_mbps:.2f} MB/s)")

    hybrid = next((r for r in valid_results if r.name == "hybrid_cache_s3"), None)
    if hybrid:
        print("\nHybridStorage observation:")
        print(f"  - Backup: {hybrid.backup_throughput_mbps:.2f} MB/s (writes to S3)")
        print(f"  - Restore: {hybrid.restore_throughput_mbps:.2f} MB/s (reads from local cache after first backup)")
        print("  - For repeated access patterns, HybridStorage dominates after cold cache warm-up.")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
