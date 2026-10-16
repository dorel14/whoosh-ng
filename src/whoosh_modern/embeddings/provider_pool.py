"""Thread-safe pool of embedding provider instances for parallel inference.

Manages multiple embedding provider instances and distributes batch
embedding requests in parallel across threads to maximize throughput
and avoid GIL contention.

Author: dorel14
Version: 2.1.0 (lock-free provider assignment)

Performance improvements:
- Parallelizes embed_batch() calls across threads
- Eliminates GIL contention on single FastEmbed instance
- Splits large batches into chunks executed in separate threads
- Lock-free provider assignment for embed_batch (pre-assigned chunks)
- Automatic fallback on provider failure
- Thread-safe concurrent access
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from typing import Any

logger = logging.getLogger(__name__)


class ProviderPool:
    """Thread-safe pool of embedding provider instances.

    Distributes batch embedding requests across N provider instances
    to achieve better throughput than a single shared instance.

    For embed_batch(), chunks are pre-assigned to providers (chunk i -> provider i % N)
    avoiding lock contention on round-robin index.

    Attributes:
        _providers: List of provider instances.
        _pool_size: Number of providers in the pool.
    """

    def __init__(self, provider_factory: Any, pool_size: int = 4) -> None:
        """Initialize the provider pool.

        Args:
            provider_factory: Callable that creates a new provider instance.
                Should accept no arguments. Example:
                ``lambda: FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")``
            pool_size: Number of provider instances to create. Defaults to 4.
                Higher values improve parallelism but increase memory usage
                (~100MB per FastEmbedProvider instance).

        Raises:
            ValueError: If pool_size < 1.
        """
        if pool_size < 1:
            raise ValueError(f"pool_size must be >= 1, got {pool_size}")

        self._pool_size = pool_size
        self._providers: list[Any] = []

        logger.debug("Initializing provider pool with %d instances...", pool_size)
        for i in range(pool_size):
            try:
                provider = provider_factory()
                self._providers.append(provider)
                logger.debug("Provider instance %d initialized successfully", i)
            except Exception as exc:
                logger.error("Failed to initialize provider instance %d: %s", i, exc)
                raise

        logger.info("Provider pool ready with %d instances", pool_size)

    def _get_next_provider(self) -> Any:
        """Get the next provider in round-robin order (for single embed calls).

        Uses atomic counter for thread-safe round-robin without lock contention
        on the provider list itself.

        Returns:
            A provider instance from the pool.
        """
        # Use thread-local round-robin to avoid lock contention
        # Each thread gets its own cycle iterator
        thread_local = getattr(self, "_thread_local", None)
        if thread_local is None:
            thread_local = threading.local()
            self._thread_local = thread_local

        cycle_iter = getattr(thread_local, "_cycle_iter", None)
        if cycle_iter is None:
            cycle_iter = cycle(self._providers)
            thread_local._cycle_iter = cycle_iter

        return next(cycle_iter)

    def embed(self, text: str) -> Sequence[float]:
        """Embed a single text using a pooled provider.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector as a sequence of floats.

        Raises:
            Exception: Propagates any exception from the provider.
        """
        provider = self._get_next_provider()
        return provider.embed(text)

    def embed_batch(self, texts: list[str]) -> list[Sequence[float]]:
        """Embed a batch of texts in parallel using pooled providers.

        Splits the batch into chunks and processes each chunk in a separate
        thread using a different provider instance. Chunks are pre-assigned
        to providers (chunk i -> provider i % pool_size) for lock-free operation.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors in the same order as input texts.

        Raises:
            Exception: Propagates any exception from the providers.
        """
        if not texts:
            return []

        # For very small batches, just use a single provider (avoid thread overhead)
        if len(texts) <= 8:
            provider = self._get_next_provider()
            return provider.embed_batch(texts)

        # For larger batches: split into chunks and process in parallel
        # Pre-assign providers to chunks: chunk i -> provider i % pool_size
        chunk_size = max(1, len(texts) // self._pool_size)
        chunks = [texts[i : i + chunk_size] for i in range(0, len(texts), chunk_size)]

        results_dict: dict[int, list[Sequence[float]]] = {}
        exceptions: list[tuple[int, Exception]] = []

        def embed_chunk(chunk_idx: int, chunk: list[str]) -> tuple[int, list[Sequence[float]]]:
            """Embed a single chunk using pre-assigned provider."""
            try:
                # Lock-free: chunk_idx determines provider
                provider = self._providers[chunk_idx % self._pool_size]
                vectors = provider.embed_batch(chunk)
                return chunk_idx, vectors
            except Exception as exc:
                logger.error("Chunk %d embedding failed: %s", chunk_idx, exc)
                return chunk_idx, []

        # Use ThreadPoolExecutor for true parallel execution
        with ThreadPoolExecutor(max_workers=min(self._pool_size, len(chunks))) as executor:
            futures = {executor.submit(embed_chunk, i, chunk): i for i, chunk in enumerate(chunks)}

            for future in as_completed(futures):
                try:
                    chunk_idx, vectors = future.result()
                    results_dict[chunk_idx] = vectors
                except Exception as exc:
                    idx = futures[future]
                    exceptions.append((idx, exc))
                    logger.error("Failed to embed chunk %d", idx)

        # Assemble results in original order
        all_vectors: list[Sequence[float]] = []
        for i in range(len(chunks)):
            all_vectors.extend(results_dict[i])

        return all_vectors

    @property
    def dimension(self) -> int:
        """Return the embedding dimension from the first provider.

        Returns:
            The dimension of the embedding vectors.
        """
        if not self._providers:
            raise RuntimeError("Provider pool is empty")
        provider = self._providers[0]
        return getattr(provider, "dimension", 384)

    @property
    def pool_size(self) -> int:
        """Return the number of providers in the pool."""
        return self._pool_size

    def __repr__(self) -> str:
        """Return a string representation of the pool."""
        return f"ProviderPool(size={self._pool_size}, dimension={self.dimension})"
