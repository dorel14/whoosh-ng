"""Wiktionary dictionary indexer for full-text search.

Builds a Whoosh-NG index from a DataSource implementing the
``DataSource`` protocol, enabling full-text search over definitions,
synonyms, antonyms, and forms with language and part-of-speech filtering.

Typical usage with the bundled JSON Lines dictionaries::

    from whoosh_modern.data_sources import JSONSource
    from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

    source = JSONSource("src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json")
    indexer = WiktionaryIndexer("indexdir")
    indexer.build_index(source, language="fr")

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
from typing import Any

from whoosh.fields import ID, KEYWORD, TEXT, Schema
from whoosh.index import create_in, exists_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.searching import Searcher
from whoosh_modern.data_sources import DataSource

logger = logging.getLogger(__name__)

_WIKTIONARY_SCHEMA = Schema(
    word=ID(stored=True, unique=True),
    definition=TEXT(stored=True),
    synonyms=KEYWORD(stored=True, scorable=False),
    antonyms=KEYWORD(stored=True, scorable=False),
    forms=KEYWORD(stored=True, scorable=False),
    pos=KEYWORD(stored=True, scorable=False),
    language=KEYWORD(stored=True, scorable=False),
)


class WiktionaryIndexer:
    """Index a Wiktionary dictionary for full-text search.

    Wraps any ``DataSource`` implementation and builds a Whoosh-NG index
    with a fixed Wiktionary schema. Documents are expected to expose at
    least ``word``, ``lang``, ``pos``, ``s``, ``n``, ``definition``,
    and ``forms`` keys as produced by
    ``update_wiktionary_dictionaries.py``.

    Args:
        index_dir: Filesystem directory where the Whoosh index will be
            created or opened.
    """

    def __init__(self, index_dir: str) -> None:
        """Initialize the indexer.

        Args:
            index_dir: Directory path for the Whoosh index.
        """
        self._index_dir = index_dir
        self._index: Any = None

    def build_index(self, source: DataSource, language: str | None = None) -> int:
        """Build the Whoosh index from a DataSource.

        Creates or recreates the index in ``index_dir`` and indexes every
        document yielded by ``source.iter_documents()`` whose ``lang``
        matches ``language`` (or all entries if ``language`` is ``None``).

        Args:
            source: DataSource yielding document dicts with Wiktionary
                fields.
            language: Optional two-letter language code filter
                (e.g. ``"fr"``). If ``None``, all languages are indexed.

        Returns:
            Number of documents indexed.
        """
        os.makedirs(self._index_dir, exist_ok=True)
        if exists_in(self._index_dir):
            self._index = open_dir(self._index_dir)
            writer = self._index.writer()
        else:
            self._index = create_in(self._index_dir, _WIKTIONARY_SCHEMA)
            writer = self._index.writer()

        indexed = 0
        for doc in source.iter_documents():
            entry_lang = str(doc.get("lang", ""))
            if language and entry_lang != language:
                continue

            word = doc.get("word")
            if not word:
                continue

            pos = doc.get("pos") or ""
            synonyms = doc.get("s") or []
            antonyms = doc.get("n") or []
            definition = doc.get("definition") or ""
            forms = doc.get("forms") or []

            writer.add_document(
                word=str(word),
                definition=str(definition),
                synonyms=" ".join(str(s) for s in synonyms),
                antonyms=" ".join(str(a) for a in antonyms),
                forms=" ".join(str(f) for f in forms),
                pos=str(pos),
                language=entry_lang,
            )
            indexed += 1

        writer.commit()
        logger.info("Indexed %d entries into %s", indexed, self._index_dir)
        return indexed

    def search(
        self,
        query: str,
        language: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search the built index.

        Args:
            query: Search query string matched against ``definition``.
            language: Optional language filter. If provided, results are
                restricted to this language code.
            limit: Maximum number of results to return.

        Returns:
            A list of result dicts with at least ``word``, ``definition``,
            ``language``, and ``score``.
        """
        if self._index is None:
            self._index = open_dir(self._index_dir)

        results: list[dict[str, Any]] = []
        with self._index.searcher() as searcher:
            parser = QueryParser("definition", self._index.schema)
            parsed = parser.parse(query)
            hits = searcher.search(parsed, limit=limit)

            for hit in hits:
                result: dict[str, Any] = {
                    "word": hit["word"],
                    "definition": hit["definition"],
                    "language": hit["language"],
                    "score": hit.score,
                }
                if language and result["language"] != language:
                    continue
                for field in ("synonyms", "antonyms", "forms", "pos"):
                    if field in hit:
                        result[field] = hit[field]
                results.append(result)

        return results

    def iter_documents(self, language: str | None = None) -> list[dict[str, Any]]:
        """Iterate over all indexed documents.

        Args:
            language: Optional language filter.

        Returns:
            A list of document dicts from the index.
        """
        if self._index is None:
            self._index = open_dir(self._index_dir)

        documents: list[dict[str, Any]] = []
        with self._index.searcher() as searcher:
            for hit in searcher.documents():
                entry_lang = hit.get("language", "")
                if language and entry_lang != language:
                    continue
                doc: dict[str, Any] = {
                    "word": hit["word"],
                    "definition": hit["definition"],
                    "language": entry_lang,
                    "pos": hit.get("pos", ""),
                }
                for field in ("synonyms", "antonyms", "forms"):
                    raw_value = hit.get(field, "")
                    if raw_value:
                        doc[field] = raw_value.split()
                documents.append(doc)

        return documents
