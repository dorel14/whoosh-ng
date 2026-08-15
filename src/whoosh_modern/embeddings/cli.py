"""CLI for managing ONNX embedding models.

Usage::

    whoosh-ng-models list
    whoosh-ng-models install bge-small-en-v1.5
    whoosh-ng-models info multilingual-e5-small
    whoosh-ng-models verify multilingual-e5-small
    whoosh-ng-models remove multilingual-e5-small
    whoosh-ng-models update multilingual-e5-small

Or via Python::

    python -m whoosh_modern.embeddings.cli list
    python -m whoosh_modern.embeddings.cli install bge-small-en-v1.5

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import logging
import sys

from whoosh_modern.embeddings.model_manager import EmbeddingModelManager
from whoosh_modern.embeddings.registry import get_default_registry

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ``ArgumentParser`` instance.
    """
    parser = argparse.ArgumentParser(
        prog="whoosh-ng-models",
        description="Manage ONNX embedding models for Whoosh-NG.",
    )
    parser.add_argument(
        "--models-dir",
        default=None,
        help="Models directory (default: ~/.whoosh-ng/models/ or WHOOSH_NG_MODELS_DIR)",
    )
    parser.add_argument(
        "--hf-token",
        default=None,
        help="HuggingFace token. Falls back to HF_TOKEN / HUGGING_FACE_HUB_TOKEN env vars.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    _list_parser = subparsers.add_parser("list", help="List installed models.")
    _list_parser.add_argument(
        "--all",
        action="store_true",
        help="List all available models (not just installed).",
    )

    _install_parser = subparsers.add_parser(
        "install", help="Download and cache an embedding model."
    )
    _install_parser.add_argument("model_name", help="Model name to install.")
    _install_parser.add_argument(
        "--quantization",
        default=None,
        help="Quantization variant (fp32, fp16, int8).",
    )
    _install_parser.add_argument(
        "--expected-sha256",
        default=None,
        help="Expected SHA256 checksum of the primary .onnx file.",
    )
    _install_parser.add_argument(
        "--url",
        action="append",
        default=None,
        help="Explicit download URL (can be passed multiple times).",
    )

    _info_parser = subparsers.add_parser("info", help="Show metadata for a model.")
    _info_parser.add_argument("model_name", help="Model name to inspect.")

    _verify_parser = subparsers.add_parser(
        "verify", help="Verify the integrity of an installed model."
    )
    _verify_parser.add_argument("model_name", help="Model name to verify.")
    _verify_parser.add_argument(
        "--expected-sha256",
        default=None,
        help="Expected SHA256 checksum of the primary .onnx file.",
    )

    _remove_parser = subparsers.add_parser(
        "remove", help="Remove an installed model from the local cache."
    )
    _remove_parser.add_argument("model_name", help="Model name to remove.")

    _update_parser = subparsers.add_parser(
        "update", help="Update an installed model by re-downloading it."
    )
    _update_parser.add_argument("model_name", help="Model name to update.")
    _update_parser.add_argument(
        "--expected-sha256",
        default=None,
        help="Expected SHA256 checksum of the primary .onnx file.",
    )
    _update_parser.add_argument(
        "--url",
        action="append",
        default=None,
        help="Explicit download URL (can be passed multiple times).",
    )

    return parser


def _cmd_list(args: argparse.Namespace, manager: EmbeddingModelManager) -> int:
    """Handle the ``list`` command.

    Lists installed models by default. When ``--all`` is passed, lists all
    models available in the registry, including those not yet installed.

    Args:
        args: Parsed CLI arguments.
        manager: Model manager instance.

    Returns:
        Exit code (0 on success).
    """
    if args.all:
        registry = get_default_registry()
        print("Available models:")
        for name in registry.list_models():
            info = registry.resolve(name)
            if info:
                q = f" ({info.quantization})" if info.quantization else ""
                print(f"  {name}{q}: {info.description}")
    else:
        installed = manager.list_installed()
        if not installed:
            print("No models installed.")
            return 0
        print("Installed models:")
        for name in installed:
            print(f"  {name}")
    return 0


def _cmd_install(args: argparse.Namespace, manager: EmbeddingModelManager) -> int:
    """Handle the ``install`` command.

    Downloads and caches an embedding model. If ``--quantization`` is passed,
    the registry is consulted to resolve the quantized variant name before
    downloading.

    Args:
        args: Parsed CLI arguments.
        manager: Model manager instance.

    Returns:
        Exit code (0 on success, 1 on error).
    """
    model_name = args.model_name
    quantization = args.quantization
    expected_sha256 = args.expected_sha256
    urls = args.url

    target_name = model_name
    if quantization:
        registry = get_default_registry()
        quantized = registry.get_quantized(model_name, quantization)
        target_name = quantized.name if quantized else f"{model_name}-{quantization}"

    try:
        model_dir = manager.download(target_name, urls=urls, expected_sha256=expected_sha256)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Model '{target_name}' installed at {model_dir}")
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    """Handle the ``info`` command.

    Shows metadata for a registered model without requiring it to be installed.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 on success, 1 if not found).
    """
    registry = get_default_registry()
    info = registry.resolve(args.model_name)
    if info is None:
        print(f"Unknown model: {args.model_name}", file=sys.stderr)
        return 1
    print(f"Name:            {info.name}")
    print(f"Model ID:        {info.model_id}")
    print(f"Dimension:       {info.dimension}")
    print(f"Pooling:         {info.pooling}")
    print(f"Normalize:       {info.normalize}")
    print(f"Quantization:    {info.quantization or 'fp32'}")
    print(f"Description:     {info.description}")
    return 0


def _cmd_verify(args: argparse.Namespace, manager: EmbeddingModelManager) -> int:
    """Handle the ``verify`` command.

    Verifies the integrity of an installed model using its SHA256 checksum
    when provided.

    Args:
        args: Parsed CLI arguments.
        manager: Model manager instance.

    Returns:
        Exit code (0 on success, 1 if verification fails).
    """
    model_name = args.model_name
    expected = args.expected_sha256
    if not manager.is_installed(model_name):
        print(f"Model '{model_name}' is not installed.", file=sys.stderr)
        return 1
    ok = manager.verify_checksum(model_name, expected)
    if ok:
        q = " (checksum verified)" if expected else " (file exists)"
        print(f"Model '{model_name}' is valid{q}.")
        return 0
    print(f"Model '{model_name}' failed checksum verification.", file=sys.stderr)
    return 1


def _cmd_remove(args: argparse.Namespace, manager: EmbeddingModelManager) -> int:
    """Handle the ``remove`` command.

    Removes an installed model from the local cache.

    Args:
        args: Parsed CLI arguments.
        manager: Model manager instance.

    Returns:
        Exit code (0 on success, 1 on error).
    """
    try:
        manager.remove(args.model_name)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_update(args: argparse.Namespace, manager: EmbeddingModelManager) -> int:
    """Handle the ``update`` command.

    Re-downloads an installed model to refresh its files.

    Args:
        args: Parsed CLI arguments.
        manager: Model manager instance.

    Returns:
        Exit code (0 on success, 1 on error).
    """
    try:
        model_dir = manager.update(
            args.model_name,
            urls=args.url,
            expected_sha256=args.expected_sha256,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Model '{args.model_name}' updated at {model_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the models CLI.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if not args.command:
        parser.print_help()
        return 0

    manager = EmbeddingModelManager(models_dir=args.models_dir, hf_token=args.hf_token)

    if args.command == "list":
        return _cmd_list(args, manager)
    if args.command == "install":
        return _cmd_install(args, manager)
    if args.command == "info":
        return _cmd_info(args)
    if args.command == "verify":
        return _cmd_verify(args, manager)
    if args.command == "remove":
        return _cmd_remove(args, manager)
    if args.command == "update":
        return _cmd_update(args, manager)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
