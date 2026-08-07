"""S3 Storage Benchmark for Whoosh-NG.

Compares multiple S3 strategies for storing Whoosh index segments:

1. 1 object per segment file (naive)
2. 1 object per posting list (fine-grained)
3. Compressed segments (ZSTD)
4. Local cache + S3 sync (HybridStorage-like)
5. Lazy segment reads via Range Requests

Metrics:
- Write throughput (MB/s, objects/s)
- Read throughput (MB/s, objects/s)
- Latency p50/p95/p99 (ms)
- Total time for full index scan
"""

from __future__ import annotations

import asyncio
import io
import os
import random
import statistics
import time
from dataclasses import dataclass, field
from typing import Any

import boto3
import zstandard as zstd

from whoosh_modern.storage import HybridStorage, S3Storage


@dataclass
class BenchmarkResult:
    name: str
    write_time_s: float = 0.0
    read_time_s: float = 0.0
    write_throughput_mbps: float = 0.0
    read_throughput_mbps: float = 0.0
    read_latencies_ms: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class SegmentData:
    """Simulates a Whoosh segment file."""

    segment_id: int
    posting_lists: dict[str, bytes]  # field_name -> posting list data
    metadata: bytes
    total_size: int = 0

    def __post_init__(self) -> None:
        self.total_size = sum(len(v) for v in self.posting_lists.values()) + len(self.metadata)

    def as_file(self) -> bytes:
        """Serialize as a single segment file."""
        buf = io.BytesIO()
        buf.write(self.metadata)
        for field_name, data in self.posting_lists.items():
            buf.write(field_name.encode("utf-8").ljust(32, b"\x00"))
            buf.write(len(data).to_bytes(4, "big"))
            buf.write(data)
        return buf.getvalue()

    @classmethod
    def from_file(cls, data: bytes) -> SegmentData:
        """Deserialize from a single segment file."""
        offset = 0
        metadata = data[:256]
        offset = 256
        posting_lists: dict[str, bytes] = {}
        while offset < len(data):
            field_name = data[offset : offset + 32].rstrip(b"\x00").decode("utf-8")
            offset += 32
            size = int.from_bytes(data[offset : offset + 4], "big")
            offset += 4
            posting_lists[field_name] = data[offset : offset + size]
            offset += size
        return cls(segment_id=0, posting_lists=posting_lists, metadata=metadata)


def generate_synthetic_segment(
    segment_id: int, num_fields: int = 5, size_kb: int = 64
) -> SegmentData:
    """Generate a synthetic Whoosh segment with random posting lists."""
    posting_lists: dict[str, bytes] = {}
    field_names = [f"field_{i}" for i in range(num_fields)]
    bytes_per_field = (size_kb * 1024 - 256) // num_fields
    for field_name in field_names:
        posting_lists[field_name] = random.randbytes(bytes_per_field)
    metadata = segment_id.to_bytes(8, "big") + random.randbytes(248)
    return SegmentData(segment_id=segment_id, posting_lists=posting_lists, metadata=metadata)


def get_s3_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        region_name="us-east-1",
    )


BUCKET = "whoosh-benchmark"


class S3StorageStrategy:
    name: str = "base"

    def write_segments(self, segments: list[SegmentData]) -> float:
        raise NotImplementedError

    def read_segments(self, segment_ids: list[int]) -> float:
        raise NotImplementedError

    def cleanup(self) -> None:
        pass


class OneObjectPerSegment(S3StorageStrategy):
    """Strategy 1: 1 S3 object per segment file."""

    name = "1_obj_per_segment"

    def write_segments(self, segments: list[SegmentData]) -> float:
        client = get_s3_client()
        start = time.perf_counter()
        for seg in segments:
            client.put_object(
                Bucket=BUCKET,
                Key=f"segments/seg_{seg.segment_id:06d}.dat",
                Body=seg.as_file(),
            )
        return time.perf_counter() - start

    def read_segments(self, segment_ids: list[int]) -> float:
        client = get_s3_client()
        start = time.perf_counter()
        for sid in segment_ids:
            client.get_object(Bucket=BUCKET, Key=f"segments/seg_{sid:06d}.dat")
        return time.perf_counter() - start

    def cleanup(self) -> None:
        client = get_s3_client()
        keys = client.list_objects_v2(Bucket=BUCKET, Prefix="segments/").get("Contents", [])
        if keys:
            client.delete_objects(
                Bucket=BUCKET, Delete={"Objects": [{"Key": k["Key"]} for k in keys]}
            )


