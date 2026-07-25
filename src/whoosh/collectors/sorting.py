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
"""Sorting collector."""

import os
import threading
from abc import abstractmethod
from array import array
from bisect import insort
from collections import defaultdict
from heapq import heapify, heappush, heapreplace
from whoosh import sorting
from whoosh.searching import Results, TimeLimit
from whoosh.util import now

from whoosh.collectors.base import Collector

class SortingCollector(Collector):
    """A collector that returns results sorted by a given
    :class:` whoosh.sorting.Facet` object. See :doc:`/facets` for more
    information.
    """

    def __init__(self, sortedby, limit=10, reverse=False):
        """
        :param sortedby: see :doc:`/facets`.
        :param reverse: If True, reverse the overall results. Note that you
            can reverse individual facets in a multi-facet sort key as well.
        """

        Collector.__init__(self)
        self.sortfacet = sorting.MultiFacet.from_sortedby(sortedby)
        self.limit = limit
        self.reverse = reverse

    def prepare(self, top_searcher, q, context):
        self.categorizer = self.sortfacet.categorizer(top_searcher)
        # If the categorizer requires a valid matcher, then tell the child
        # collector that we need it
        rm = context.needs_current or self.categorizer.needs_current
        Collector.prepare(self, top_searcher, q, context.set(needs_current=rm))

        # List of (sortkey, docnum) pairs
        self.items = []

    def set_subsearcher(self, subsearcher, offset):
        Collector.set_subsearcher(self, subsearcher, offset)
        self.categorizer.set_searcher(subsearcher, offset)

    def sort_key(self, sub_docnum):
        return self.categorizer.key_for(self.matcher, sub_docnum)

    def collect(self, sub_docnum):
        global_docnum = self.offset + sub_docnum
        sortkey = self.sort_key(sub_docnum)
        self.items.append((sortkey, global_docnum))
        self.docset.add(global_docnum)
        return sortkey

    def results(self):
        items = self.items
        items.sort(reverse=self.reverse)
        if self.limit:
            items = items[: self.limit]
        return self._results(items, docset=self.docset)
