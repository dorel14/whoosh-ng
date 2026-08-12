"""Update Wiktionary dictionaries from kaikki.org.

Downloads ``kaikki.org-dictionary-all.jsonl`` from https://kaikki.org/,
extracts dictionary entries by language, and writes compact per-language
JSON Lines files into ``src/whoosh_modern/linguistics/dictionaries/wiktionary/``.

Each output line contains:

    {
        "word": "<headword>",
        "lang": "<lang_code>",
        "pos": "<part_of_speech>",
        "s": ["<synonym>", ...],
        "n": ["<antonym>", ...],
        "definition": "<gloss text>",
        "forms": ["<inflection>", ...]
    }

Usage::

    # Update a single language
    python scripts/update_wiktionary_dictionaries.py --lang fr

    # Update all supported languages
    python scripts/update_wiktionary_dictionaries.py --all

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

KAIKKI_URL = "https://kaikki.org/dictionary/kaikki.org-dictionary-all.jsonl"
DICTIONARIES_DIR = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    "src",
    "whoosh_modern",
    "linguistics",
    "dictionaries",
    "wiktionary",
)
MANIFEST_PATH = os.path.join(DICTIONARIES_DIR, "manifest.json")

SUPPORTED_LANGS: dict[str, str] = {
    "fr": "French",
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
}

_ALLOWED_POS: frozenset[str] = frozenset(
    {
        "noun",
        "verb",
        "adjective",
        "adverb",
        "proper noun",
        "preposition",
        "conjunction",
        "interjection",
        "article",
        "determiner",
        "pronoun",
    }
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update Wiktionary synonym dictionaries from kaikki.org."
    )
    parser.add_argument(
        "--lang",
        choices=list(SUPPORTED_LANGS.keys()),
        help="Update only the specified language code.",
    )
    parser.add_argument(
        "--all",
        dest="update_all",
        action="store_true",
        help="Update all supported languages.",
    )
    parser.add_argument(
        "--source",
        default=KAIKKI_URL,
        help=f"URL or local path to the kaikki.org JSONL file (default: {KAIKKI_URL}).",
    )
    parser.add_argument(
        "--output-dir",
        default=DICTIONARIES_DIR,
        help=f"Output directory for dictionary files (default: {DICTIONARIES_DIR}).",
    )
    return parser.parse_args()


def _stream_jsonl(source: str):
    """Yield parsed JSON objects from a JSON Lines source.

    Args:
        source: URL or local file path to a JSON Lines file.

    Yields:
        Parsed JSON objects, one per non-empty line.
    """
    if source.startswith("http://") or source.startswith("https://"):
        import urllib.request

        logger.info("Downloading %s ...", source)
        with urllib.request.urlopen(source) as response:
            for raw_line in response:
                raw_line = raw_line.decode("utf-8").strip()
                if not raw_line:
                    continue
                yield json.loads(raw_line)
    else:
        logger.info("Reading local file %s", source)
        with open(source, encoding="utf-8") as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                yield json.loads(raw_line)


def _extract_synonyms(entry: dict[str, Any]) -> tuple[str, str, list[str]] | None:
    """Extract a single (word, lang, synonyms) triple from a kaikki.org entry.

    Args:
        entry: A parsed JSON object from the kaikki.org JSON Lines file.

    Returns:
        A tuple of (word, lang_code, synonyms) or None if the entry should
        be skipped.
    """
    word = entry.get("word")
    lang = entry.get("lang")
    pos = entry.get("pos")
    synonyms = entry.get("s")

    if not word or not isinstance(word, str):
        return None

    if " " in word:
        return None

    if lang not in SUPPORTED_LANGS:
        return None

    if pos not in _ALLOWED_POS:
        return None

    if not synonyms or not isinstance(synonyms, list):
        return None

    clean_synonyms = [str(s) for s in synonyms if isinstance(s, str) and s and " " not in s]
    if not clean_synonyms:
        return None

    return str(word), str(lang), clean_synonyms


def _update_language(lang: str, output_dir: str, source: str) -> dict[str, Any]:
    """Process the JSONL source and write the synonym file for ``lang``.

    Args:
        lang: Two-letter language code (e.g. ``"fr"``).
        output_dir: Directory where the per-language file will be written.
        source: URL or local path to the kaikki.org JSONL file.

    Returns:
        A manifest entry dict for the language.
    """
    output_path = os.path.join(output_dir, f"{lang}.json")
    word_map: dict[str, list[str]] = {}
    entry_count = 0
    skipped_count = 0

    for entry in _stream_jsonl(source):
        result = _extract_synonyms(entry)
        if result is None:
            skipped_count += 1
            continue
        word, entry_lang, synonyms = result
        if entry_lang != lang:
            skipped_count += 1
            continue
        if word not in word_map:
            word_map[word] = []
        word_map[word].extend(synonyms)
        entry_count += 1

    # Deduplicate synonyms per word
    deduped = {word: sorted(set(syns)) for word, syns in word_map.items()}

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for word, syns in deduped.items():
            f.write(json.dumps({"word": word, "s": syns}, ensure_ascii=False) + "\n")

    logger.info(
        "Wrote %d entries to %s (%d skipped)",
        len(deduped),
        output_path,
        skipped_count,
    )

    file_size = os.path.getsize(output_path)
    return {
        "lang": lang,
        "name": SUPPORTED_LANGS[lang],
        "file": f"{lang}.json",
        "entries": len(deduped),
        "size_bytes": file_size,
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _write_manifest(manifest: dict[str, Any], output_dir: str) -> None:
    """Write the manifest JSON file.

    Args:
        manifest: The full manifest dict.
        output_dir: Directory where ``manifest.json`` will be written.
    """
    path = os.path.join(output_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    logger.info("Wrote manifest to %s", path)


def main() -> None:
    """Entry point: update Wiktionary dictionaries."""
    args = _parse_args()

    if not args.lang and not args.update_all:
        raise SystemExit("Error: --lang or --all must be specified.")

    target_langs = list(SUPPORTED_LANGS.keys()) if args.update_all else [args.lang]
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    manifest: dict[str, Any] = {
        "source": args.source,
        "generated_at": datetime.now(UTC).isoformat(),
        "languages": {},
    }

    for lang in target_langs:
        logger.info("Updating %s (%s) ...", lang, SUPPORTED_LANGS[lang])
        entry = _update_language(lang, output_dir, args.source)
        manifest["languages"][lang] = entry

    _write_manifest(manifest, output_dir)
    logger.info("Done. Updated %d language(s).", len(target_langs))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