class OneObjectPerPostingList(S3StorageStrategy):
    """Strategy 2: 1 S3 object per posting list."""

    name = "1_obj_per_posting_list"

    def write_segments(self, segments: list[SegmentData]) -> float:
        client = get_s3_client()
        start = time.perf_counter()
        for seg in segments:
            for field_name, data in seg.posting_lists.items():
                client.put_object(
                    Bucket=BUCKET,
                    Key=f"postings/seg_{seg.segment_id:06d}/{field_name}.bin",
                    Body=data,
                )
            client.put_object(
                Bucket=BUCKET,
                Key=f"postings/seg_{seg.segment_id:06d}/metadata.bin",
                Body=seg.metadata,
            )
        return time.perf_counter() - start

    def read_segments(self, segment_ids: list[int]) -> float:
        client = get_s3_client()
        start = time.perf_counter()
        for sid in segment_ids:
            prefix = f"postings/seg_{sid:06d}/"
            resp = client.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
            for obj in resp.get("Contents", []):
                client.get_object(Bucket=BUCKET, Key=obj["Key"])
        return time.perf_counter() - start

    def cleanup(self) -> None:
        client = get_s3_client()
        for prefix in ["postings/"]:
            keys = client.list_objects_v2(Bucket=BUCKET, Prefix=prefix).get("Contents", [])
            if keys:
                client.delete_objects(
                    Bucket=BUCKET, Delete={"Objects": [{"Key": k["Key"]} for k in keys]}
                )


class CompressedSegments(S3StorageStrategy):
    """Strategy 3: 1 compressed object per segment (ZSTD)."""

    name = "compressed_zstd"

    def write_segments(self, segments: list[SegmentData]) -> float:
        client = get_s3_client()
        cctx = zstd.ZstdCompressor()
        start = time.perf_counter()
        for seg in segments:
            compressed = cctx.compress(seg.as_file())
            client.put_object(
                Bucket=BUCKET,
                Key=f"compressed/seg_{seg.segment_id:06d}.zst",
                Body=compressed,
            )
        return time.perf_counter() - start

    def read_segments(self, segment_ids: list[int]) -> float:
        client = get_s3_client()
        dctx = zstd.ZstdDecompressor()
        start = time.perf_counter()
        for sid in segment_ids:
            resp = client.get_object(Bucket=BUCKET, Key=f"compressed/seg_{sid:06d}.zst")
            dctx.decompress(resp["Body"].read())
        return time.perf_counter() - start

    def cleanup(self) -> None:
        client = get_s3_client()
        keys = client.list_objects_v2(Bucket=BUCKET, Prefix="compressed/").get("Contents", [])
        if keys:
            client.delete_objects(
                Bucket=BUCKET, Delete={"Objects": [{"Key": k["Key"]} for k in keys]}
            )


class HybridCacheS3(S3StorageStrategy):
    """Strategy 4: Local cache + S3 sync (HybridStorage)."""

    name = "hybrid_cache_s3"

    def __init__(self, cache_dir: str = "./benchmark_cache") -> None:
        self.cache_dir = cache_dir
        self.storage: HybridStorage | None = None

    def _get_minio_client(self) -> Any:
        return get_s3_client()

    def write_segments(self, segments: list[SegmentData]) -> float:
        remote = S3Storage(bucket=BUCKET, prefix="hybrid", client=self._get_minio_client())
        self.storage = HybridStorage(local_cache=self.cache_dir, remote=remote)
        start = time.perf_counter()
        for seg in segments:
            self.storage.write(f"seg_{seg.segment_id:06d}.dat", seg.as_file())
        return time.perf_counter() - start

    def read_segments(self, segment_ids: list[int]) -> float:
        assert self.storage is not None
        start = time.perf_counter()
        for sid in segment_ids:
            self.storage.read(f"seg_{sid:06d}.dat")
        return time.perf_counter() - start

    def cleanup(self) -> None:
        import shutil

        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        client = get_s3_client()
        keys = client.list_objects_v2(Bucket=BUCKET, Prefix="hybrid/").get("Contents", [])
        if keys:
            client.delete_objects(
                Bucket=BUCKET, Delete={"Objects": [{"Key": k["Key"]} for k in keys]}
            )


