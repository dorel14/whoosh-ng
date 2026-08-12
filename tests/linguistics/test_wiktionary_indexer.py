"""Tests for WiktionaryIndexer."""

from __future__ import annotations

import os

import pytest

from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

_DICT_DIR = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    "src",
    "whoosh_modern",
    "linguistics",
    "dictionaries",
    "wiktionary",
)


class TestWiktionaryIndexer:
    def test_build_and_search_basic(self, tmp_path):
        source = JSONSource(os.path.join(_DICT_DIR, "fr.json"))
        index_dir = str(tmp_path / "index")
        indexer = WiktionaryIndexer(index_dir)
        count = indexer.build_index(source, language="fr")
        assert count > 0

        results = indexer.search("véhicule", language="fr", limit=5)
        assert len(results) > 0
        assert results[0]["word"] == "voiture"
        assert results[0]["language"] == "fr"

    def test_language_filter(self, tmp_path):
        source = JSONSource(os.path.join(_DICT_DIR, "en.json"))
        index_dir = str(tmp_path / "index")
        indexer = WiktionaryIndexer(index_dir)
        indexer.build_index(source, language="en")

        results = indexer.search("habitation", language="en", limit=5)
        assert all(r["language"] == "en" for r in results)

    def test_search_returns_metadata(self, tmp_path):
        source = JSONSource(os.path.join(_DICT_DIR, "fr.json"))
        index_dir = str(tmp_path / "index")
        indexer = WiktionaryIndexer(index_dir)
        indexer.build_index(source, language="fr")
        results = indexer.search("véhicule", language="fr", limit=1)
        assert len(results) == 1
        hit = results[0]
        assert "word" in hit
        assert "definition" in hit
        assert "language" in hit
        assert "score" in hit

    def test_no_results_for_unknown_query(self, tmp_path):
        source = JSONSource(os.path.join(_DICT_DIR, "fr.json"))
        index_dir = str(tmp_path / "index")
        indexer = WiktionaryIndexer(index_dir)
        indexer.build_index(source, language="fr")
        results = indexer.search("zzzzzz_not_in_dict", language="fr", limit=5)
        assert results == []

    def test_build_index_all_languages(self, tmp_path):
        source = JSONSource(os.path.join(_DICT_DIR, "en.json"))
        index_dir = str(tmp_path / "index")
        indexer = WiktionaryIndexer(index_dir)
        count = indexer.build_index(source)
        assert count > 0
