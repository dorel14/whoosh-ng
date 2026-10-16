"""Async model preloading for embedding providers.

Provides utilities for loading embedding models asynchronously at application
startup to avoid blocking the main thread during the first indexing/search
operation.

Author: dorel14
Version: 1.0.0

Features:
- Async model warmup with progress logging
- Multiple model concurrent loading
- Fallback to sync loading if async unavailable
- Integration with FastEmbedProvider, SentenceTransformersProvider, ONNXEmbeddingProvider
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


async def preload_embedding_model_async(
    model_name: str,
    provider_type: str = "fastembed",
) -> bool:
    """Preload an embedding model asynchronously.

    Args:
        model_name: Model identifier (e.g., "BAAI/bge-small-en-v1.5").
        provider_type: Provider type ("fastembed", "sentence-transformers",
            "onnx", "libembedding").

    Returns:
        True if preload succeeded, False otherwise.
    """
    loop = asyncio.get_event_loop()

    def load_sync() -> bool:
        try:
            if provider_type == "fastembed":
                from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

                provider = FastEmbedProvider(model_name=model_name)
                logger.info(
                    "Preloaded FastEmbed model: %s (dim=%d)",
                    model_name,
                    provider.dimension,
                )
                return True
            elif provider_type == "sentence-transformers":
                from whoosh_modern.embeddings.sentence_transformers_provider import (
                    SentenceTransformersProvider,
                )

                provider = SentenceTransformersProvider(model_name=model_name)
                logger.info("Preloaded SentenceTransformers model: %s", model_name)
                return True
            elif provider_type == "libembedding":
                from whoosh_modern.embeddings.libembedding_provider import LibEmbeddingProvider

                provider = LibEmbeddingProvider(model_name=model_name)
                logger.info(
                    "Preloaded LibEmbedding model: %s (dim=%d)",
                    model_name,
                    provider.dimension,
                )
                return True
            else:
                logger.warning(
                    "ONNX model preloading requires model_path parameter. Skipping: %s",
                    model_name,
                )
                return False
        except Exception as exc:
            logger.error("Failed to preload %s model %s: %s", provider_type, model_name, exc)
            return False

    return await loop.run_in_executor(None, load_sync)


async def preload_embedding_models_async(
    models: dict[str, str],
) -> dict[str, bool]:
    """Preload multiple embedding models concurrently.

    Args:
        models: Mapping of model_name -> provider_type.
               Example: {"BAAI/bge-small-en-v1.5": "fastembed",
                        "all-MiniLM-L6-v2": "sentence-transformers"}

    Returns:
        Mapping of model_name -> success bool.
    """
    tasks = [
        preload_embedding_model_async(model_name, provider_type)
        for model_name, provider_type in models.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        model_name: isinstance(result, bool) and result
        for model_name, result in zip(models.keys(), results, strict=False)
    }


def preload_embedding_model(
    model_name: str,
    provider_type: str = "fastembed",
) -> bool:
    """Preload an embedding model synchronously (blocking).

    Use this when async/await is not available or when you need to block
    until the model is loaded.

    Args:
        model_name: Model identifier.
        provider_type: Provider type ("fastembed", "sentence-transformers",
            "onnx", "libembedding").

    Returns:
        True if preload succeeded, False otherwise.
    """
    try:
        if provider_type == "fastembed":
            from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

            provider = FastEmbedProvider(model_name=model_name)
            logger.info(
                "Preloaded FastEmbed model: %s (dim=%d)",
                model_name,
                provider.dimension,
            )
            return True
        elif provider_type == "sentence-transformers":
            from whoosh_modern.embeddings.sentence_transformers_provider import (
                SentenceTransformersProvider,
            )

            provider = SentenceTransformersProvider(model_name=model_name)
            logger.info("Preloaded SentenceTransformers model: %s", model_name)
            return True
        elif provider_type == "libembedding":
            from whoosh_modern.embeddings.libembedding_provider import LibEmbeddingProvider

            provider = LibEmbeddingProvider(model_name=model_name)
            logger.info(
                "Preloaded LibEmbedding model: %s (dim=%d)",
                model_name,
                provider.dimension,
            )
            return True
        else:
            logger.warning(
                "ONNX model preloading requires model_path parameter. Skipping: %s",
                model_name,
            )
            return False
    except Exception as exc:
        logger.error("Failed to preload %s model %s: %s", provider_type, model_name, exc)
        return False


def preload_embedding_provider_pool(
    provider_factory: Callable[[], Any],
    pool_size: int = 4,
) -> bool:
    """Preload a provider pool by creating all instances.

    Args:
        provider_factory: Callable that creates provider instances.
        pool_size: Number of instances to create.

    Returns:
        True if all instances created successfully, False otherwise.
    """
    try:
        for i in range(pool_size):
            try:
                provider = provider_factory()
                logger.debug(
                    "Preloaded provider instance %d/%d (dim=%s)",
                    i + 1,
                    pool_size,
                    getattr(provider, "dimension", "unknown"),
                )
            except Exception as exc:
                logger.error("Failed to create provider instance %d: %s", i, exc)
                return False
        logger.info("Successfully preloaded provider pool with %d instances", pool_size)
        return True
    except Exception as exc:
        logger.error("Provider pool preloading failed: %s", exc)
        return False
