"""ONNX Runtime embedding provider for Whoosh-NG.

Provides local CPU-friendly embeddings via ONNX Runtime without any PyTorch
dependency. Uses HuggingFace ``tokenizers`` for tokenization and ``onnxruntime``
for inference. Supports mean / cls / max pooling and L2 normalization.

Typical usage::

    provider = ONNXEmbeddingProvider(
        model_path="models/multilingual-e5-small",
        tokenizer_dir="models/multilingual-e5-small",
    )
    vector = provider.embed("hello world")
    batch = provider.embed_batch(["hello", "world"])

Install the optional dependencies::

    pip install whoosh-ng[embeddings-onnx]

Author: SoniqueBay Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ONNXEmbeddingProvider:
    """Embedding provider using ONNX Runtime for CPU-friendly inference.

    Loads a quantized or full-precision ONNX model together with a HuggingFace
    ``tokenizers``-based tokenizer and exposes single-text and batch embedding
    methods. Supports configurable pooling strategies and optional L2
    normalization.

    Args:
        model_path: Path to the ``.onnx`` model file.
        tokenizer_dir: Directory containing the HuggingFace tokenizer files
            (``tokenizer.json``, ``tokenizer_config.json``, etc.). Defaults to
            the parent directory of ``model_path`` when omitted.
        pooling: Pooling strategy applied to token-level outputs. One of
            ``"mean"``, ``"cls"``, or ``"max"``. Defaults to ``"mean"``.
        normalize: When ``True``, L2-normalize the final embedding vector.
            Defaults to ``True``.
        dimension: Expected embedding dimension. When ``None``, the dimension
            is inferred from the ONNX model output shape at first inference.
        enable_prefix: When ``True``, prepend the E5-style task prefix
            (``"query: "`` or ``"passage: "``) to inputs. Set to ``False``
            when the model does not expect a prefix. Defaults to ``True``.

    Raises:
        ImportError: If ``tokenizers`` or ``onnxruntime`` are not installed.
        FileNotFoundError: If ``model_path`` does not point to an existing
            file.
        ValueError: If ``pooling`` is not one of the accepted values.
    """

    def __init__(
        self,
        model_path: str,
        tokenizer_dir: str | None = None,
        pooling: str = "mean",
        normalize: bool = True,
        dimension: int | None = None,
        enable_prefix: bool = True,
        quantization: str = "fp32",
    ) -> None:
        """Initialize the ONNX embedding provider.

        Args:
            model_path: Path to the ``.onnx`` model file.
            tokenizer_dir: Directory containing the HuggingFace tokenizer files.
            pooling: Pooling strategy (``"mean"``, ``"cls"``, ``"max"``).
            normalize: Whether to L2-normalize the output vectors.
            dimension: Expected embedding dimension (optional).
            enable_prefix: Whether to apply E5-style task prefixes.
            quantization: Quantization level (``"fp32"``, ``"fp16"``, ``"int8"``).
        """
        if pooling not in ("mean", "cls", "max"):
            raise ValueError(
                f"Unsupported pooling strategy: {pooling!r}. Choose from 'mean', 'cls', or 'max'."
            )
        if quantization not in ("fp32", "fp16", "int8"):
            raise ValueError(
                f"Unsupported quantization: {quantization!r}. "
                "Choose from 'fp32', 'fp16', or 'int8'."
            )

        model_file = Path(model_path)
        if not model_file.is_file():
            raise FileNotFoundError(f"ONNX model file not found: {model_path!r}")

        resolved_tokenizer_dir = (
            Path(tokenizer_dir) if tokenizer_dir is not None else model_file.parent
        )

        try:
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise ImportError(
                "ONNXEmbeddingProvider requires the 'tokenizers' package. "
                "Install it with: pip install tokenizers"
            ) from exc

        try:
            import onnxruntime as ort

            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = 1
            sess_options.inter_op_num_threads = 1
            if quantization == "fp16":
                sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            providers = ["CPUExecutionProvider"]
            self._session: Any = ort.InferenceSession(
                str(model_file),
                sess_options=sess_options,
                providers=providers,
            )
        except ImportError as exc:
            raise ImportError(
                "ONNXEmbeddingProvider requires onnxruntime. "
                "Install it with: pip install whoosh-ng[embeddings-onnx]"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to load ONNX model from {model_path!r}: {exc}") from exc

        try:
            self._tokenizer: Any = Tokenizer.from_file(
                str(resolved_tokenizer_dir / "tokenizer.json")
            )
            self._tokenizer.enable_truncation(max_length=512)
            self._tokenizer.enable_padding()
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load tokenizer from {resolved_tokenizer_dir!r}: {exc}"
            ) from exc

        self._pooling = pooling
        self._normalize = normalize
        self._dimension = dimension
        self._enable_prefix = enable_prefix
        self._model_path = str(model_file)
        self._dimension_inferred = False

        logger.debug(
            "ONNXEmbeddingProvider initialized: model=%s, pooling=%s, normalize=%s",
            model_file.name,
            pooling,
            normalize,
        )

    def _infer_dimension(self) -> None:
        """Infer the embedding dimension from the ONNX session output shape.

        Sets ``self._dimension`` from the last dimension of the first output
        tensor when it was not provided at construction time.
        """
        if self._dimension_inferred or self._dimension is not None:
            return
        try:
            output = self._session.get_outputs()[0]
            shape = output.shape
            if shape and shape[-1] is not None:
                self._dimension = int(shape[-1])
        except Exception:
            pass
        self._dimension_inferred = True

    @property
    def dimension(self) -> int | None:
        """Return the embedding dimension, or ``None`` if not yet determined.

        The dimension is inferred from the ONNX model output shape on the
        first call to :meth:`embed_batch` when not provided at construction
        time.
        """
        return self._dimension

    def _apply_prefix(self, text: str, is_query: bool = False) -> str:
        """Apply the E5-style task prefix when enabled.

        Args:
            text: The raw input text.
            is_query: When ``True``, use the ``"query: "`` prefix; otherwise
                use ``"passage: "``.

        Returns:
            The (possibly prefixed) text string.
        """
        if not self._enable_prefix:
            return text
        prefix = "query: " if is_query else "passage: "
        return f"{prefix}{text}"

    def _pool(
        self,
        token_embeddings: list[list[float]],
        attention_mask: list[int],
    ) -> list[float]:
        """Apply the configured pooling strategy to token-level embeddings.

        Args:
            token_embeddings: Per-token embedding vectors (one list per token).
            attention_mask: Attention mask (1 for real tokens, 0 for padding).

        Returns:
            A single pooled embedding vector.
        """
        if self._pooling == "cls":
            return token_embeddings[0]

        if self._pooling == "max":
            return [
                max(v for v, mask in zip(values, attention_mask, strict=False) if mask)
                for values in zip(*token_embeddings, strict=False)
            ]

        valid = [
            values for values, mask in zip(token_embeddings, attention_mask, strict=False) if mask
        ]
        dim = self._dimension or 0
        if not valid:
            return [0.0] * dim
        return [sum(v) / len(valid) for v in zip(*valid, strict=False)]

    def _normalize_vector(self, vector: list[float]) -> list[float]:
        """L2-normalize the given vector.

        Args:
            vector: The raw embedding vector.

        Returns:
            The L2-normalized embedding vector.
        """
        import math

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0.0:
            return vector
        return [v / norm for v in vector]

    def embed(self, text: str) -> list[float]:
        """Embed a single text into a vector.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts into vectors.

        Runs the tokenizer and ONNX session once per batch for throughput.

        Args:
            texts: Sequence of texts to embed.

        Returns:
            A list of embedding vectors, one per input text.
        """
        if not texts:
            return []

        self._infer_dimension()

        prefixed = [self._apply_prefix(t) for t in texts]
        encoded = self._tokenizer.encode_batch(prefixed)
        input_ids = [e.ids for e in encoded]
        attention_mask = [e.attention_mask for e in encoded]

        input_name = self._session.get_inputs()[0].name
        ort_inputs: dict[str, Any] = {input_name: input_ids}
        if len(self._session.get_inputs()) > 1:
            mask_name = self._session.get_inputs()[1].name
            ort_inputs[mask_name] = attention_mask

        outputs = self._session.run(None, ort_inputs)
        token_embeddings = outputs[0].tolist()

        results: list[list[float]] = []
        for token_vecs, mask in zip(token_embeddings, attention_mask, strict=False):
            vector = self._pool(token_vecs, mask)
            if self._normalize:
                vector = self._normalize_vector(vector)
            results.append(vector)

        logger.debug("ONNX batch embedding: %d texts processed", len(texts))
        return results

    def __repr__(self) -> str:
        return (
            f"ONNXEmbeddingProvider("
            f"model_path={self._model_path!r}, "
            f"pooling={self._pooling!r}, "
            f"normalize={self._normalize}, "
            f"quantization={self._pooling!r}"
            f")"
        )
