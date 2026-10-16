"""Example: Embeddings with ONNXEmbeddingProvider.

Install:
    pip install whoosh-ng[embeddings-onnx]

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from whoosh_modern.embeddings import EmbeddingModelManager, ONNXEmbeddingProvider


def main() -> None:
    manager = EmbeddingModelManager()
    model_dir = manager.download("multilingual-e5-small")
    onnx_path = str(next(model_dir.glob("*.onnx")))

    provider = ONNXEmbeddingProvider(
        model_path=onnx_path,
        tokenizer_dir=str(model_dir),
        pooling="mean",
        normalize=True,
    )

    vector = provider.embed("hello world")
    print(f"Dimension: {len(vector)}")

    batch = provider.embed_batch(["hello", "world"])
    print(f"Batch size: {len(batch)}")


if __name__ == "__main__":
    main()
