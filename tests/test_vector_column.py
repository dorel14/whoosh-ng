"""Tests for VectorColumn and VECTOR field with native column storage."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from whoosh import fields
from whoosh.codec.whoosh3 import W3Codec
from whoosh.filedb.filestore import RamStorage
from whoosh.index import create_in
from whoosh_modern.fields.vector import VECTOR

pytest.importorskip("numpy")


def _build_index(tmp_path: Any) -> Any:
    idx_dir = tmp_path / "index"
    idx_dir.mkdir()
    schema = fields.Schema(
        id=fields.TEXT(stored=True),
        embedding=VECTOR(dimension=4, dtype="float32", normalized=True),
    )
    ix = create_in(str(idx_dir), schema)
    writer = ix.writer()
    writer.add_document(id="doc1", embedding=[1.0, 0.0, 0.0, 0.0])
    writer.add_document(id="doc2", embedding=[0.0, 1.0, 0.0, 0.0])
    writer.add_document(id="doc3", embedding=[0.707, 0.707, 0.0, 0.0])
    writer.commit()
    return ix


class TestVectorColumn:
    def test_has_column(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            assert r.has_column("embedding")

    def test_column_reader_returns_bytes(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            cr = r.column_reader("embedding", translate=False)
            raw = cr[0]
            assert isinstance(raw, bytes)
            assert len(raw) == 16  # 4 * float32

    def test_column_reader_translated_returns_ndarray(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            cr = r.column_reader("embedding", translate=True)
            vec = cr[0]
            assert isinstance(vec, np.ndarray)
            assert vec.dtype == np.float32
            assert vec.shape == (4,)

    def test_vector_values_match(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            cr = r.column_reader("embedding", translate=True)
            v0 = cr[0]
            v1 = cr[1]
            v2 = cr[2]
            assert pytest.approx(v0[0], abs=1e-6) == 1.0
            assert pytest.approx(v1[1], abs=1e-6) == 1.0
            expected = 1.0 / np.sqrt(2)
            assert pytest.approx(v2[0], abs=1e-5) == expected
            assert pytest.approx(v2[1], abs=1e-5) == expected

    def test_default_vector_for_missing_doc(self, tmp_path: Any) -> None:
        ix = _build_index(tmp_path)
        reader = ix.reader()
        assert reader is not None
        with reader as r:
            cr = r.column_reader("embedding", translate=True)
            n_docs = r.doc_count_all()
            for docnum in range(n_docs):
                vec = cr[docnum]
                assert isinstance(vec, np.ndarray)
                assert vec.shape == (4,)

    def test_vector_field_to_column_value(self) -> None:
        field = VECTOR(dimension=3, dtype="float32", normalized=True)
        value = field.to_column_value([1.0, 0.0, 0.0])
        assert isinstance(value, bytes)
        assert len(value) == 12  # 3 * float32

    def test_vector_field_from_column_value(self) -> None:
        field = VECTOR(dimension=3, dtype="float32")
        raw = field.to_column_value([1.0, 2.0, 3.0])
        arr = field.from_column_value(raw)
        assert isinstance(arr, np.ndarray)
        assert arr.dtype == np.float32
        assert list(arr) == pytest.approx([1.0, 2.0, 3.0])

    def test_vector_field_normalized(self) -> None:
        field = VECTOR(dimension=2, dtype="float32", normalized=True)
        raw = field.to_column_value([3.0, 4.0])
        arr = np.frombuffer(raw, dtype=np.float32)
        norm = float(np.linalg.norm(arr))
        assert pytest.approx(norm, abs=1e-6) == 1.0

    def test_unsupported_dtype_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported dtype"):
            VECTOR(dimension=4, dtype="float64")
