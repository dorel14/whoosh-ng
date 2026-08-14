"""Tests for the embedding model manager."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from whoosh_modern.embeddings.model_manager import (
    EmbeddingModelManager,
    _get_default_models_dir,
)
from whoosh_modern.embeddings.registry import EmbeddingModelRegistry, ModelInfo


def _make_registry() -> EmbeddingModelRegistry:
    """Build a minimal registry with one test model.

    Returns:
        An ``EmbeddingModelRegistry`` with a single ``ModelInfo``.
    """
    registry = EmbeddingModelRegistry()
    registry.register(
        ModelInfo(
            name="test-model",
            model_id="org/test-model",
            dimension=128,
            pooling="mean",
            normalize=True,
            quantization=None,
            description="Test model for unit tests",
        )
    )
    return registry


def test_get_default_models_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_default_models_dir uses env var when set."""
    monkeypatch.setenv("WHOOSH_NG_MODELS_DIR", "/tmp/whoosh-models")
    result = _get_default_models_dir()
    assert result == Path("/tmp/whoosh-models").expanduser().resolve()


def test_get_default_models_dir_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_default_models_dir falls back to ~/.whoosh-ng/models/."""
    monkeypatch.delenv("WHOOSH_NG_MODELS_DIR", raising=False)
    result = _get_default_models_dir()
    assert result == Path.home() / ".whoosh-ng" / "models"


def test_init_defaults() -> None:
    """Test that EmbeddingModelManager uses default directory."""
    manager = EmbeddingModelManager(registry=_make_registry())
    assert manager.models_dir == _get_default_models_dir()


def test_init_custom_dir() -> None:
    """Test that a custom models_dir is respected."""
    manager = EmbeddingModelManager(models_dir="/custom/models", registry=_make_registry())
    assert manager.models_dir == Path("/custom/models").expanduser().resolve()


def test_get_model_dir() -> None:
    """Test that get_model_dir returns the expected path."""
    manager = EmbeddingModelManager(models_dir="/tmp/models", registry=_make_registry())
    result = manager.get_model_dir("test-model")
    assert result == Path("/tmp/models/test-model").expanduser().resolve()


def test_list_installed_empty(tmp_path: Path) -> None:
    """Test list_installed returns empty list when directory is empty."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.list_installed() == []


def test_list_installed_with_dirs(tmp_path: Path) -> None:
    """Test list_installed returns sorted model names."""
    (tmp_path / "model-a").mkdir()
    (tmp_path / "model-b").mkdir()
    (tmp_path / "not-a-dir.txt").write_text("skip")
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.list_installed() == ["model-a", "model-b"]


def test_is_installed_true(tmp_path: Path) -> None:
    """Test is_installed returns True when model dir has .onnx file."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"fake")
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.is_installed("test-model") is True


def test_is_installed_false_missing_dir(tmp_path: Path) -> None:
    """Test is_installed returns False when directory does not exist."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.is_installed("missing") is False


def test_is_installed_false_no_onnx(tmp_path: Path) -> None:
    """Test is_installed returns False when no .onnx file is present."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "readme.txt").write_text("no model here")
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.is_installed("test-model") is False


def test_download_creates_dir(tmp_path: Path) -> None:
    """Test that download creates the model directory."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    onnx_content = b"fake onnx model bytes"

    mock_response = MagicMock()
    mock_response.read.return_value = onnx_content
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        model_dir = manager.download(
            "test-model",
            urls=["https://example.com/model.onnx"],
        )

    assert model_dir.exists()
    assert (model_dir / "model.onnx").exists()
    assert (model_dir / "model.onnx").read_bytes() == onnx_content


def test_download_skips_existing(tmp_path: Path) -> None:
    """Test that download skips files that already exist."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    existing = tmp_path / "test-model" / "model.onnx"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"existing")

    call_count = 0

    def mock_urlopen(url: str, timeout: int = 60) -> MagicMock:
        nonlocal call_count
        call_count += 1
        raise AssertionError("urlopen should not be called for existing files")

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        model_dir = manager.download(
            "test-model",
            urls=["https://example.com/model.onnx"],
        )

    assert call_count == 0
    assert (model_dir / "model.onnx").read_bytes() == b"existing"


def test_download_unknown_model_raises() -> None:
    """Test that downloading an unknown model without URLs raises ValueError."""
    manager = EmbeddingModelManager(models_dir=Path("/tmp"), registry=_make_registry())
    with pytest.raises(ValueError, match="Unknown model"):
        manager.download("nonexistent-model")


def test_download_missing_onnx_raises(tmp_path: Path) -> None:
    """Test that download raises FileNotFoundError if no .onnx is produced."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())

    mock_response = MagicMock()
    mock_response.read.return_value = b"not an onnx file"
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with (
        patch("urllib.request.urlopen", return_value=mock_response),
        pytest.raises(FileNotFoundError, match="No .onnx file found"),
    ):
        manager.download(
            "test-model",
            urls=["https://example.com/readme.txt"],
        )


