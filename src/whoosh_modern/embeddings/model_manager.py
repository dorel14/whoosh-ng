"""Model manager for ONNX embedding models.

Provides ``EmbeddingModelManager`` to download, cache, and verify ONNX
embedding models in ``~/.whoosh-ng/models/``. Uses ``huggingface_hub`` when
available (via the ``embeddings-onnx`` extra) and falls back to
``urllib.request`` otherwise.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any

from whoosh_modern.embeddings.registry import (
    EmbeddingModelRegistry,
    ModelInfo,
    get_default_registry,
)

try:
    from huggingface_hub import hf_hub_download as _hf_hub_download

    _HAS_HUGGINGFACE_HUB = True
except ImportError:
    _HAS_HUGGINGFACE_HUB = False

    def _hf_hub_download(*args: Any, **kwargs: Any) -> Any:  # type: ignore[no-redef]
        raise ImportError("huggingface_hub is required for this operation")

logger = logging.getLogger(__name__)

DEFAULT_MODELS_DIR_ENV = "WHOOSH_NG_MODELS_DIR"
DEFAULT_MODELS_RELATIVE = ".whoosh-ng/models"
_HF_TOKEN_ENV_VARS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")


def _get_hf_token() -> str | None:
    """Return the first available HuggingFace token from environment.

    Checks ``HF_TOKEN`` then ``HUGGING_FACE_HUB_TOKEN``.

    Returns:
        The token string, or ``None`` if no token is configured.
    """
    for env_var in _HF_TOKEN_ENV_VARS:
        token = os.environ.get(env_var)
        if token:
            return token
    return None


def _get_default_models_dir() -> Path:
    """Return the default models directory.

    Checks the ``WHOOSH_NG_MODELS_DIR`` environment variable first,
    then falls back to ``~/.whoosh-ng/models/``.

    Returns:
        The resolved ``Path`` to the models directory.
    """
    env_dir = os.environ.get(DEFAULT_MODELS_DIR_ENV)
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return Path.home() / ".whoosh-ng" / "models"


class EmbeddingModelManager:
    """Manage ONNX embedding model downloads and local cache.

    Handles downloading model files to ``~/.whoosh-ng/models/``, verifying
    SHA256 checksums, and listing installed models. Uses ``urllib.request``
    so no extra HTTP dependency is required.

    Args:
        models_dir: Directory for model storage. Defaults to
            ``~/.whoosh-ng/models/`` or ``WHOOSH_NG_MODELS_DIR`` env var.
        base_url: Base URL for model downloads. Defaults to
            ``"https://huggingface.co"``.
        registry: Optional ``EmbeddingModelRegistry`` instance. Defaults to
            ``get_default_registry()``.

    Attributes:
        _models_dir: Resolved models directory path.
        _base_url: Base URL for downloads.
        _registry: Model metadata registry.
    """

    def __init__(
        self,
        models_dir: Path | str | None = None,
        base_url: str = "https://huggingface.co",
        registry: EmbeddingModelRegistry | None = None,
        hf_token: str | None = None,
    ) -> None:
        """Initialize the model manager.

        Args:
            models_dir: Directory for model storage.
            base_url: Base URL for model downloads.
            registry: Optional model metadata registry.
            hf_token: Optional HuggingFace token. Falls back to
                ``HF_TOKEN`` / ``HUGGING_FACE_HUB_TOKEN`` env vars.
        """
        if models_dir is None:
            self._models_dir: Path = _get_default_models_dir()
        else:
            self._models_dir = Path(models_dir).expanduser().resolve()
        self._base_url = base_url.rstrip("/")
        self._registry = registry or get_default_registry()
        self._hf_token = hf_token or _get_hf_token()

    @property
    def models_dir(self) -> Path:
        """Return the models directory path."""
        return self._models_dir

    def get_model_dir(self, model_name: str) -> Path:
        """Return the local directory for a model.

        Args:
            model_name: Model identifier.

        Returns:
            Path to the model's local directory.
        """
        return self._models_dir / model_name

    @staticmethod
    def get_default_models_dir() -> Path:
        """Return the default models directory path.

        Returns:
            The default ``Path`` for model storage.
        """
        return _get_default_models_dir()

    def list_installed(self) -> list[str]:
        """List locally installed model names.

        Returns:
            A sorted list of model name strings found in the models
            directory.
        """
        if not self._models_dir.exists():
            return []
        return sorted(p.name for p in self._models_dir.iterdir() if p.is_dir())

    def is_installed(self, model_name: str) -> bool:
        """Check whether a model is present locally.

        Args:
            model_name: Model identifier.

        Returns:
            ``True`` if the model directory exists and contains an
            ``.onnx`` file.
        """
        model_dir = self.get_model_dir(model_name)
        if not model_dir.exists():
            return False
        return any(p.suffix == ".onnx" for p in model_dir.iterdir())

    def exists(self, model_name: str) -> bool:
        """Check whether a model is present locally.

        Alias for :meth:`is_installed`.

        Args:
            model_name: Model identifier.

        Returns:
            ``True`` if the model is installed locally.
        """
        return self.is_installed(model_name)

    def info(self, model_name: str) -> ModelInfo | None:
        """Return metadata for a model from the registry.

        Args:
            model_name: Model identifier.

        Returns:
            The ``ModelInfo`` from the registry, or ``None`` if not found.
        """
        return self._registry.resolve(model_name)

    def remove(self, model_name: str) -> None:
        """Remove a model from the local cache.

        Args:
            model_name: Model identifier.

        Raises:
            FileNotFoundError: If the model directory does not exist.
        """
        model_dir = self.get_model_dir(model_name)
        if not model_dir.exists():
            raise FileNotFoundError(f"Model '{model_name}' is not installed at {model_dir}")
        import shutil

        shutil.rmtree(model_dir)
        logger.info("Model '%s' removed from %s", model_name, model_dir)

    def update(
        self,
        model_name: str,
        urls: list[str] | None = None,
        expected_sha256: str | None = None,
    ) -> Path:
        """Update a model by re-downloading it.

        Removes the existing model directory and re-downloads.

        Args:
            model_name: Model identifier.
            urls: Optional list of file URLs to download.
            expected_sha256: Optional expected SHA256 of the primary
                ``.onnx`` file.

        Returns:
            Path to the updated model directory.

        Raises:
            FileNotFoundError: If the model is not currently installed.
        """
        model_dir = self.get_model_dir(model_name)
        if not model_dir.exists():
            raise FileNotFoundError(f"Model '{model_name}' is not installed at {model_dir}")
        import shutil

        shutil.rmtree(model_dir)
        logger.info("Removed existing model '%s' for update", model_name)
        return self.download(model_name, urls=urls, expected_sha256=expected_sha256)

    def verify_checksum(self, model_name: str, expected_sha256: str | None = None) -> bool:
        """Verify the SHA256 checksum of a model's ``.onnx`` file.

        Args:
            model_name: Model identifier.
            expected_sha256: Expected SHA256 hex digest. When ``None``,
                only the file existence is checked.

        Returns:
            ``True`` if the checksum matches or no expected checksum was
            provided.
        """
        model_dir = self.get_model_dir(model_name)
        onnx_files = list(model_dir.glob("*.onnx"))
        if not onnx_files:
            return False
        if expected_sha256 is None:
            return True
        digest = hashlib.sha256()
        with open(onnx_files[0], "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest().lower() == expected_sha256.lower()

    def download(
        self,
        model_name: str,
        urls: list[str] | None = None,
        expected_sha256: str | None = None,
    ) -> Path:
        """Download model files to the local cache.

        Creates the model directory if needed, then downloads each URL
        into it. Skips files that already exist unless the checksum does
        not match.

        When ``huggingface_hub`` is installed, downloads are resolved
        through the Hub instead of guessing raw HTTP URLs.

        Args:
            model_name: Model identifier (used as the sub-directory name).
            urls: List of file URLs to download. Defaults to HuggingFace
                Hub paths derived from the registry entry for
                ``model_name``.
            expected_sha256: Optional expected SHA256 of the primary
                ``.onnx`` file for integrity verification.

        Returns:
            Path to the model's local directory.

        Raises:
            ValueError: If ``model_name`` is not in the registry and no
                ``urls`` are provided.
            FileNotFoundError: If the downloaded ``.onnx`` file is missing
                after download.
            RuntimeError: If the checksum does not match the expected value.
        """
        model_info = self._registry.resolve(model_name)
        model_dir = self.get_model_dir(model_name)
        model_dir.mkdir(parents=True, exist_ok=True)

        if _HAS_HUGGINGFACE_HUB and urls is None:
            if model_info is None:
                raise ValueError(
                    f"Unknown model '{model_name}'. "
                    "Provide explicit `urls` or register the model first."
                )
            onnx_candidates = self._get_onnx_candidates(model_info)
            other_files = [
                "tokenizer.json",
                "tokenizer_config.json",
                "config.json",
            ]
            onnx_dest = model_dir / "model.onnx"
            if not self._download_onnx_with_hf(
                model_info, onnx_candidates, onnx_dest
            ):
                raise FileNotFoundError(
                    f"Failed to download any ONNX file for '{model_name}' "
                    f"from candidates {onnx_candidates}"
                )
            for filename in other_files:
                try:
                    _hf_hub_download(
                        repo_id=model_info.model_id,
                        filename=filename,
                        repo_type="model",
                        revision="main",
                        local_dir=model_dir,
                        force_download=False,
                        token=self._hf_token,
                    )
                except Exception as exc:
                    logger.warning("Failed to download %s: %s", filename, exc)
        else:
            if urls is None:
                if model_info is None:
                    raise ValueError(
                        f"Unknown model '{model_name}'. "
                        "Provide explicit `urls` or register the model first."
                    )
                urls = self._build_default_urls(model_info)

            for url in urls:
                filename = url.rsplit("/", 1)[-1] or "model.onnx"
                dest = model_dir / filename
                self._download_file(url, dest)

        onnx_files = list(model_dir.glob("*.onnx"))
        if not onnx_files:
            raise FileNotFoundError(f"No .onnx file found in {model_dir} after download")

        if expected_sha256 is not None and not self.verify_checksum(model_name, expected_sha256):
            raise RuntimeError(
                f"Checksum mismatch for model '{model_name}'. "
                f"Expected {expected_sha256}, got {self._sha256_of(onnx_files[0])}"
            )

        logger.info("Model '%s' ready at %s", model_name, model_dir)
        return model_dir

    def _build_default_urls(self, model_info: ModelInfo) -> list[str]:
        """Build default download URLs from a ``ModelInfo``.

        Args:
            model_info: Model metadata.

        Returns:
            A list of URLs for ``.onnx``, ``tokenizer.json``, and
            ``config.json``.
        """
        base = f"{self._base_url}/{model_info.model_id}/resolve/main"
        suffix = f"-{model_info.quantization}" if model_info.quantization else ""
        subfolder = model_info.subfolder or ""
        if subfolder:
            subfolder = f"{subfolder}/"
        return [
            f"{base}/{subfolder}model{suffix}.onnx",
            f"{base}/tokenizer.json",
            f"{base}/tokenizer_config.json",
            f"{base}/config.json",
        ]

    def _get_onnx_candidates(self, model_info: ModelInfo) -> list[str]:
        """Return candidate ONNX filenames for the given model.

        Args:
            model_info: Model metadata.

        Returns:
            A list of candidate filenames to try via ``huggingface_hub``.
        """
        suffix = f"-{model_info.quantization}" if model_info.quantization else ""
        base_names = [
            f"model{suffix}.onnx",
            f"model{suffix}_fp16.onnx",
            f"model{suffix}_quantized.onnx",
        ]
        if model_info.subfolder:
            return [f"{model_info.subfolder}/{name}" for name in base_names]
        return base_names

    def _download_onnx_with_hf(
        self,
        model_info: ModelInfo,
        candidates: list[str],
        dest: Path,
    ) -> bool:
        """Try downloading an ONNX file via ``huggingface_hub``.

        Args:
            model_info: Model metadata.
            candidates: Candidate repo-relative paths to try.
            dest: Destination path for the downloaded file.

        Returns:
            ``True`` if any candidate was downloaded successfully.
        """
        for candidate in candidates:
            subfolder = None
            filename = candidate
            if "/" in candidate:
                subfolder, filename = candidate.split("/", 1)
            try:
                local_path = _hf_hub_download(
                    repo_id=model_info.model_id,
                    filename=filename,
                    repo_type="model",
                    revision="main",
                    subfolder=subfolder,
                )
                import shutil

                shutil.copy2(local_path, dest)
                return True
            except Exception:
                continue
        return False

    def _download_file(self, url: str, dest: Path) -> None:
        """Download a file from ``url`` to ``dest``.

        Skips download if the destination already exists.

        Args:
            url: Source URL.
            dest: Destination file path.

        Raises:
            RuntimeError: If the download fails.
        """
        if dest.exists():
            logger.debug("Skipping existing file: %s", dest)
            return
        logger.debug("Downloading %s -> %s", url, dest)
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            dest.write_bytes(data)
        except Exception as exc:
            raise RuntimeError(f"Failed to download {url!r} to {dest!r}: {exc}") from exc

    def _try_download_any(self, urls: list[str], dest: Path) -> bool:
        """Try downloading from multiple URLs until one succeeds.

        Args:
            urls: Candidate source URLs.
            dest: Destination file path.

        Returns:
            ``True`` if any download succeeded, ``False`` otherwise.
        """
        for url in urls:
            try:
                self._download_file(url, dest)
                return True
            except RuntimeError:
                continue
        return False

    def _sha256_of(self, path: Path) -> str:
        """Compute the SHA256 hex digest of a file.

        Args:
            path: Path to the file.

        Returns:
            Lowercase SHA256 hex digest string.
        """
        digest = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest().lower()
