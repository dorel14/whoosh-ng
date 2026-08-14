"""Tests for the embedding model registry."""

from __future__ import annotations

import pytest

from whoosh_modern.embeddings.registry import (
    EmbeddingModelRegistry,
    ModelInfo,
    get_default_registry,
)


def test_model_info_creation() -> None:
    """Test that ModelInfo can be instantiated with all fields."""
    info = ModelInfo(
        name="test-model",
        model_id="org/test-model",
        dimension=256,
        pooling="cls",
        normalize=False,
        quantization="int8",
        description="Test model",
    )
    assert info.name == "test-model"
    assert info.dimension == 256
    assert info.pooling == "cls"
    assert info.normalize is False
    assert info.quantization == "int8"


def test_model_info_defaults() -> None:
    """Test ModelInfo default values."""
    info = ModelInfo(name="default-model", model_id="org/default", dimension=128)
    assert info.pooling == "mean"
    assert info.normalize is True
    assert info.quantization is None
    assert info.description == ""


def test_registry_register_and_resolve() -> None:
    """Test that a model can be registered and resolved."""
    registry = EmbeddingModelRegistry()
    info = ModelInfo(name="m1", model_id="org/m1", dimension=64)
    registry.register(info)
    resolved = registry.resolve("m1")
    assert resolved is not None
    assert resolved.name == "m1"
    assert resolved.dimension == 64


def test_registry_resolve_missing() -> None:
    """Test that resolving an unknown model returns None."""
    registry = EmbeddingModelRegistry()
    assert registry.resolve("unknown") is None


def test_registry_duplicate_raises() -> None:
    """Test that registering a duplicate model name raises KeyError."""
    registry = EmbeddingModelRegistry()
    registry.register(ModelInfo(name="dup", model_id="org/dup", dimension=32))
    with pytest.raises(KeyError, match="already registered"):
        registry.register(ModelInfo(name="dup", model_id="org/dup2", dimension=32))


def test_registry_list_models() -> None:
    """Test that list_models returns all registered model names."""
    registry = EmbeddingModelRegistry()
    registry.register(ModelInfo(name="a", model_id="org/a", dimension=32))
    registry.register(ModelInfo(name="b", model_id="org/b", dimension=64))
    names = registry.list_models()
    assert sorted(names) == ["a", "b"]


def test_get_quantized_exact() -> None:
    """Test get_quantized with a fully-qualified quantized name."""
    registry = EmbeddingModelRegistry()
    registry.register(
        ModelInfo(
            name="model-int8",
            model_id="org/model",
            dimension=32,
            quantization="int8",
        )
    )
    result = registry.get_quantized("model", "int8")
    assert result is not None
    assert result.name == "model-int8"


def test_get_quantized_fallback() -> None:
    """Test get_quantized falls back to matching quantization field."""
    registry = EmbeddingModelRegistry()
    registry.register(
        ModelInfo(
            name="model",
            model_id="org/model",
            dimension=32,
            quantization="fp16",
        )
    )
    result = registry.get_quantized("model", "fp16")
    assert result is not None
    assert result.name == "model"


def test_get_quantized_missing() -> None:
    """Test get_quantized returns None when variant is not found."""
    registry = EmbeddingModelRegistry()
    registry.register(ModelInfo(name="model", model_id="org/model", dimension=32))
    assert registry.get_quantized("model", "int8") is None


def test_default_registry_populated() -> None:
    """Test that get_default_registry returns pre-configured models."""
    registry = get_default_registry()
    names = registry.list_models()
    assert "bge-small-en-v1.5" in names
    assert "multilingual-e5-small" in names
    assert "mini-lm-en-ONNX" in names
    assert "bge-small-en-v1.5-int8" in names

    info = registry.resolve("bge-small-en-v1.5")
    assert info is not None
    assert info.dimension == 384
    assert info.pooling == "mean"
    assert info.normalize is True
    assert info.quantization is None
