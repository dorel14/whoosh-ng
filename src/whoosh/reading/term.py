# Copyright 2007 Matt Chaput. All rights reserved.
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
# THIS SOFTWARE IS PROVIDED BY MATT CHAPUT ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL MATT CHAPUT OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Matt Chaput.
"""Term information and multi-cursor helpers."""

from abc import abstractmethod
from bisect import bisect_right
from heapq import heapify, heappop, heapreplace, nlargest
from math import log

from cached_property import cached_property
from whoosh import columns
from whoosh.filedb.filestore import OverlayStorage
from whoosh.matching import MultiMatcher
from whoosh.support.levenshtein import distance
from whoosh.system import emptybytes

class TermInfo:
    """Represents a set of statistics about a term. This object is returned by
    :meth:`IndexReader.term_info`. These statistics may be useful for
    optimizations and scoring algorithms.
    """

    def __init__(
        self,
        weight=0,
        df=0,
        minlength=None,
        maxlength=0,
        maxweight=0,
        minid=None,
        maxid=0,
    ):
        self._weight = weight
        self._df = df
        self._minlength = minlength
        self._maxlength = maxlength
        self._maxweight = maxweight
        self._minid = minid
        self._maxid = maxid

    def add_posting(self, docnum, weight, length=None):
        if self._minid is None:
            self._minid = docnum
        self._maxid = docnum
        self._weight += weight
        self._df += 1
        self._maxweight = max(self._maxweight, weight)

        if length is not None:
            if self._minlength is None:
                self._minlength = length
            else:
                self._minlength = min(self._minlength, length)
            self._maxlength = max(self._maxlength, length)

    def weight(self):
        """Returns the total frequency of the term across all documents."""

        return self._weight

    def doc_frequency(self):
        """Returns the number of documents the term appears in."""

        return self._df

    def min_length(self):
        """Returns the length of the shortest field value the term appears
        in.
        """

        return self._minlength

    def max_length(self):
        """Returns the length of the longest field value the term appears
        in.
        """

        return self._maxlength

    def max_weight(self):
        """Returns the number of times the term appears in the document in
        which it appears the most.
        """

        return self._maxweight

    def min_id(self):
        """Returns the lowest document ID this term appears in."""

        return self._minid

    def max_id(self):
        """Returns the highest document ID this term appears in."""

        return self._maxid

def combine_terminfos(tis):
    if len(tis) == 1:
        ti, offset = tis[0]
        ti._minid += offset
        ti._maxid += offset
        return ti

    # Combine the various statistics
    w = sum(ti.weight() for ti, _ in tis)
    df = sum(ti.doc_frequency() for ti, _ in tis)
    ml = min(ti.min_length() for ti, _ in tis)
    xl = max(ti.max_length() for ti, _ in tis)
    xw = max(ti.max_weight() for ti, _ in tis)

    # For min and max ID, we need to add the doc offsets
    mid = min(ti.min_id() + offset for ti, offset in tis)
    xid = max(ti.max_id() + offset for ti, offset in tis)

    return TermInfo(w, df, ml, xl, xw, mid, xid)

class MultiCursor:
    def __init__(self, cursors):
        self._cursors = [c for c in cursors if c.is_valid()]
        self._low = []
        self._text = None
        self.next()

    def _find_low(self):
        low = []
        lowterm = None

        for c in self._cursors:
            if c.is_valid():
                cterm = c.term()
                if low and cterm == lowterm:
                    low.append(c)
                elif low and cterm < lowterm:
                    low = [c]
                    lowterm = cterm

        self._low = low
        self._text = lowterm
        return lowterm

    def first(self):
        for c in self._cursors:
            c.first()
        return self._find_low()

    def find(self, term):
        for c in self._cursors:
            c.find(term)
        return self._find_low()

    def next(self):
        for c in self._cursors:
            c.next()
        return self._find_low()

    def term_info(self):
        tis = [c.term_info() for c in self._low]
        return combine_terminfos(tis) if tis else None

    def is_valid(self):
        return any(c.is_valid() for c in self._cursors)
