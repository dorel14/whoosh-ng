---
title: "Legacy Code Cleanup Strategy"
nav_order: 60
---

# Legacy Code Cleanup Strategy

This guide explains how Whoosh-NG separates modern typed code from legacy code,
and how the legacy cleanup is progressing.

## Why a legacy boundary?

`whoosh-modern` is the new, fully typed surface of Whoosh-NG.
The original `whoosh` package still works at runtime, but it carries decades of
Python 2/3 compatibility patterns, dynamic metaprogramming, and untyped internals.
Trying to force strict types on all of it at once would block development.

The cleanup strategy is **incremental and opt-in**:

1. `src/whoosh_modern/` is typed and linted with `pyright` and `mypy` strict.
2. `src/whoosh/` is the legacy surface. It is split into:
   - **excluded modules** (documented in `pyrightconfig.json`) — code that is too
     dynamic or vendored for an economical type pass right now;
   - **cleanup candidates** — small, isolated files that are straightforward to
     annotate and verify.
3. Each sprint, a wave of candidates is typed, tested, and promoted out of the
   high-tolerance zone.

## Current pyright/mypy thresholds (Sprint 2)

| Checker | Scope | Threshold |
|---------|-------|-----------|
| `pyright` | `src/whoosh_modern/` | **0 errors** (strict) |
| `pyright` | legacy | **≤ 500 errors** (tolerant) |
| `mypy` | `src/` | **0 errors** (via overrides + `ignore_errors`) |

## Exclusion rationale (pyrightconfig.json)

The `exclude` list in `pyrightconfig.json` groups excluded files by theme:

- **Vendored / no stubs**: `pyparsing.py`, `relativedelta.py`
- **Migration shims**: `codec/whoosh2.py`, `codec/whoosh3.py`
- **Dynamic parsing**: `qparser/`, `query/`, `analysis/`, `automata/`
- **Large datastores**: `filedb/`, `reading/`, `writing/`
- **Heuristic / data-driven**: `lang/dmetaphone.py`, `lang/lovins.py`,
  `lang/phonetic.py`, `lang/wordnet.py`
- **Core dynamic objects**: `classify.py`, `index.py`, `locking.py`,
  `formats.py`, `middleware/`
- **Vendored low-level**: `support/bench.py`, `support/base85.py`,
  `support/bitstream.py`, `support/bitvector.py`, `support/charset.py`,
  `support/levenshtein.py`

## Sprint 2 cleanup plan

For Sprint 2, the focus is on small utility and support modules that have few
external dependencies and no heavy metaprogramming.

Candidate wave:

- `src/whoosh/util/varints.py`
- `src/whoosh/util/text.py`
- `src/whoosh/util/loading.py`
- `src/whoosh/support/bitstream.py`
- `src/whoosh/support/levenshtein.py`

For each file:

1. Remove the blanket `# type: ignore` (if present).
2. Add precise function signatures.
3. Run `pyright` and `mypy` to confirm **0 new errors**.
4. Move the file out of `pyrightconfig.json` excludes.
5. Add a regression test in `tests/test_legacy_cleanup.py`.

## Long-term goal

Eventually every file in `src/whoosh/` should be checkable by `mypy` and
`pyright` without blanket excludes. Until then, the exclude list is the
explicit ledger of debt, and each sprint chips away at it.
