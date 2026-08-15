"""Tests for embedding providers."""

from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from whoosh_modern.embeddings.sentence_transformers_provider import (
    SentenceTransformersProvider,
)


def test_sentence_transformers_provider_embed() -> None:
    pytest.importorskip("sentence_transformers", reason="sentence-transformers not installed")
    provider = SentenceTransformersProvider()
    vector = provider.embed("hello world")
    assert len(vector) > 0
    assert all(isinstance(v, float) for v in vector)


pytest.importorskip("onnxruntime", reason="onnxruntime not installed")
pytest.importorskip("tokenizers", reason="tokenizers not installed")

from whoosh_modern.embeddings.onnx_provider import ONNXEmbeddingProvider


def _make_fake_onnx(tmp_path: Path, dimension: int = 4) -> Path:
    """Create a minimal fake ONNX model file for testing.

    Uses the real ``onnx`` package to serialize a trivial MatMul graph so
    ``onnxruntime`` can load and run it. Falls back to an empty file if
    ``onnx`` is unavailable.

    Args:
        tmp_path: Pytest-provided temporary directory.
        dimension: Embedding dimension for the fake model output.

    Returns:
        Path to the fake ``.onnx`` model file.
    """
    model_path = tmp_path / "fake_model.onnx"
    try:
        import onnx  # type: ignore[import-not-found]
        from onnx import TensorProto, helper

        x = helper.make_tensor_value_info("input_ids", TensorProto.INT64, [None, None])
        y = helper.make_tensor_value_info(
            "token_embeddings", TensorProto.FLOAT, [None, None, dimension]
        )
        matmul_node = helper.make_node("MatMul", ["input_ids", "W"], ["token_embeddings"])
        w_initializer = helper.make_tensor(
            "W",
            TensorProto.FLOAT,
            [None, dimension],
            [1.0] * (10 * dimension),
        )
        graph = helper.make_graph(
            [matmul_node],
            "fake_model",
            [x],
            [y],
            initializer=[w_initializer],
        )
        model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
        model.ir_version = 8
        onnx.save(model, str(model_path))
    except Exception:
        model_path.write_bytes(b"")
    return model_path


def _make_provider(
    tmp_path: Path,
    dimension: int = 4,
    *,
    pooling: str = "mean",
    normalize: bool = True,
    enable_prefix: bool = False,
    tokenizer_encode_return=None,
    session_run_return=None,
) -> tuple[ONNXEmbeddingProvider, MagicMock, MagicMock]:
    """Build an ONNXEmbeddingProvider with fully controlled, per-call mocks.

    Each call patches ``tokenizers`` and ``onnxruntime`` independently so
    no mock state leaks between tests.

    Args:
        tmp_path: Pytest-provided temporary directory.
        dimension: Embedding dimension.
        pooling: Pooling strategy to use.
        normalize: Whether to L2-normalize output vectors.
        enable_prefix: Whether to apply E5-style task prefixes.
        tokenizer_encode_return: Iterable of per-text encoding results. Each
            item must expose ``.ids`` (list[list[int]]) and
            ``.attention_mask`` (list[list[int]]). Defaults to one result
            with 3 tokens and full mask.
        session_run_return: Value to return from ``session.run``.
            Defaults to a (1, 3, dimension) float32 identity rows array.

    Returns:
        A tuple of (provider, mock_tokenizer, mock_session).
    """
    model_path = _make_fake_onnx(tmp_path, dimension=dimension)

    if tokenizer_encode_return is None:
        _default_enc = MagicMock()
        _default_enc.ids = [[1, 2, 3]]
        _default_enc.attention_mask = [[1, 1, 1]]
        tokenizer_encode_return = [_default_enc]

    if session_run_return is None:
        session_run_return = np.eye(dimension, dtype=np.float32).reshape(1, dimension, dimension)

    mock_tokenizer = MagicMock()
    mock_tokenizer.encode_batch.return_value = list(tokenizer_encode_return)

    mock_session = MagicMock()
    mock_session.get_inputs.return_value = [MagicMock(name="input_ids")]
    mock_session.run.return_value = [session_run_return]

    with (
        patch("tokenizers.Tokenizer.from_file", return_value=mock_tokenizer),
        patch("onnxruntime.InferenceSession", return_value=mock_session),
    ):
        provider = ONNXEmbeddingProvider(
            model_path=str(model_path),
            pooling=pooling,
            normalize=normalize,
            dimension=dimension,
            enable_prefix=enable_prefix,
        )

    return provider, mock_tokenizer, mock_session


def test_onnx_provider_embed(tmp_path: Path) -> None:
    """Test that embed returns a list of floats with the correct dimension."""
    provider, _, _ = _make_provider(tmp_path, dimension=4)
    vector = provider.embed("hello world")
    assert isinstance(vector, list)
    assert len(vector) == 4
    assert all(isinstance(v, float) for v in vector)


