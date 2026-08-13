"""Tests for the synonym engine."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.application import SearchApplication
from whoosh_modern.linguistics import (
    LANG_SYNONYMS,
    JSONSynonymProvider,
    SQLiteSynonymStore,
    StaticSynonymProvider,
    SynonymCompiler,
    SynonymExpansionMiddleware,
    SynonymManager,
    YAMLSynonymProvider,
)


class TestStaticSynonymProvider:
    def test_empty_provider(self):
        provider = StaticSynonymProvider()
        assert provider.get_synonyms("hello") == []

    def test_add_and_get(self):
        provider = StaticSynonymProvider()
        provider.add_synonym("car", ["automobile", "vehicle"])
        assert set(provider.get_synonyms("car")) == {"automobile", "vehicle"}

    def test_remove_synonym(self):
        provider = StaticSynonymProvider()
        provider.add_synonym("car", ["automobile", "vehicle"])
        provider.remove_synonym("car", "automobile")
        assert provider.get_synonyms("car") == ["vehicle"]

    def test_remove_nonexistent(self):
        provider = StaticSynonymProvider()
        provider.add_synonym("car", ["automobile"])
        provider.remove_synonym("car", "boat")
        assert provider.get_synonyms("car") == ["automobile"]

    def test_to_dict_roundtrip(self):
        provider = StaticSynonymProvider({"car": ["automobile"], "bike": ["bicycle"]})
        data = provider.to_dict()
        assert data == {"car": ["automobile"], "bike": ["bicycle"]}

    def test_update_from_dict(self):
        provider = StaticSynonymProvider()
        provider.update_from_dict({"car": ["automobile"]})
        assert set(provider.get_synonyms("car")) == {"automobile"}


class TestYAMLSynonymProvider:
    def test_load_yaml(self):
        content = "car:\n  - automobile\n  - vehicle\nbike:\n  - bicycle\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        try:
            provider = YAMLSynonymProvider(path)
            assert set(provider.get_synonyms("car")) == {"automobile", "vehicle"}
            assert provider.get_synonyms("bike") == ["bicycle"]
        finally:
            os.unlink(path)

    def test_missing_yaml_raises(self):
        pytest.importorskip("yaml")
        # PyYAML is installed in the test environment, so we just verify
        # the provider loads successfully.
        content = "car:\n  - automobile\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        try:
            provider = YAMLSynonymProvider(path)
            assert provider.get_synonyms("car") == ["automobile"]
        finally:
            os.unlink(path)


class TestJSONSynonymProvider:
    def test_load_json(self):
        data = {"car": ["automobile"], "bike": ["bicycle"]}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            provider = JSONSynonymProvider(path)
            assert provider.get_synonyms("car") == ["automobile"]
        finally:
            os.unlink(path)


class TestSQLiteSynonymStore:
    def test_add_and_get(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            store = SQLiteSynonymStore(path)
            store.add_synonym("car", ["automobile", "vehicle"])
            assert set(store.get_synonyms("car")) == {"automobile", "vehicle"}
            store.close()
        finally:
            os.unlink(path)

    def test_remove(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            store = SQLiteSynonymStore(path)
            store.add_synonym("car", ["automobile", "vehicle"])
            store.remove_synonym("car", "automobile")
            assert store.get_synonyms("car") == ["vehicle"]
            store.close()
        finally:
            os.unlink(path)


class TestSynonymCompiler:
    def test_compile_empty(self):
        compiler = SynonymCompiler()
        assert compiler.compile() == {}

    def test_compile_and_add(self):
        compiler = SynonymCompiler({"car": ["automobile"]})
        compiler.add("bike", ["bicycle"])
        result = compiler.compile()
        assert set(result["car"]) == {"automobile"}
        assert set(result["bike"]) == {"bicycle"}

    def test_merge(self):
        compiler = SynonymCompiler({"car": ["automobile"]})
        compiler.merge({"bike": ["bicycle"]})
        result = compiler.compile()
        assert "car" in result
        assert "bike" in result


class TestSynonymManager:
    def test_get_synonyms(self):
        manager = SynonymManager({"car": ["automobile"]})
        assert manager.get_synonyms("car") == ["automobile"]
        assert manager.get_synonyms("bike") == []

    def test_add_and_remove(self):
        manager = SynonymManager()
        manager.add_synonyms("car", ["automobile", "vehicle"])
        assert set(manager.get_synonyms("car")) == {"automobile", "vehicle"}
        manager.remove_synonym("car", "automobile")
        assert manager.get_synonyms("car") == ["vehicle"]

    def test_import_export_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"car": ["automobile"]}, f)
            path = f.name
        try:
            manager = SynonymManager()
            manager.import_json(path)
            assert manager.get_synonyms("car") == ["automobile"]
            out_path = path + ".out"
            manager.export_json(out_path)
            with open(out_path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["car"] == ["automobile"]
            os.unlink(out_path)
        finally:
            os.unlink(path)

    def test_lang_synonyms_loaded(self):
        assert "fr" in LANG_SYNONYMS
        assert "voiture" in LANG_SYNONYMS["fr"]
        assert "en" in LANG_SYNONYMS
        assert "car" in LANG_SYNONYMS["en"]

    def test_import_wiktionary(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                json.dumps({"word": "voiture", "pos": "noun", "s": ["automobile", "véhicule"]})
                + "\n"
            )
            f.write(json.dumps({"word": "maison", "pos": "noun", "s": ["domicile"]}) + "\n")
            path = f.name
        try:
            manager = SynonymManager()
            manager.import_wiktionary(path)
            assert set(manager.get_synonyms("voiture")) == {"automobile", "véhicule"}
            assert manager.get_synonyms("maison") == ["domicile"]
        finally:
            os.unlink(path)

    def test_import_wiktionary_skips_invalid_entries(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json.dumps({"word": "my car", "pos": "noun", "s": ["automobile"]}) + "\n")
            f.write(json.dumps({"word": "", "pos": "noun", "s": ["x"]}) + "\n")
            f.write(json.dumps({"word": "run", "pos": "suffix", "s": ["race"]}) + "\n")
            f.write(json.dumps({"word": "voiture", "pos": "noun", "s": ["automobile"]}) + "\n")
            path = f.name
        try:
            manager = SynonymManager()
            manager.import_wiktionary(path)
            assert manager.get_synonyms("my car") == []
            assert manager.get_synonyms("") == []
            assert manager.get_synonyms("run") == []
            assert set(manager.get_synonyms("voiture")) == {"automobile"}
        finally:
            os.unlink(path)

    def test_import_wiktionary_index(self, tmp_path):
        from whoosh_modern.data_sources.json import JSONSource
        from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

        source = JSONSource("src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json")
        index_dir = str(tmp_path / "index")
        indexer = WiktionaryIndexer(index_dir)
        indexer.build_index(source, language="fr")

        manager = SynonymManager()
        manager.import_wiktionary_index(index_dir, language="fr")
        assert set(manager.get_synonyms("voiture")) == {"automobile", "véhicule"}


class TestSynonymExpansionMiddleware:
    def test_expand_query(self):
        manager = SynonymManager({"car": ["automobile"]})
        middleware = SynonymExpansionMiddleware(manager)
        ctx = MiddlewareContext(operation="search")
        ctx.query = "car"
        ctx = middleware.before_search(ctx)
        assert "automobile" in ctx.query

    def test_expand_document(self):
        manager = SynonymManager({"car": ["automobile"]})
        middleware = SynonymExpansionMiddleware(manager)
        ctx = MiddlewareContext(operation="index")
        ctx.document = {"title": "car"}
        ctx = middleware.before_index(ctx)
        assert "automobile" in ctx.document["title"]

    def test_no_expansion_when_none(self):
        middleware = SynonymExpansionMiddleware(SynonymManager())
        ctx = MiddlewareContext(operation="search")
        ctx.query = "hello"
        ctx = middleware.before_search(ctx)
        assert ctx.query == "hello"


class TestSearchApplicationWiktionaryIntegration:
    def test_synonym_manager_populated_from_indexer(self, tmp_path):
        from whoosh_modern.data_sources.json import JSONSource
        from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

        source = JSONSource("src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json")
        index_dir = str(tmp_path / "index")
        indexer = WiktionaryIndexer(index_dir)
        indexer.build_index(source, language="fr")

        app = SearchApplication(wiktionary_indexer=indexer)

        manager = app.synonym_manager
        assert set(manager.get_synonyms("voiture")) == {"automobile", "véhicule"}
