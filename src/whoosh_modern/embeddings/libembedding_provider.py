"""LibEmbedding-based embedding provider.

Author: dorel14
Version: 2.0.0

Wraps ``libembedding.TextEmbedding`` behind the ``EmbeddingProvider``
protocol. Models are downloaded automatically on first use and cached
by libembedding.

Presets:
- ``"fast"`` → ``TextEmbedding.from_mode("fast")``
- ``"balanced"`` → ``TextEmbedding.from_mode("balanced")``
- ``"quality"`` → ``TextEmbedding.from_mode("quality")``
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

LIBEMBEDDING_MODE_PRESETS = {"fast", "balanced", "quality"}


class LibEmbeddingProvider:
    """Embedding provider backed by libembedding (CPU-only, zero PyTorch).

    Wraps ``libembedding.TextEmbedding`` behind the ``EmbeddingProvider``
    protocol. Models are downloaded automatically on first use and cached
    by libembedding.

    Attributes:
        _model: The underlying libembedding ``TextEmbedding`` instance.
        _model_name: The libembedding model identifier or preset.
        _dimension: Expected embedding dimension, inferred from the model.
    """

    def __init__(
        self,
        model_name: str = "balanced",
        pooling: str = "mean",
        batch_size: int | None = None,
        cache_size: int | None = None,
        threads: int | None = None,
        quantization: str | None = None,
    ) -> None:
        """Initialize the libembedding provider.

        Args:
            model_name: libembedding model identifier or preset name
                (default: ``"balanced"``). Supported presets are
                ``"fast"``, ``"balanced"``, and ``"quality"``, resolved
                via ``TextEmbedding.from_mode()``.
            pooling: Pooling strategy forwarded to libembedding
                (``"mean"`` or ``"cls"``).
            batch_size: Optional inference batch size. ``None`` keeps
                libembedding's default.
            cache_size: Optional LRU cache size. ``None`` disables caching.
            threads: Optional number of threads for ONNX Runtime. When
                provided, ``OMP_NUM_THREADS`` and ``ORT_NUM_THREADS`` are
                set before loading the model. ``None`` leaves the default.
            quantization: Optional quantization mode forwarded to
                libembedding (``"none"``, ``"static"``, ``"dynamic"``,
                ``"fp16"``, ``"auto"``).

        Raises:
            ImportError: If ``libembedding`` is not installed.
            ValueError: If ``model_name`` is an unsupported preset.
        """
        resolved = model_name
        if model_name in LIBEMBEDDING_MODE_PRESETS:
            resolved = self._load_from_mode(model_name)
        self._model_name = resolved
        if threads is not None:
            os.environ["OMP_NUM_THREADS"] = str(threads)
            os.environ["ORT_NUM_THREADS"] = str(threads)
        kwargs: dict[str, Any] = {}
        if pooling:
            kwargs["pooling"] = pooling
        if batch_size is not None:
            kwargs["batch_size"] = batch_size
        if cache_size is not None:
            kwargs["cache_size"] = cache_size
        if quantization is not None:
            kwargs["quantization"] = quantization
        self._model = self._load_model(resolved, **kwargs)
        self._dimension = self._infer_dimension()

    @staticmethod
    def _load_from_mode(mode: str) -> str:
        """Resolve a preset mode to a model identifier via libembedding.

        Args:
            mode: One of ``"fast"``, ``"balanced"``, ``"quality"``.

        Returns:
            The resolved model identifier string.

        Raises:
            ImportError: If ``libembedding`` is not installed.
            ValueError: If ``mode`` is not a supported preset.
        """
        if mode not in LIBEMBEDDING_MODE_PRESETS:
            raise ValueError(
                f"Unsupported libembedding preset: {mode!r}. "
                f"Choose from {sorted(LIBEMBEDDING_MODE_PRESETS)}."
            )
        try:
            from libembedding import TextEmbedding
        except ImportError as exc:
            raise ImportError(
                "LibEmbeddingProvider requires libembedding. "
                "Install with: pip install whoosh-ng[libembedding]"
            ) from exc
        try:
            return TextEmbedding.from_mode(mode=mode).model_name
        except Exception as exc:
            raise RuntimeError(f"Failed to resolve libembedding preset {mode!r}: {exc}") from exc

    @staticmethod
    def _load_model(model_name: str, **kwargs: Any) -> Any:
        """Load a libembedding TextEmbedding model.

        Args:
            model_name: libembedding model identifier.
            **kwargs: Additional keyword arguments forwarded to
                ``TextEmbedding``.

        Returns:
            A libembedding ``TextEmbedding`` instance.

        Raises:
            ImportError: If ``libembedding`` is not installed.
        """
        try:
            from libembedding import TextEmbedding
        except ImportError as exc:
            raise ImportError(
                "LibEmbeddingProvider requires libembedding. "
                "Install with: pip install whoosh-ng[libembedding]"
            ) from exc
        return TextEmbedding(model_name=model_name, **kwargs)

    def _infer_dimension(self) -> int:
        """Infer the embedding dimension by probing the model with a short text.

        Returns:
            The embedding dimension inferred from the model output.
        """
        try:
            result = self._model.embed(["__whoosh_dim_probe__"])
            first = result[0] if isinstance(result, list) else next(iter(result))
            return len(first.tolist())
        except Exception as exc:
            logger.debug("Failed to infer dimension from libembedding model: %s", exc)
            raise RuntimeError(
                f"Could not infer embedding dimension for model {self._model_name!r}"
            ) from exc

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Return the resolved model name."""
        return self._model_name

    def embed(self, text: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        result = self._model.embed([text])
        first = result[0] if isinstance(result, list) else next(iter(result))
        return [float(x) for x in first.tolist()]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            A list of embedding vectors.
        """
        if not texts:
            return []
        result = self._model.embed(texts)
        return [[float(x) for x in vec.tolist()] for vec in result]

    def __repr__(self) -> str:
        return f"LibEmbeddingProvider(model_name={self._model_name!r}, dimension={self._dimension})"