def test_verify_checksum_success(tmp_path: Path) -> None:
    """Test checksum verification succeeds for a matching file."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    content = b"hello world"
    expected = hashlib.sha256(content).hexdigest()
    (model_dir / "model.onnx").write_bytes(content)

    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.verify_checksum("test-model", expected) is True


def test_verify_checksum_mismatch(tmp_path: Path) -> None:
    """Test checksum verification fails for a mismatched file."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"hello world")

    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.verify_checksum("test-model", "00000000000000000000000000000000") is False


def test_verify_checksum_no_file(tmp_path: Path) -> None:
    """Test checksum verification returns False when no .onnx exists."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.verify_checksum("test-model", "abc123") is False


def test_verify_checksum_no_expected(tmp_path: Path) -> None:
    """Test that verify_checksum returns True when expected is None."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"any content")
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.verify_checksum("test-model", None) is True


def test_download_verifies_checksum(tmp_path: Path) -> None:
    """Test that download verifies checksum when expected_sha256 is given."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    content = b"verified content"
    expected = hashlib.sha256(content).hexdigest()

    mock_response = MagicMock()
    mock_response.read.return_value = content
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        model_dir = manager.download(
            "test-model",
            urls=["https://example.com/model.onnx"],
            expected_sha256=expected,
        )

    assert (model_dir / "model.onnx").exists()


def test_download_checksum_mismatch_raises(tmp_path: Path) -> None:
    """Test that download raises RuntimeError on checksum mismatch."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    content = b"some content"
    wrong_checksum = "0" * 64

    mock_response = MagicMock()
    mock_response.read.return_value = content
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with (
        patch("urllib.request.urlopen", return_value=mock_response),
        pytest.raises(RuntimeError, match="Checksum mismatch"),
    ):
        manager.download(
            "test-model",
            urls=["https://example.com/model.onnx"],
            expected_sha256=wrong_checksum,
        )


def test_build_default_urls() -> None:
    """Test that _build_default_urls generates correct HuggingFace URLs."""
    registry = _make_registry()
    manager = EmbeddingModelManager(base_url="https://huggingface.co", registry=registry)
    info = registry.resolve("test-model")
    assert info is not None
    urls = manager._build_default_urls(info)
    assert urls[0] == "https://huggingface.co/org/test-model/resolve/main/model.onnx"
    assert urls[1] == "https://huggingface.co/org/test-model/resolve/main/tokenizer.json"


def test_build_default_urls_quantized() -> None:
    """Test that _build_default_urls appends quantization suffix."""
    registry = EmbeddingModelRegistry()
    registry.register(
        ModelInfo(
            name="model-int8",
            model_id="org/model",
            dimension=64,
            quantization="int8",
        )
    )
    manager = EmbeddingModelManager(base_url="https://huggingface.co", registry=registry)
    info = registry.resolve("model-int8")
    assert info is not None
    urls = manager._build_default_urls(info)
    assert urls[0] == ("https://huggingface.co/org/model/resolve/main/model-int8.onnx")


# --- New methods: exists, info, remove, update ---


def test_exists_true(tmp_path: Path) -> None:
    """Test exists() returns True when model is installed."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"fake")
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.exists("test-model") is True


def test_exists_false(tmp_path: Path) -> None:
    """Test exists() returns False when model is not installed."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    assert manager.exists("missing") is False


def test_info_from_registry() -> None:
    """Test info() returns ModelInfo from registry."""
    manager = EmbeddingModelManager(registry=_make_registry())
    info = manager.info("test-model")
    assert info is not None
    assert info.name == "test-model"
    assert info.dimension == 128


def test_info_unknown() -> None:
    """Test info() returns None for unknown model."""
    manager = EmbeddingModelManager(registry=_make_registry())
    assert manager.info("nonexistent") is None