def test_onnx_provider_embed_batch(tmp_path: Path) -> None:
    """Test that embed_batch returns one vector per input text."""
    n_texts = 3
    dimension = 4
    batch_output = np.zeros((n_texts, 3, dimension), dtype=np.float32)
    for i in range(n_texts):
        batch_output[i, i % 3, :] = 1.0

    encode_return = []
    for _ in range(n_texts):
        enc = MagicMock()
        enc.ids = [[1, 2, 3]]
        enc.attention_mask = [[1, 1, 1]]
        encode_return.append(enc)

    provider, _, _ = _make_provider(
        tmp_path,
        dimension=dimension,
        tokenizer_encode_return=encode_return,
        session_run_return=batch_output,
    )
    vectors = provider.embed_batch(["hello", "world", "foo"])
    assert len(vectors) == n_texts
    for v in vectors:
        assert len(v) == dimension
        assert all(isinstance(x, float) for x in v)


def test_onnx_provider_normalize(tmp_path: Path) -> None:
    """Test that normalize=True produces unit-norm vectors."""
    # [1,1,1,0] has norm sqrt(3) != 1, so normalization is observable
    nonzero_output = np.array(
        [[[1.0, 1.0, 1.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]],
        dtype=np.float32,
    )
    provider, _, _ = _make_provider(
        tmp_path,
        dimension=4,
        session_run_return=nonzero_output,
    )
    vector = provider.embed("test")
    norm = math.sqrt(sum(v * v for v in vector))
    assert norm == pytest.approx(1.0, abs=1e-5)


def test_onnx_provider_no_normalize(tmp_path: Path) -> None:
    """Test that normalize=False leaves raw (non-unit-norm) vectors."""
    # [1,1,1,0] has norm sqrt(3); without normalization it stays non-unit
    nonzero_output = np.array(
        [[[1.0, 1.0, 1.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]],
        dtype=np.float32,
    )
    provider, _, _ = _make_provider(
        tmp_path,
        dimension=4,
        normalize=False,
        session_run_return=nonzero_output,
    )
    vector = provider.embed("test")
    norm = math.sqrt(sum(v * v for v in vector))
    assert norm != pytest.approx(1.0, abs=1e-5)


def test_onnx_provider_prefix(tmp_path: Path) -> None:
    """Test that enable_prefix=True prepends the passage prefix."""
    passage_prefix = "passage: hello world"
    # Build enc result by setting attributes post-construction to avoid
    # MagicMock auto-creating child mocks for attribute access.
    enc_result = MagicMock()
    enc_result.ids = [[1]]
    enc_result.attention_mask = [[1]]
    encode_return = [enc_result]

    provider, mock_tokenizer, _ = _make_provider(
        tmp_path,
        enable_prefix=True,
        tokenizer_encode_return=encode_return,
    )
    provider.embed("hello world")
    called_texts = mock_tokenizer.encode_batch.call_args[0][0]
    assert called_texts[0] == passage_prefix


def test_onnx_provider_pooling_cls(tmp_path: Path) -> None:
    """Test that pooling='cls' returns the first token embedding."""
    cls_output = np.array(
        [[[5.0, 6.0, 7.0, 8.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]],
        dtype=np.float32,
    )
    # Use normalize=False so the raw CLS vector is observable without
    # the L2-normalization step obscuring the expected values.
    provider, _, _ = _make_provider(
        tmp_path,
        dimension=4,
        pooling="cls",
        normalize=False,
        session_run_return=cls_output,
    )
    vector = provider.embed("hello")
    assert vector == pytest.approx([5.0, 6.0, 7.0, 8.0], abs=1e-6)


def test_onnx_provider_empty_batch(tmp_path: Path) -> None:
    """Test that embed_batch with an empty input returns an empty list."""
    provider, _, _ = _make_provider(tmp_path, dimension=4)
    assert provider.embed_batch([]) == []


def test_onnx_provider_invalid_pooling(tmp_path: Path) -> None:
    """Test that an invalid pooling strategy raises ValueError."""
    model_path = _make_fake_onnx(tmp_path, dimension=4)
    with pytest.raises(ValueError, match="Unsupported pooling strategy"):
        ONNXEmbeddingProvider(
            model_path=str(model_path),
            pooling="invalid",
            enable_prefix=False,
        )


def test_onnx_provider_missing_model() -> None:
    """Test that a missing model file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="ONNX model file not found"):
        ONNXEmbeddingProvider(
            model_path="/nonexistent/path/model.onnx",
            enable_prefix=False,
        )


def test_onnx_provider_repr(tmp_path: Path) -> None:
    """Test the string representation of the provider."""
    provider, _, _ = _make_provider(tmp_path, dimension=4)
    r = repr(provider)
    assert "ONNXEmbeddingProvider" in r
    assert "fake_model.onnx" in r
