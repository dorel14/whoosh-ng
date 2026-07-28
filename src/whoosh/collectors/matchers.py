# type: ignore
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
"""Collectors based on matchers (scored, top-N, unlimited)."""

import os
import threading
from abc import abstractmethod
from array import array
from bisect import insort
from collections import defaultdict
from heapq import heapify, heappush, heapreplace

from whoosh import sorting
from whoosh.collectors.base import Collector, ilen
from whoosh.searching import Results, TimeLimit
from whoosh.util import now


class ScoredCollector(Collector):
    """Base class for collectors that sort the results based on document score."""

    def __init__(self, replace=10):
        """
        :param replace: Number of matches between attempts to replace the
            matcher with a more efficient version.
        """

        Collector.__init__(self)
        self.replace = replace

    def prepare(self, top_searcher, q, context):
        # This collector requires a valid matcher at each step
        Collector.prepare(self, top_searcher, q, context)

        if top_searcher.weighting.use_final:
            self.final_fn = top_searcher.weighting.final
        else:
            self.final_fn = None

        # Heap containing top N (score, 0-docnum) pairs
        self.items = []
        # Minimum score a document must have to make it into the top N. This is
        # used by the block-quality optimizations
        self.minscore = 0
        # Number of times the matcher was replaced (for debugging)
        self.replaced_times = 0
        # Number of blocks skipped by quality optimizations (for debugging)
        self.skipped_times = 0

    def sort_key(self, sub_docnum):
        return 0 - self.matcher.score()

    def _collect(self, global_docnum, score):
        # Concrete subclasses should override this method to collect matching
        # documents

        raise NotImplementedError

    def _use_block_quality(self):
        # Concrete subclasses should override this method to return True if the
        # collector should use block quality optimizations

        return False

    def collect(self, sub_docnum):
        # Do common work to calculate score and top-level document number
        global_docnum = self.offset + sub_docnum

        score = self.matcher.score()
        if self.final_fn:
            score = self.final_fn(self.top_searcher, global_docnum, score)

        # Call specialized method on subclass
        return self._collect(global_docnum, score)

    def matches(self):
        minscore = self.minscore
        matcher = self.matcher
        usequality = self._use_block_quality()
        replace = self.replace
        replacecounter = 0

        # A flag to indicate whether we should check block quality at the start
        # of the next loop
        checkquality = True

        while matcher.is_active():
            # If the replacement counter has reached 0, try replacing the
            # matcher with a more efficient version
            if replace:
                if replacecounter == 0 or self.minscore != minscore:
                    self.matcher = matcher = matcher.replace(minscore or 0)
                    self.replaced_times += 1
                    if not matcher.is_active():
                        break
                    usequality = self._use_block_quality()
                    replacecounter = self.replace

                    if self.minscore != minscore:
                        checkquality = True
                        minscore = self.minscore

                replacecounter -= 1

            # If we're using block quality optimizations, and the checkquality
            # flag is true, try to skip ahead to the next block with the
            # minimum required quality
            if usequality and checkquality and minscore is not None:
                self.skipped_times += matcher.skip_to_quality(minscore)
                # Skipping ahead might have moved the matcher to the end of the
                # posting list
                if not matcher.is_active():
                    break

            yield matcher.id()

            # Move to the next document. This method returns True if the
            # matcher has entered a new block, so we should check block quality
            # again.
            checkquality = matcher.next()


