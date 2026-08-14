"""Registry of pre-configured ONNX embedding models.

Provides ``EmbeddingModelRegistry`` to centralize model metadata
(dimensions, pooling, normalization, quantization) and ``ModelInfo``
dataclass for per-model configuration.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Metadata for a pre-configured embedding model.

    Attributes:
        name: Unique model identifier (e.g. ``"bge-small-en-v1.5"``).
        model_id: HuggingFace model ID or local path fragment.
        dimension: Output embedding dimension.
        pooling: Pooling strategy (``"mean"``, ``"cls"``, or ``"max"``).
        normalize: Whether embeddings are L2-normalized by default.
        quantization: Optional quantization variant (``"fp32"``, ``"fp16"``,
            ``"int8"``, or ``None`` for full precision).
        description: Human-readable description of the model.
        subfolder: Optional subfolder within the repo where model files
            are stored (e.g. ``"onnx"``).
    """

    name: str
    model_id: str
    dimension: int
    pooling: str = "mean"
    normalize: bool = True
    quantization: str | None = None
    description: str = ""
    subfolder: str | None = None


class EmbeddingModelRegistry:
    """Registry of pre-configured embedding models.

    Provides ``register()`` and ``resolve()`` to manage and retrieve
    ``ModelInfo`` instances by model name.

    Args:
        models: Optional initial list of ``ModelInfo`` instances.
    """

    def __init__(self, models: list[ModelInfo] | None = None) -> None:
        """Initialize the registry.

        Args:
            models: Optional initial list of ``ModelInfo`` instances.
        """
        self._models: dict[str, ModelInfo] = {}
        if models:
            for model in models:
                self.register(model)

    def register(self, model: ModelInfo) -> None:
        """Register a model configuration.

        Args:
            model: The ``ModelInfo`` to register.

        Raises:
            KeyError: If a model with the same name is already registered.
        """
        if model.name in self._models:
            raise KeyError(f"Model '{model.name}' is already registered")
        self._models[model.name] = model

    def resolve(self, name: str) -> ModelInfo | None:
        """Return the ``ModelInfo`` for the given model name.

        Args:
            name: Model identifier.

        Returns:
            The matching ``ModelInfo``, or ``None`` if not found.
        """
        return self._models.get(name)

    def list_models(self) -> list[str]:
        """Return the list of registered model names.

        Returns:
            A list of model name strings.
        """
        return list(self._models.keys())

    def get_quantized(self, name: str, quantization: str) -> ModelInfo | None:
        """Return a quantized variant of the given model if available.

        Looks for a model whose name encodes the requested quantization
        (e.g. ``"bge-small-en-v1.5-int8"``) or whose ``quantization``
        field matches.

        Args:
            name: Base model name.
            quantization: Quantization variant (``"fp32"``, ``"fp16"``,
                ``"int8"``).

        Returns:
            The matching quantized ``ModelInfo``, or ``None``.
        """
        candidate = self._models.get(f"{name}-{quantization}")
        if candidate is not None:
            return candidate
        for model in self._models.values():
            if model.name == name and model.quantization == quantization:
                return model
        return None


def get_default_registry() -> EmbeddingModelRegistry:
    """Return a registry pre-populated with common ONNX embedding models.

    Includes:
        - ``bge-small-en-v1.5`` (384 dims, mean pooling, normalized)
        - ``multilingual-e5-small`` (384 dims, mean pooling, normalized)
        - ``mini-lm-en-ONNX`` (384 dims, cls pooling, normalized)

    Returns:
        A populated ``EmbeddingModelRegistry`` instance.
    """
    registry = EmbeddingModelRegistry()
    registry.register(
        ModelInfo(
            name="bge-small-en-v1.5",
            model_id="onnx-community/bge-small-en-v1.5-ONNX",
            dimension=384,
            pooling="mean",
            normalize=True,
            description="English BGE-small optimized for ONNX Runtime",
            subfolder="onnx",
        )
    )
    registry.register(
        ModelInfo(
            name="multilingual-e5-small",
            model_id="intfloat/multilingual-e5-small",
            dimension=384,
            pooling="mean",
            normalize=True,
            description="Multilingual E5-small ONNX from intfloat",
            subfolder="onnx",
        )
    )
    registry.register(
        ModelInfo(
            name="mini-lm-en-ONNX",
            model_id="onnx-community/mini-lm-en-ONNX",
            dimension=384,
            pooling="cls",
            normalize=True,
            description="MiniLM English optimized for ONNX Runtime",
        )
    )
    registry.register(
        ModelInfo(
            name="bge-small-en-v1.5-int8",
            model_id="onnx-community/bge-small-en-v1.5-ONNX",
            dimension=384,
            pooling="mean",
            normalize=True,
            quantization="int8",
            description="BGE-small INT8 quantized for ONNX Runtime",
            subfolder="onnx",
        )
    )
    return registry


__all__ = [
    "ModelInfo",
    "EmbeddingModelRegistry",
    "get_default_registry",
]
