from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from whoosh.support.levenshtein import damerau_levenshtein, distance, levenshtein, relative
from whoosh.util.loading import RenamingUnpickler, find_object
from whoosh.util.text import byte, first_diff, prefix_encode, rcompile
from whoosh.util.varints import (
    decode_signed_varint,
    read_varint,
    signed_varint,
    varint,
    varint_to_int,
)

CLEANED_FILES = [
    Path("src/whoosh/util/varints.py"),
    Path("src/whoosh/util/text.py"),
    Path("src/whoosh/util/loading.py"),
    Path("src/whoosh/support/levenshtein.py"),
]


class TestVarints:
    def test_roundtrip_small(self):
        for i in range(1000):
            assert varint_to_int(varint(i)) == i

    def test_signed_roundtrip(self):
        for i in (-100, -1, 0, 1, 100):
            assert decode_signed_varint(varint_to_int(signed_varint(i))) == i

    def test_read_varint(self):
        buf = varint(42)
        idx = 0

        def readfn(n):
            nonlocal idx
            chunk = buf[idx : idx + n]
            idx += n
            return chunk

        assert read_varint(readfn) == 42


class TestText:
    def test_byte(self):
        assert byte(0) == b"\x00"
        assert byte(255) == b"\xff"

    def test_first_diff(self):
        assert first_diff(b"abc", b"abd") == 2
        assert first_diff(b"abc", b"abc") == 3

    def test_prefix_encode(self):
        assert prefix_encode(b"abc", b"abd") == b"\x02d"

    def test_rcompile_string(self):
        p = rcompile(r"\d+")
        m = p.match("123")
        assert m is not None
        assert m.group() == "123"

    def test_rcompile_compiled(self):
        p = rcompile(r"\d+")
        assert rcompile(p) is p


class TestLoading:
    def test_find_object(self):
        cls = find_object("whoosh.util.text.rcompile")
        assert callable(cls)


class TestLevenshtein:
    def test_levenshtein_identical(self):
        assert levenshtein("abc", "abc") == 0

    def test_levenshtein_different(self):
        assert levenshtein("abc", "abd") == 1

    def test_damerau_levenshtein_transposition(self):
        assert damerau_levenshtein("ab", "ba") == 1

    def test_distance_alias(self):
        assert distance("abc", "abc") == 0

    def test_relative(self):
        assert relative("abc", "abc") == 1.0


class TestLegacyCleanupTypecheck:
    @pytest.mark.parametrize("path", CLEANED_FILES)
    def test_pyright_clean(self, path: Path):
        result = subprocess.run(
            ["uv", "run", "pyright", str(path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        assert result.returncode == 0, (
            f"pyright errors on {path}:\n{result.stdout}\n{result.stderr}"
        )

    @pytest.mark.parametrize("path", CLEANED_FILES)
    def test_mypy_clean(self, path: Path):
        result = subprocess.run(
            ["uv", "run", "mypy", str(path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        assert result.returncode == 0, f"mypy errors on {path}:\n{result.stdout}\n{result.stderr}"
