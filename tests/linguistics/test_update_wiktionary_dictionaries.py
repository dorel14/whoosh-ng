"""Tests for the Wiktionary dictionary update script."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

from whoosh_modern.linguistics.synonyms.wiktionary_provider import WiktionarySynonymProvider

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUpdateWiktionaryDictionaries:
    def test_update_single_language_local_file(self):
        source_data = [
            {"word": "voiture", "lang": "fr", "pos": "noun", "s": ["automobile"]},
            {"word": "house", "lang": "en", "pos": "noun", "s": ["home"]},
            {"word": "auto", "lang": "de", "pos": "noun", "s": ["wagen"]},
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as src:
            for entry in source_data:
                src.write(json.dumps(entry) + "\n")
            source_path = src.name

        with tempfile.TemporaryDirectory() as output_dir:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "scripts/update_wiktionary_dictionaries.py",
                        "--lang",
                        "fr",
                        "--source",
                        source_path,
                        "--output-dir",
                        output_dir,
                    ],
                    capture_output=True,
                    text=True,
                    cwd=REPO_ROOT,
                )
                assert result.returncode == 0, result.stderr

                fr_path = os.path.join(output_dir, "fr.json")
                assert os.path.exists(fr_path)

                provider = WiktionarySynonymProvider(fr_path)
                assert set(provider.get_synonyms("voiture")) == {"automobile"}

                manifest_path = os.path.join(output_dir, "manifest.json")
                assert os.path.exists(manifest_path)
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                assert "fr" in manifest["languages"]
            finally:
                os.unlink(source_path)

    def test_update_all_languages(self):
        source_data = [
            {"word": "voiture", "lang": "fr", "pos": "noun", "s": ["automobile"]},
            {"word": "house", "lang": "en", "pos": "noun", "s": ["home"]},
            {"word": "auto", "lang": "de", "pos": "noun", "s": ["wagen"]},
            {"word": "coche", "lang": "es", "pos": "noun", "s": ["automóvil"]},
            {"word": "auto", "lang": "it", "pos": "noun", "s": ["automobile"]},
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as src:
            for entry in source_data:
                src.write(json.dumps(entry) + "\n")
            source_path = src.name

        with tempfile.TemporaryDirectory() as output_dir:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "scripts/update_wiktionary_dictionaries.py",
                        "--all",
                        "--source",
                        source_path,
                        "--output-dir",
                        output_dir,
                    ],
                    capture_output=True,
                    text=True,
                    cwd=REPO_ROOT,
                )
                assert result.returncode == 0, result.stderr

                for lang in ("fr", "en", "de", "es", "it"):
                    path = os.path.join(output_dir, f"{lang}.json")
                    assert os.path.exists(path), f"Missing {lang}.json"

                manifest_path = os.path.join(output_dir, "manifest.json")
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                assert set(manifest["languages"].keys()) == {"fr", "en", "de", "es", "it"}
            finally:
                os.unlink(source_path)
