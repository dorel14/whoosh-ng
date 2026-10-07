"""FastEmbed-based embedding provider.

Author: dorel14
Version: 3.2.0

Optimizations:
- Configurable ONNX Runtime thread count via ``threads`` parameter.
- Predefined model presets.
- Automatic model selection via ``"fast"`` preset.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

FAST_MODEL_PRESETS: dict[str, str] = {
    "bge-small": "BAAI/bge-small-en-v1.5",
    "bge-base": "BAAI/bge-base-en-v1.5",
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "minilm-multilingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "e5-small": "Xenova/e5-small-v2",
    "e5-base": "Xenova/e5-base-v2",
    "multilingual": "BAAI/bge-m3",
    "nomic": "nomic-ai/nomic-embed-text-v1",
}

_FAST_CANDIDATES: list[dict[str, Any]] = [
    {
        "id": "BAAI/bge-small-en-v1.5",
        "size_gb": 0.067,
        "dim": 384,
        "priority": 1,
        "quality": "good",
        "speed_score": 10,
    },
    {
        "id": "snowflake/snowflake-arctic-embed-s",
        "size_gb": 0.13,
        "dim": 384,
        "priority": 2,
        "quality": "better",
        "speed_score": 9,
    },
    {
        "id": "BAAI/bge-small-en",
        "size_gb": 0.13,
        "dim": 384,
        "priority": 3,
        "quality": "good",
        "speed_score": 8,
    },
    {
        "id": "Xenova/e5-small-v2",
        "size_gb": 0.12,
        "dim": 384,
        "priority": 4,
        "quality": "good",
        "speed_score": 7,
    },
    {
        "id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "size_gb": 0.22,
        "dim": 384,
        "priority": 5,
        "quality": "good",
        "speed_score": 6,
    },
    {
        "id": "BAAI/bge-base-en-v1.5",
        "size_gb": 0.21,
        "dim": 768,
        "priority": 6,
        "quality": "better",
        "speed_score": 5,
    },
    {
        "id": "sentence-transformers/all-MiniLM-L6-v2",
        "size_gb": 0.08,
        "dim": 384,
        "priority": 7,
        "quality": "good",
        "speed_score": 4,
    },
]


def _get_supported_models() -> list[str]:
    """Return the list of model identifiers supported by the installed FastEmbed.

    Returns:
        A list of model identifier strings. Falls back to an empty list
        when FastEmbed is not installed or its API is unavailable.
    """
    try:
        from fastembed import TextEmbedding

        raw = TextEmbedding.list_supported_models()
        if isinstance(raw, list):
            return [item.get("model", "") if isinstance(item, dict) else str(item) for item in raw]
    except Exception as exc:
        logger.debug("Failed to list FastEmbed supported models: %s", exc)
    return []


def resolve_fast_model() -> str:
    """Pick the fastest available embedding model for FastEmbed.

    Selection criteria:
    1. Prefer 384-dim models (smaller vectors, faster inference).
    2. Prefer smaller model size.
    3. Prefer higher speed score based on observed CPU throughput.

    Returns:
        The identifier of the best available FastEmbed model. Falls back
        to ``"BAAI/bge-small-en-v1.5"`` when no preferred model is found
        or when FastEmbed is not installed.
    """
    supported = set(_get_supported_models())
    if not supported:
        return "BAAI/bge-small-en-v1.5"

    for candidate in sorted(_FAST_CANDIDATES, key=lambda c: c["priority"]):
        model_id = candidate["id"]
        if model_id in supported:
            logger.debug(
                "Fast preset resolved to %s (speed_score=%s)",
                model_id,
                candidate["speed_score"],
            )
            return model_id

    fallback = sorted(supported)[0] if supported else "BAAI/bge-small-en-v1.5"
    logger.debug("Fast preset fallback to %s", fallback)
    return fallback


class FastEmbedProvider:
    """Embedding provider backed by FastEmbed (CPU-only, zero PyTorch).

    Wraps ``fastembed.TextEmbedding`` behind the ``EmbeddingProvider`` protocol.
    Models are downloaded automatically on first use and cached by FastEmbed.

    Attributes:
        _model: The underlying FastEmbed ``TextEmbedding`` instance.
        _model_name: The FastEmbed model identifier.
        _dimension: Expected embedding dimension, inferred from the model.
        _threads: Configured thread count for ONNX Runtime.
    """

    def __init__(
        self,
        model_name: str = "fast",
        threads: int | None = None,
        parallel: int | None = None,
        batch_size: int | None = None,
        lazy_load: bool | None = None,
    ) -> None:
        """Initialize the FastEmbed provider.

        Args:
            model_name: FastEmbed model identifier or preset name
                (default: ``"BAAI/bge-small-en-v1.5"``). Preset names are
                resolved via :data:`FAST_MODEL_PRESETS`. Use ``"fast"``
                to automatically select the best available model based on
                speed and size heuristics.
            threads: Optional number of threads for ONNX Runtime. When
                provided, ``OMP_NUM_THREADS`` and ``ORT_NUM_THREADS`` are set
                before loading the model. ``None`` leaves the default.
            parallel: Optional worker count for FastEmbed's native parallel
                inference. ``None`` runs sequentially in the main process;
                ``0`` auto-detects the number of CPU cores; ``N >= 1`` uses
                exactly ``N`` workers. Native parallelism avoids GIL
                contention and CPU oversubscription far more effectively
                than spawning multiple provider instances.
            batch_size: Optional internal batch size for FastEmbed inference.
                ``None`` keeps FastEmbed's default (256 for text).
            lazy_load: Optional flag to defer model loading until the first
                inference call. Recommended (``True``) when ``parallel`` is
                enabled to avoid loading the model in the main process.

        Raises:
            ImportError: If ``fastembed`` is not installed.
            ValueError: If ``model_name`` is an unknown preset.
        """
        resolved = FAST_MODEL_PRESETS.get(model_name, model_name)
        if resolved == "fast":
            resolved = resolve_fast_model()
        self._model_name = resolved
        self._threads = threads
        self._parallel = parallel
        self._batch_size = batch_size
        self._lazy_load = lazy_load
        self._model = self._load_model(
            resolved, threads=threads, lazy_load=lazy_load
        )
        if hasattr(self._model, "dim"):
            self._dimension = int(self._model.dim)
        else:
            # lazy_load=True defers model loading, so .dim is unavailable
            # until the first inference. Probe once to resolve the dimension.
            probe = self._model.embed(["__whoosh_dim_probe__"])
            self._dimension = len(next(iter(probe)).tolist())

    @staticmethod
    def _load_model(
        model_name: str,
        threads: int | None = None,
        lazy_load: bool | None = None,
    ) -> Any:
        """Load a FastEmbed TextEmbedding model.

        Args:
            model_name: FastEmbed model identifier.
            threads: Optional number of ONNX Runtime threads. Forwarded to
                FastEmbed's ``TextEmbedding`` constructor (which overrides
                ``OMP_NUM_THREADS``/``ORT_NUM_THREADS``), so this is the
                reliable way to cap per-worker thread usage.
            lazy_load: Optional flag to defer model loading until the first
                inference call.

        Returns:
            A FastEmbed ``TextEmbedding`` instance.

        Raises:
            ImportError: If ``fastembed`` is not installed.
        """
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise ImportError(
                "FastEmbedProvider requires fastembed. "
                "Install with: pip install whoosh-ng[embeddings]"
            ) from exc
        kwargs: dict[str, Any] = {}
        if threads is not None:
            kwargs["threads"] = threads
        if lazy_load is not None:
            kwargs["lazy_load"] = lazy_load
        return TextEmbedding(model_name, **kwargs)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    @property
    def threads(self) -> int | None:
        """Return the configured thread count, or ``None`` if default."""
        return self._threads

    def embed(self, text: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        kwargs: dict[str, Any] = {}
        if self._parallel is not None:
            kwargs["parallel"] = self._parallel
        if self._batch_size is not None:
            kwargs["batch_size"] = self._batch_size
        result = self._model.embed([text], **kwargs)
        first = result[0] if isinstance(result, list) else next(iter(result))
        return [float(x) for x in first.tolist()]

    def embed_batch(self, texts: list[str]) -> list[Sequence[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            A list of embedding vectors.
        """
        if not texts:
            return []
        kwargs: dict[str, Any] = {}
        if self._parallel is not None:
            kwargs["parallel"] = self._parallel
        if self._batch_size is not None:
            kwargs["batch_size"] = self._batch_size
        return [vec.tolist() for vec in self._model.embed(texts, **kwargs)]

    def __repr__(self) -> str:
        return (
            f"FastEmbedProvider(model_name={self._model_name!r}, "
            f"dimension={self._dimension}, threads={self._threads})"
        )
