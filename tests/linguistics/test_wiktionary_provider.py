"""Tests for WiktionarySynonymProvider."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from whoosh_modern.linguistics.synonyms.wiktionary_provider import (
    WiktionarySynonymProvider,
)


class TestWiktionarySynonymProvider:
    def test_load_valid_dictionary(self):
        data = {
            "car": ["automobile", "vehicle"],
            "house": ["home", "residence"],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            for word, syns in data.items():
                f.write(json.dumps({"word": word, "pos": "noun", "s": syns}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert set(provider.get_synonyms("car")) == {"automobile", "vehicle"}
            assert set(provider.get_synonyms("house")) == {"home", "residence"}
        finally:
            os.unlink(path)

    def test_skip_words_with_spaces(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json.dumps({"word": "my car", "pos": "noun", "s": ["automobile"]}) + "\n")
            f.write(json.dumps({"word": "car", "pos": "noun", "s": ["automobile"]}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert provider.get_synonyms("my car") == []
            assert set(provider.get_synonyms("car")) == {"automobile"}
        finally:
            os.unlink(path)

    def test_skip_invalid_pos(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json.dumps({"word": "run", "pos": "suffix", "s": ["race"]}) + "\n")
            f.write(json.dumps({"word": "car", "pos": "noun", "s": ["automobile"]}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert provider.get_synonyms("run") == []
            assert set(provider.get_synonyms("car")) == {"automobile"}
        finally:
            os.unlink(path)

    def test_skip_missing_synonyms(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json.dumps({"word": "car", "pos": "noun"}) + "\n")
            f.write(json.dumps({"word": "house", "pos": "noun", "s": []}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert provider.get_synonyms("car") == []
            assert provider.get_synonyms("house") == []
        finally:
            os.unlink(path)

    def test_skip_empty_word(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json.dumps({"word": "", "pos": "noun", "s": ["x"]}) + "\n")
            f.write(json.dumps({"word": "car", "pos": "noun", "s": ["automobile"]}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert provider.get_synonyms("") == []
            assert set(provider.get_synonyms("car")) == {"automobile"}
        finally:
            os.unlink(path)

    def test_skip_invalid_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("not a json\n")
            f.write(json.dumps({"word": "car", "pos": "noun", "s": ["automobile"]}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert set(provider.get_synonyms("car")) == {"automobile"}
        finally:
            os.unlink(path)

    def test_multiple_entries_same_word_merged(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json.dumps({"word": "car", "pos": "noun", "s": ["automobile"]}) + "\n")
            f.write(json.dumps({"word": "car", "pos": "noun", "s": ["vehicle"]}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert set(provider.get_synonyms("car")) == {"automobile", "vehicle"}
        finally:
            os.unlink(path)

    def test_deduplicate_synonyms(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(json.dumps({"word": "car", "pos": "noun", "s": ["auto", "auto"]}) + "\n")
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert provider.get_synonyms("car") == ["auto"]
        finally:
            os.unlink(path)

    def test_antonyms_ignored(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                json.dumps(
                    {
                        "word": "car",
                        "pos": "noun",
                        "s": ["automobile"],
                        "n": ["bicycle"],
                    }
                )
                + "\n"
            )
            path = f.name
        try:
            provider = WiktionarySynonymProvider(path)
            assert set(provider.get_synonyms("car")) == {"automobile"}
            assert "bicycle" not in provider.get_synonyms("car")
        finally:
            os.unlink(path)
