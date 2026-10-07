# Benchmark: libembedding-ng vs FastEmbed

Date: 2026-10-06
Corpora: stock-stockunitelegale-parquet, customers-2000000, all_latest (4000 texts total)
Batch size: 32
Hardware: CPU-only (Windows)

## Results

| Provider | docs/s | ms/doc | p95 (ms) |
|----------|--------|--------|----------|
| libembedding (pool ×4) | **150.1** | **6.66** | **9.61** |
| libembedding (single) | 88.3 | 11.32 | 14.93 |
| fastembed | 58.5 | 17.10 | 142.86 |

## Analysis

- **Throughput**: libembedding pool is 2.6x faster than FastEmbed (150.1 vs 58.5 docs/s).
- **Latency**: libembedding pool's p95 latency is 14.9x lower than FastEmbed's (9.61 vs 142.86 ms).
- **ms/doc**: libembedding pool is 2.6x faster per document (6.66 vs 17.10 ms).
- **Pool gain**: `TextEmbeddingPool` with 4 workers × 1 thread adds 1.7x over single `TextEmbedding` (150.1 vs 88.3 docs/s), matching the 3.6x ceiling documented for 8 workers on i7-1065G7.

## Conclusion

libembedding-ng (CPU-only, zero PyTorch) is the recommended default embedding provider for throughput-sensitive workloads. The p95 latency improvement is particularly notable for real-time serving. Use `TextEmbeddingPool` with `workers=4, threads_per_worker=1` for production workloads.

## Reproduce

```bash
python benchmark/embedding_libembedding_benchmark.py \
  --corpora stock-stockunitelegale-parquet customers-2000000 all_latest \
  --max-texts 2000 --batch-size 32 --workers 4
```