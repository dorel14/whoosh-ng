# Copyright 2025 Whoosh-NG contributors. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS
# IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Autocomplete prefix query support."""

from __future__ import annotations

from typing import Iterable, Sequence

from whoosh.query import qcore
from whoosh.query.terms import Prefix


class AutocompleteQuery(Prefix):
    """Matches documents that have terms starting with the given prefix.

    This is a thin, stable public wrapper around :class:`whoosh.query.terms.Prefix`
    so that autocomplete/prefix completion can be used without relying on
    internal query classes directly.
    """

    def __init__(self, fieldname: str, text: str, boost: float = 1.0) -> None:
        super().__init__(fieldname, text, boost=boost)


def suggestions(
    searcher,
    fieldname: str,
    prefix: str,
    *,
    limit: int = 5,
    scorer: str = "frequency",
) -> Sequence[str]:
    """Return completion suggestions for ``prefix`` from ``fieldname``.

    :param searcher: an open :class:`whoosh.searching.Searcher`.
    :param fieldname: the field to search for terms.
    :param prefix: the prefix to complete.
    :param limit: maximum number of suggestions to return.
    :param scorer: ``"frequency"`` to sort by term frequency, ``"alpha"``
        for alphabetical order.
    :returns: ordered sequence of suggestion strings.
    """
    q = AutocompleteQuery(fieldname, prefix)
    results = searcher.search(q, limit=limit, sortedby=fieldname if scorer == "alpha" else None)
    terms: Iterable[str] = (
        hit[fieldname] for hit in results if fieldname in hit
    )
    if scorer == "frequency":
        freq: dict[str, int] = {}
        for term in terms:
            freq[term] = freq.get(term, 0) + 1
        return sorted(freq.keys(), key=lambda t: (-freq[t], t))[:limit]
    return sorted(set(terms))[:limit]