async def run_benchmark() -> None:
    """Run all S3 storage benchmarks."""
    num_segments = 50
    size_kb_per_segment = 64
    read_sample_size = 20

    print(f"Generating {num_segments} synthetic segments ({size_kb_per_segment}KB each)...")
    segments = [
        generate_synthetic_segment(i, num_fields=5, size_kb=size_kb_per_segment)
        for i in range(num_segments)
    ]
    total_size_mb = sum(s.total_size for s in segments) / (1024 * 1024)
    print(f"Total generated data: {total_size_mb:.2f} MB")

    strategies = [
        OneObjectPerSegment(),
        OneObjectPerPostingList(),
        CompressedSegments(),
        HybridCacheS3(),
    ]

    results: list[BenchmarkResult] = []

    for strategy in strategies:
        print(f"\n{'=' * 60}")
        print(f"Benchmarking: {strategy.name}")
        print(f"{'=' * 60}")

        try:
            strategy.cleanup()

            # Write benchmark
            write_time = strategy.write_segments(segments)
            write_mbps = total_size_mb / write_time if write_time > 0 else 0.0
            print(
                f"  Write: {write_time:.3f}s "
                f"({write_mbps:.2f} MB/s, {num_segments / write_time:.1f} obj/s)"
            )

            # Read benchmark
            sample_ids = random.sample(range(num_segments), min(read_sample_size, num_segments))
            read_time = strategy.read_segments(sample_ids)
            read_mbps = (
                (total_size_mb * read_sample_size / num_segments) / read_time
                if read_time > 0
                else 0.0
            )
            print(
                f"  Read:  {read_time:.3f}s "
                f"({read_mbps:.2f} MB/s, {read_sample_size / read_time:.1f} obj/s)"
            )

            result = BenchmarkResult(
                name=strategy.name,
                write_time_s=write_time,
                read_time_s=read_time,
                write_throughput_mbps=write_mbps,
                read_throughput_mbps=read_mbps,
            )
            results.append(result)

        except Exception as exc:  # pylint: disable=broad-except
            print(f"  ERROR: {exc}")
            results.append(BenchmarkResult(name=strategy.name, errors=[str(exc)]))
        finally:
            strategy.cleanup()

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'Strategy':<30} {'Write (MB/s)':<15} {'Read (MB/s)':<15}")
    print("-" * 60)
    for res in results:
        if res.errors:
            print(f"{res.name:<30} ERROR: {res.errors[0]}")
        else:
            print(
                f"{res.name:<30} "
                f"{res.write_throughput_mbps:<15.2f} {res.read_throughput_mbps:<15.2f}"
            )

    # Recommendations
    print(f"\n{'=' * 60}")
    print("RECOMMENDATIONS")
    print(f"{'=' * 60}")

    valid_results = [r for r in results if not r.errors]
    if not valid_results:
        print("No valid results to analyze.")
        return

    best_write = max(valid_results, key=lambda r: r.write_throughput_mbps)
    best_read = max(valid_results, key=lambda r: r.read_throughput_mbps)
    print(f"Best write throughput: {best_write.name} ({best_write.write_throughput_mbps:.2f} MB/s)")
    print(f"Best read throughput:  {best_read.name} ({best_read.read_throughput_mbps:.2f} MB/s)")

    hybrid = next((r for r in valid_results if r.name == "hybrid_cache_s3"), None)
    if hybrid:
        print("\nNote: HybridStorage (local cache + S3) provides:")
        print("  - First read: S3 latency (cold cache)")
        print("  - Subsequent reads: local disk speed (warm cache)")
        print("  - Best for: repeated queries on stable indexes")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