def test_remove_success(tmp_path: Path) -> None:
    """Test remove() deletes the model directory."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"fake")
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    manager.remove("test-model")
    assert not model_dir.exists()


def test_remove_missing_raises(tmp_path: Path) -> None:
    """Test remove() raises FileNotFoundError for missing model."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    with pytest.raises(FileNotFoundError, match="not installed"):
        manager.remove("missing")


def test_update_redownloads(tmp_path: Path) -> None:
    """Test update() removes old model and re-downloads."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    # Pre-install old content
    old_dir = tmp_path / "test-model"
    old_dir.mkdir()
    (old_dir / "model.onnx").write_bytes(b"old content")

    new_content = b"updated model"
    mock_response = MagicMock()
    mock_response.read.return_value = new_content
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = manager.update(
            "test-model",
            urls=["https://example.com/model.onnx"],
        )

    assert result.exists()
    assert (result / "model.onnx").read_bytes() == new_content


def test_update_missing_raises(tmp_path: Path) -> None:
    """Test update() raises FileNotFoundError for missing model."""
    manager = EmbeddingModelManager(models_dir=tmp_path, registry=_make_registry())
    with pytest.raises(FileNotFoundError, match="not installed"):
        manager.update("missing")


# --- CLI tests ---


def test_cli_list_installed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI list shows installed models."""
    (tmp_path / "model-a").mkdir()
    (tmp_path / "model-b").mkdir()
    from whoosh_modern.embeddings.cli import main

    rc = main(["--models-dir", str(tmp_path), "list"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "model-a" in captured.out
    assert "model-b" in captured.out


def test_cli_list_all(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI list --all shows available models from registry."""
    from whoosh_modern.embeddings.cli import main

    rc = main(["--models-dir", str(tmp_path), "list", "--all"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "bge-small-en-v1.5" in captured.out


def test_cli_info(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI info shows model metadata."""
    from whoosh_modern.embeddings.cli import main

    rc = main(["info", "bge-small-en-v1.5"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "bge-small-en-v1.5" in captured.out
    assert "384" in captured.out


def test_cli_info_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI info returns error for unknown model."""
    from whoosh_modern.embeddings.cli import main

    rc = main(["info", "nonexistent"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Unknown model" in captured.err


def test_cli_install(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI install downloads a model."""
    from whoosh_modern.embeddings.cli import main

    content = b"cli test onnx"
    mock_response = MagicMock()
    mock_response.read.return_value = content
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        rc = main(
            [
                "--models-dir",
                str(tmp_path),
                "install",
                "test-cli-model",
                "--url",
                "https://example.com/model.onnx",
            ]
        )

    captured = capsys.readouterr()
    assert rc == 0
    assert "installed" in captured.out.lower()
    assert (tmp_path / "test-cli-model" / "model.onnx").exists()


def test_cli_verify_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI verify succeeds for installed model."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"content")
    from whoosh_modern.embeddings.cli import main

    rc = main(["--models-dir", str(tmp_path), "verify", "test-model"])
    assert rc == 0
    assert "valid" in capsys.readouterr().out.lower()


def test_cli_verify_missing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test CLI verify fails for missing model."""
    from whoosh_modern.embeddings.cli import main

    rc = main(["verify", "missing-model"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "not installed" in captured.err


def test_cli_remove(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI remove deletes a model."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"content")
    from whoosh_modern.embeddings.cli import main

    rc = main(["--models-dir", str(tmp_path), "remove", "test-model"])
    assert rc == 0
    assert not model_dir.exists()


def test_cli_remove_missing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test CLI remove fails for missing model."""
    from whoosh_modern.embeddings.cli import main

    rc = main(["remove", "missing-model"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Error" in captured.err


def test_cli_update(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI update re-downloads a model."""
    model_dir = tmp_path / "test-model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"old")

    new_content = b"updated via CLI"
    mock_response = MagicMock()
    mock_response.read.return_value = new_content
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    from whoosh_modern.embeddings.cli import main

    with patch("urllib.request.urlopen", return_value=mock_response):
        rc = main(
            [
                "--models-dir",
                str(tmp_path),
                "update",
                "test-model",
                "--url",
                "https://example.com/model.onnx",
            ]
        )
    assert rc == 0
    assert (model_dir / "model.onnx").read_bytes() == new_content
