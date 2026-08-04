"""Whoosh-NG benchmark specifications.

This package defines the ``WhooshLikeSpec`` base class used by the
benchmark CLI runner (``python -m benchmark``) and provides the
``BenchmarkResult`` / ``BenchmarkReport`` helpers from ``reporting.py``.

Usage
-----

End-to-end indexing / search benchmarks (CLI):

    python -m benchmark --spec reuters --index --search --report csv
    python -m benchmark --spec dictionary --index --report json

Component benchmarks (pytest-benchmark):

    python -m pytest benchmark/ --benchmark-only
    --override-ini="norecursedirs="
    --override-ini="testpaths=benchmark"
    --override-ini="python_files=benchmark_*.py"

See each spec file for details on what it benchmarks.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from whoosh.support.bench import Spec


class WhooshLikeSpec(Spec):
    """Base class for end-to-end Whoosh indexing / search benchmark specs.

    Subclasses must define:

    * ``whoosh_schema()`` – return a :class:`whoosh.fields.Schema` instance.
    * ``documents()``    – yield document dicts to index.

    Optional class attributes:

    * ``name``            – human-readable spec name (used in report titles).
    * ``main_field``      – the main full-text field (default ``"body"``).
    * ``headline_field``  – field used for result snippets (default ``"title"``).
    * ``default_query``   – default search query string (default ``"test"``).
    * ``filename``        – name of a data file when loading from disk.
    """

    name: str = ""
    main_field: str = "body"
    headline_field: str = "title"
    default_query: str = "test"
    filename: str = ""

    def whoosh_schema(self):
        """Return the Whoosh :class:`~whoosh.fields.Schema` for this spec.

        Must be overridden by subclasses.
        """
        raise NotImplementedError("subclasses must implement whoosh_schema()")

    def documents(self):
        """Yield document dicts to be indexed.

        Must be overridden by subclasses.
        """
        raise NotImplementedError("subclasses must implement documents()")

    def batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
        """Yield batches of document dicts for efficient bulk indexing.

        Default implementation groups :meth:`documents` into lists of
        ``batch_size``. Subclasses should override this when they can
        read batches natively (e.g. from a DataSource with
        ``stream_batches()``).
        """
        batch: list[dict[str, Any]] = []
        for doc in self.documents():
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
