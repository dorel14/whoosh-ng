"""ONNX quantization tests.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from whoosh_modern.embeddings.onnx_provider import ONNXEmbeddingProvider


@pytest.fixture
def dummy_onnx_model(tmp_path: Path) -> str:
    """Create a minimal fake ONNX model file for testing."""
    try:
        import onnx  # type: ignore[import-not-found]
        from onnx import TensorProto, helper
    except ImportError:
        pytest.skip("onnx package not installed")

    # Minimal model: input_ids -> identity output with matching shape/type
    ids = helper.make_tensor_value_info("input_ids", TensorProto.INT64, [1, 4])
    out = helper.make_tensor_value_info("output", TensorProto.INT64, [1, 4])
    node = helper.make_node("Identity", ["input_ids"], ["output"])
    graph = helper.make_graph([node], "dummy", [ids], [out])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    model_path = tmp_path / "dummy.onnx"
    model_path.write_bytes(model.SerializeToString())
    return str(model_path)


@pytest.fixture
def dummy_tokenizer(tmp_path: Path) -> str:
    """Create a minimal valid tokenizer JSON for testing."""
    tok_dir = tmp_path / "tok"
    tok_dir.mkdir()
    tokenizer_json = '{"version":"1.0","added_tokens":[],\
        "normalizer":null,"pre_tokenizer":null,"post_processor":null,"decoder":null,\
        "model":{"type":"BPE","dropout":0.0,"unk_token":null,"continuing_subword_prefix":null,\
        "end_of_word_suffix":null,"fuse_unk":false,"vocab":{"<unk>":0},"merges":[]}}'
    (tok_dir / "tokenizer.json").write_text(tokenizer_json, encoding="utf-8")
    (tok_dir / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (tok_dir / "config.json").write_text("{}", encoding="utf-8")
    return str(tok_dir)


def test_quantization_fp32(dummy_onnx_model: str, dummy_tokenizer: str) -> None:
    """Test ONNXEmbeddingProvider accepts fp32 quantization."""
    provider = ONNXEmbeddingProvider(
        model_path=dummy_onnx_model,
        tokenizer_dir=dummy_tokenizer,
        quantization="fp32",
    )
    assert provider is not None


def test_quantization_fp16(dummy_onnx_model: str, dummy_tokenizer: str) -> None:
    """Test ONNXEmbeddingProvider accepts fp16 quantization."""
    provider = ONNXEmbeddingProvider(
        model_path=dummy_onnx_model,
        tokenizer_dir=dummy_tokenizer,
        quantization="fp16",
    )
    assert provider is not None


def test_quantization_int8(dummy_onnx_model: str, dummy_tokenizer: str) -> None:
    """Test ONNXEmbeddingProvider accepts int8 quantization."""
    provider = ONNXEmbeddingProvider(
        model_path=dummy_onnx_model,
        tokenizer_dir=dummy_tokenizer,
        quantization="int8",
    )
    assert provider is not None


def test_quantization_invalid(dummy_onnx_model: str, dummy_tokenizer: str) -> None:
    """Test ONNXEmbeddingProvider rejects invalid quantization."""
    with pytest.raises(ValueError, match="Unsupported quantization"):
        ONNXEmbeddingProvider(
            model_path=dummy_onnx_model,
            tokenizer_dir=dummy_tokenizer,
            quantization="invalid",
        )