class TopCollector(ScoredCollector):
    """A collector that only returns the top "N" scored results."""

    def __init__(self, limit=10, usequality=True, **kwargs):
        """
        :param limit: the maximum number of results to return.
        :param usequality: whether to use block-quality optimizations. This may
            be useful for debugging.
        """

        ScoredCollector.__init__(self, **kwargs)
        self.limit = limit
        self.usequality = usequality
        self.total = 0

    def _use_block_quality(self):
        return (
            self.usequality
            and not self.top_searcher.weighting.use_final
            and self.matcher.supports_block_quality()
        )

    def computes_count(self):
        return not self._use_block_quality()

    def all_ids(self):
        # Since this collector can skip blocks, it doesn't track the total
        # number of matching documents, so if the user asks for all matched
        # docs we need to re-run the search using docs_for_query

        return self.top_searcher.docs_for_query(self.q)

    def count(self):
        if self.computes_count():
            return self.total
        else:
            return ilen(self.all_ids())

    # ScoredCollector.collect calls this
    def _collect(self, global_docnum, score):
        items = self.items
        self.total += 1

        # Document numbers are negated before putting them in the heap so that
        # higher document numbers have lower "priority" in the queue. Lower
        # document numbers should always come before higher document numbers
        # with the same score to keep the order stable.
        if len(items) < self.limit:
            # The heap isn't full, so add this document
            heappush(items, (score, 0 - global_docnum))
            # Negate score to act as sort key so higher scores appear first
            return 0 - score
        elif score > items[0][0]:
            # The heap is full, but if this document has a high enough
            # score to make the top N, add it to the heap
            heapreplace(items, (score, 0 - global_docnum))
            self.minscore = items[0][0]
            # Negate score to act as sort key so higher scores appear first
            return 0 - score
        else:
            return 0

    def remove(self, global_docnum):
        negated = 0 - global_docnum
        items = self.items

        # Remove the document if it's on the list (it may not be since
        # TopCollector forgets documents that don't make the top N list)
        for i in range(len(items)):
            if items[i][1] == negated:
                items.pop(i)
                # Restore the heap invariant
                heapify(items)
                self.minscore = items[0][0] if items else 0
                return

    def results(self):
        # The items are stored (postive score, negative docnum) so the heap
        # keeps the highest scores and lowest docnums, in order from lowest to
        # highest. Since for the results we want the highest scores first,
        # sort the heap in reverse order
        items = self.items
        items.sort(reverse=True)
        # De-negate the docnums for presentation to the user
        items = [(score, 0 - docnum) for score, docnum in items]
        return self._results(items)


class UnlimitedCollector(ScoredCollector):
    """A collector that returns **all** scored results."""

    def __init__(self, reverse=False):
        ScoredCollector.__init__(self)
        self.reverse = reverse

    # ScoredCollector.collect calls this
    def _collect(self, global_docnum, score):
        self.items.append((score, global_docnum))
        self.docset.add(global_docnum)
        # Negate score to act as sort key so higher scores appear first
        return 0 - score

    def results(self):
        # Sort by negated scores so that higher scores go first, then by
        # document number to keep the order stable when documents have the
        # same score
        self.items.sort(key=lambda x: (0 - x[0], x[1]), reverse=self.reverse)
        return self._results(self.items, docset=self.docset)


class UnsortedCollector(Collector):
    def prepare(self, top_searcher, q, context):
        Collector.prepare(self, top_searcher, q, context.set(weighting=None))
        self.items = []

    def collect(self, sub_docnum):
        global_docnum = self.offset + sub_docnum
        self.items.append((None, global_docnum))
        self.docset.add(global_docnum)

    def results(self):
        items = self.items
        return self._results(items, docset=self.docset)


class WrappingCollector(Collector):
    """Base class for collectors that wrap other collectors."""

    def __init__(self, child):
        self.child = child

    @property
    def top_searcher(self):
        return self.child.top_searcher

    @property
    def context(self):
        return self.child.context

    def prepare(self, top_searcher, q, context):
        self.child.prepare(top_searcher, q, context)

    def set_subsearcher(self, subsearcher, offset):
        self.child.set_subsearcher(subsearcher, offset)
        self.subsearcher = subsearcher
        self.matcher = self.child.matcher
        self.offset = self.child.offset

    def all_ids(self):
        return self.child.all_ids()

    def count(self):
        return self.child.count()

    def collect_matches(self):
        for sub_docnum in self.matches():
            self.collect(sub_docnum)

    def sort_key(self, sub_docnum):
        return self.child.sort_key(sub_docnum)

    def collect(self, sub_docnum):
        return self.child.collect(sub_docnum)

    def remove(self, global_docnum):
        return self.child.remove(global_docnum)

    def matches(self):
        return self.child.matches()

    def finish(self):
        self.child.finish()

    def results(self):
        return self.child.results()

