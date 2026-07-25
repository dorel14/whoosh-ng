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
"""Base collector class and helpers."""

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


def ilen(iterator):
    total = 0
    for _ in iterator:
        total += 1
    return total


class Collector:
    """Base class for collectors."""

    def prepare(self, top_searcher, q, context):
        """This method is called before a search.

        Subclasses can override this to perform set-up work, but
        they should still call the superclass's method because it sets several
        necessary attributes on the collector object:

        self.top_searcher
            The top-level searcher.
        self.q
            The query object
        self.context
            ``context.needs_current`` controls whether a wrapping collector
            requires that this collector's matcher be in a valid state at every
            call to ``collect()``. If this is ``False``, the collector is free
            to use faster methods that don't necessarily keep the matcher
            updated, such as ``matcher.all_ids()``.

        :param top_searcher: the top-level :class:` whoosh.searching.Searcher`
            object.
        :param q: the :class:` whoosh.query.Query` object being searched for.
        :param context: a :class:` whoosh.searching.SearchContext` object
            containing information about the search.
        """

        self.top_searcher = top_searcher
        self.q = q
        self.context = context

        self.starttime = now()
        self.runtime = None
        self.docset = set()

    def run(self):
        # Collect matches for each sub-searcher
        try:
            for subsearcher, offset in self.top_searcher.leaf_searchers():
                self.set_subsearcher(subsearcher, offset)
                self.collect_matches()
        finally:
            self.finish()

    def set_subsearcher(self, subsearcher, offset):
        """This method is called each time the collector starts on a new
        sub-searcher.

        Subclasses can override this to perform set-up work, but
        they should still call the superclass's method because it sets several
        necessary attributes on the collector object:

        self.subsearcher
            The current sub-searcher. If the top-level searcher is atomic, this
            is the same as the top-level searcher.
        self.offset
            The document number offset of the current searcher. You must add
            this number to the document number passed to
            :meth:`Collector.collect` to get the top-level document number
            for use in results.
        self.matcher
            A :class:` whoosh.matching.Matcher` object representing the matches
            for the query in the current sub-searcher.
        """

        self.subsearcher = subsearcher
        self.offset = offset
        self.matcher = self.q.matcher(subsearcher, self.context)

    def computes_count(self):
        """Returns True if the collector naturally computes the exact number of
        matching documents. Collectors that use block optimizations will return
        False since they might skip blocks containing matching documents.

        Note that if this method returns False you can still call :meth:`count`,
        but it means that method might have to do more work to calculate the
        number of matching documents.
        """

        return True

    def all_ids(self):
        """Returns a sequence of docnums matched in this collector. (Only valid
        after the collector is run.)

        The default implementation is based on the docset. If a collector does
        not maintain the docset, it will need to override this method.
        """

        return self.docset

    def count(self):
        """Returns the total number of documents matched in this collector.
        (Only valid after the collector is run.)

        The default implementation is based on the docset. If a collector does
        not maintain the docset, it will need to override this method.
        """

        return len(self.docset)

    def collect_matches(self):
        """This method calls :meth:`Collector.matches` and then for each
        matched document calls :meth:`Collector.collect`. Sub-classes that
        want to intervene between finding matches and adding them to the
        collection (for example, to filter out certain documents) can override
        this method.
        """

        collect = self.collect
        for sub_docnum in self.matches():
            collect(sub_docnum)

    @abstractmethod
    def collect(self, sub_docnum):
        """This method is called for every matched document. It should do the
        work of adding a matched document to the results, and it should return
        an object to use as a "sorting key" for the given document (such as the
        document's score, a key generated by a facet, or just None). Subclasses
        must implement this method.

        If you want the score for the current document, use
        ``self.matcher.score()``.

        Overriding methods should add the current document offset
        (``self.offset``) to the ``sub_docnum`` to get the top-level document
        number for the matching document to add to results.

        :param sub_docnum: the document number of the current match within the
            current sub-searcher. You must add ``self.offset`` to this number
            to get the document's top-level document number.
        """

        raise NotImplementedError

    @abstractmethod
    def sort_key(self, sub_docnum):
        """Returns a sorting key for the current match. This should return the
        same value returned by :meth:`Collector.collect`, but without the side
        effect of adding the current document to the results.

        If the collector has been prepared with ``context.needs_current=True``,
        this method can use ``self.matcher`` to get information, for example
        the score. Otherwise, it should only use the provided ``sub_docnum``,
        since the matcher may be in an inconsistent state.

        Subclasses must implement this method.
        """

        raise NotImplementedError

    def remove(self, global_docnum):
        """Removes a document from the collector. Not that this method uses the
        global document number as opposed to :meth:`Collector.collect` which
        takes a segment-relative docnum.
        """

        items = self.items
        for i in range(len(items)):
            if items[i][1] == global_docnum:
                items.pop(i)
                return
        raise KeyError(global_docnum)

    def _step_through_matches(self):
        matcher = self.matcher
        while matcher.is_active():
            yield matcher.id()
            matcher.next()

    def matches(self):
        """Yields a series of relative document numbers for matches
        in the current subsearcher.
        """

        # We jump through a lot of hoops to avoid stepping through the matcher
        # "manually" if we can because all_ids() is MUCH faster
        if self.context.needs_current:
            return self._step_through_matches()
        else:
            return self.matcher.all_ids()

    def finish(self):
        """This method is called after a search.

        Subclasses can override this to perform set-up work, but
        they should still call the superclass's method because it sets several
        necessary attributes on the collector object:

        self.runtime
            The time (in seconds) the search took.
        """

        self.runtime = now() - self.starttime

    def _results(self, items, **kwargs):
        # Fills in a Results object with the invariant information and the
        # given "items" (a list of (score, docnum) tuples)
        r = Results(self.top_searcher, self.q, items, **kwargs)
        r.runtime = self.runtime
        r.collector = self
        return r

    @abstractmethod
    def results(self):
        """Returns a :class:`~ whoosh.searching.Results` object containing the
        results of the search. Subclasses must implement this method
        """

        raise NotImplementedError
