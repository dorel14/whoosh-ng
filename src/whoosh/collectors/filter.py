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
"""Filtering, faceting, collapsing, terms, and time-limit collectors."""

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

from whoosh.collectors.base import Collector, ilen
from whoosh.collectors.matchers import WrappingCollector


class FilterCollector(WrappingCollector):
    """A collector that lets you allow and/or restrict certain document numbers
    in the results::

        uc = collectors.UnlimitedCollector()

        ins = query.Term("chapter", "rendering")
        outs = query.Term("status", "restricted")
        fc = FilterCollector(uc, allow=ins, restrict=outs)

        mysearcher.search_with_collector(myquery, fc)
        print(fc.results())

    This collector discards a document if:

    * The allowed set is not None and a document number is not in the set, or
    * The restrict set is not None and a document number is in the set.

    (So, if the same document number is in both sets, that document will be
    discarded.)

    If you have a reference to the collector, you can use
    ``FilterCollector.filtered_count`` to get the number of matching documents
    filtered out of the results by the collector.
    """

    def __init__(self, child, allow=None, restrict=None):
        """
        :param child: the collector to wrap.
        :param allow: a query, Results object, or set-like object containing
            docnument numbers that are allowed in the results, or None (meaning
            everything is allowed).
        :param restrict: a query, Results object, or set-like object containing
            document numbers to disallow from the results, or None (meaning
            nothing is disallowed).
        """

        self.child = child
        self.allow = allow
        self.restrict = restrict

    def prepare(self, top_searcher, q, context):
        self.child.prepare(top_searcher, q, context)

        allow = self.allow
        restrict = self.restrict
        ftc = top_searcher._filter_to_comb

        self._allow = ftc(allow) if allow else None
        self._restrict = ftc(restrict) if restrict else None
        self.filtered_count = 0

    def all_ids(self):
        child = self.child

        _allow = self._allow
        _restrict = self._restrict

        for global_docnum in child.all_ids():
            if (_allow and global_docnum not in _allow) or (
                _restrict and global_docnum in _restrict
            ):
                continue
            yield global_docnum

    def count(self):
        child = self.child
        if child.computes_count():
            return child.count()
        else:
            return ilen(self.all_ids())

    def matches(self):
        # Re-apply the allow/restrict filtering at the "matches" level so that
        # wrapping collectors which iterate ``child.matches()`` (for example
        # :class:`TimeLimitCollector`) still respect the filter, instead of
        # bypassing :meth:`collect_matches` (issue #567).
        _allow = self._allow
        _restrict = self._restrict
        if _allow is None and _restrict is None:
            yield from self.child.matches()
            return

        offset = getattr(self, "offset", 0)
        for sub_docnum in self.child.matches():
            global_docnum = offset + sub_docnum
            if (_allow is not None and global_docnum not in _allow) or (
                _restrict is not None and global_docnum in _restrict
            ):
                continue
            yield sub_docnum

    def collect_matches(self):
        child = self.child
        _allow = self._allow
        _restrict = self._restrict

        if _allow is not None or _restrict is not None:
            filtered_count = self.filtered_count
            for sub_docnum in child.matches():
                global_docnum = self.offset + sub_docnum
                if (_allow is not None and global_docnum not in _allow) or (
                    _restrict is not None and global_docnum in _restrict
                ):
                    filtered_count += 1
                    continue
                child.collect(sub_docnum)
            self.filtered_count = filtered_count
        else:
            # If there was no allow or restrict set, don't do anything special,
            # just forward the call to the child collector
            child.collect_matches()

    def results(self):
        r = self.child.results()
        r.collector = self
        r.filtered_count = self.filtered_count
        r.allowed = self.allow
        r.restricted = self.restrict
        return r


class FacetCollector(WrappingCollector):
    """A collector that creates groups of documents based on
    :class:` whoosh.sorting.Facet` objects. See :doc:`/facets` for more
    information.

    This collector is used if you specify a ``groupedby`` parameter in the
    :meth:` whoosh.searching.Searcher.search` method. You can use the
    :meth:` whoosh.searching.Results.groups` method to access the facet groups.

    If you have a reference to the collector can also use
    ``FacetedCollector.facetmaps`` to access the groups directly::

        uc = collectors.UnlimitedCollector()
        fc = FacetedCollector(uc, sorting.FieldFacet("category"))
        mysearcher.search_with_collector(myquery, fc)
        print(fc.facetmaps)
    """

    def __init__(self, child, groupedby, maptype=None):
        """
        :param groupedby: see :doc:`/facets`.
        :param maptype: a :class:` whoosh.sorting.FacetMap` type to use for any
            facets that don't specify their own.
        """

        self.child = child
        self.facets = sorting.Facets.from_groupedby(groupedby)
        self.maptype = maptype

    def prepare(self, top_searcher, q, context):
        facets = self.facets

        # For each facet we're grouping by:
        # - Create a facetmap (to hold the groups)
        # - Create a categorizer (to generate document keys)
        self.facetmaps = {}
        self.categorizers = {}

        # Set needs_current to True if any of the categorizers require the
        # current document to work
        needs_current = context.needs_current
        for facetname, facet in facets.items():
            self.facetmaps[facetname] = facet.map(self.maptype)

            ctr = facet.categorizer(top_searcher)
            self.categorizers[facetname] = ctr
            needs_current = needs_current or ctr.needs_current
        context = context.set(needs_current=needs_current)

        self.child.prepare(top_searcher, q, context)

    def set_subsearcher(self, subsearcher, offset):
        WrappingCollector.set_subsearcher(self, subsearcher, offset)

        # Tell each categorizer about the new subsearcher and offset
        for categorizer in self.categorizers.values():
            categorizer.set_searcher(self.child.subsearcher, self.child.offset)

    def collect(self, sub_docnum):
        matcher = self.child.matcher
        global_docnum = sub_docnum + self.child.offset

        # We want the sort key for the document so we can (by default) sort
        # the facet groups
        sortkey = self.child.collect(sub_docnum)

        # For each facet we're grouping by
        for name, categorizer in self.categorizers.items():
            add = self.facetmaps[name].add

            # We have to do more work if the facet allows overlapping groups
            if categorizer.allow_overlap:
                for key in categorizer.keys_for(matcher, sub_docnum):
                    add(categorizer.key_to_name(key), global_docnum, sortkey)
            else:
                key = categorizer.key_for(matcher, sub_docnum)
                key = categorizer.key_to_name(key)
                add(key, global_docnum, sortkey)

        return sortkey

    def results(self):
        r = self.child.results()
        r._facetmaps = self.facetmaps
        return r


class CollapseCollector(WrappingCollector):
    """A collector that collapses results based on a facet. That is, it
    eliminates all but the top N results that share the same facet key.
    Documents with an empty key for the facet are never eliminated.

    The "top" results within each group is determined by the result ordering
    (e.g. highest score in a scored search) or an optional second "ordering"
    facet.

    If you have a reference to the collector you can use
    ``CollapseCollector.collapsed_counts`` to access the number of documents
    eliminated based on each key::

        tc = TopCollector(limit=20)
        cc = CollapseCollector(tc, "group", limit=3)
        mysearcher.search_with_collector(myquery, cc)
        print(cc.collapsed_counts)

    See :ref:`collapsing` for more information.
    """

    def __init__(self, child, keyfacet, limit=1, order=None):
        """
        :param child: the collector to wrap.
        :param keyfacet: a :class:` whoosh.sorting.Facet` to use for collapsing.
            All but the top N documents that share a key will be eliminated
            from the results.
        :param limit: the maximum number of documents to keep for each key.
        :param order: an optional :class:` whoosh.sorting.Facet` to use
            to determine the "top" document(s) to keep when collapsing. The
            default (``orderfaceet=None``) uses the results order (e.g. the
            highest score in a scored search).
        """

        self.child = child
        self.keyfacet = sorting.MultiFacet.from_sortedby(keyfacet)

        self.limit = limit
        if order:
            self.orderfacet = sorting.MultiFacet.from_sortedby(order)
        else:
            self.orderfacet = None

    def prepare(self, top_searcher, q, context):
        # Categorizer for getting the collapse key of a document
        self.keyer = self.keyfacet.categorizer(top_searcher)
        # Categorizer for getting the collapse order of a document
        self.orderer = None
        if self.orderfacet:
            self.orderer = self.orderfacet.categorizer(top_searcher)

        # Dictionary mapping keys to lists of (sortkey, global_docnum) pairs
        # representing the best docs for that key
        self.lists = defaultdict(list)
        # Dictionary mapping keys to the number of documents that have been
        # filtered out with that key
        self.collapsed_counts = defaultdict(int)
        # Total number of documents filtered out by collapsing
        self.collapsed_total = 0

        # If the keyer or orderer require a valid matcher, tell the child
        # collector we need it
        needs_current = (
            context.needs_current
            or self.keyer.needs_current
            or (self.orderer and self.orderer.needs_current)
        )
        self.child.prepare(top_searcher, q, context.set(needs_current=needs_current))

    def set_subsearcher(self, subsearcher, offset):
        WrappingCollector.set_subsearcher(self, subsearcher, offset)

        # Tell the keyer and (optional) orderer about the new subsearcher
        self.keyer.set_searcher(subsearcher, offset)
        if self.orderer:
            self.orderer.set_searcher(subsearcher, offset)

    def all_ids(self):
        child = self.child
        limit = self.limit
        counters = defaultdict(int)

        for subsearcher, offset in child.subsearchers():
            self.set_subsearcher(subsearcher, offset)
            matcher = child.matcher
            keyer = self.keyer
            for sub_docnum in child.matches():
                ckey = keyer.key_for(matcher, sub_docnum)
                if ckey is not None:
                    if ckey in counters and counters[ckey] >= limit:
                        continue
                    else:
                        counters[ckey] += 1
                yield offset + sub_docnum

    def count(self):
        if self.child.computes_count():
            return self.child.count() - self.collapsed_total
        else:
            return ilen(self.all_ids())

    def collect_matches(self):
        lists = self.lists
        limit = self.limit
        keyer = self.keyer
        orderer = self.orderer
        collapsed_counts = self.collapsed_counts

        child = self.child
        matcher = child.matcher
        offset = child.offset
        for sub_docnum in child.matches():
            # Collapsing category key
            ckey = keyer.key_to_name(keyer.key_for(matcher, sub_docnum))
            if not ckey:
                # If the document isn't in a collapsing category, just add it
                child.collect(sub_docnum)
            else:
                global_docnum = offset + sub_docnum

                if orderer:
                    # If user specified a collapse order, use it
                    sortkey = orderer.key_for(child.matcher, sub_docnum)
                else:
                    # Otherwise, use the results order
                    sortkey = child.sort_key(sub_docnum)

                # Current list of best docs for this collapse key
                best = lists[ckey]
                add = False
                if len(best) < limit:
                    # If the heap is not full yet, just add this document
                    add = True
                elif sortkey < best[-1][0]:
                    # If the heap is full but this document has a lower sort
                    # key than the highest key currently on the heap, replace
                    # the "least-best" document
                    # Tell the child collector to remove the document
                    child.remove(best.pop()[1])
                    add = True

                if add:
                    insort(best, (sortkey, global_docnum))
                    child.collect(sub_docnum)
                else:
                    # Remember that a document was filtered
                    collapsed_counts[ckey] += 1
                    self.collapsed_total += 1

    def results(self):
        r = self.child.results()
        r.collapsed_counts = self.collapsed_counts
        return r


class TimeLimitCollector(WrappingCollector):
    """A collector that raises a :class:`TimeLimit` exception if the search
    does not complete within a certain number of seconds::

        uc = collectors.UnlimitedCollector()
        tlc = TimeLimitedCollector(uc, timelimit=5.8)
        try:
            mysearcher.search_with_collector(myquery, tlc)
        except collectors.TimeLimit:
            print("The search ran out of time!")

        # We can still get partial results from the collector
        print(tlc.results())

    IMPORTANT: On Unix systems (systems where signal.SIGALRM is defined), the
    code uses signals to stop searching immediately when the time limit is
    reached. On Windows, the OS does not support this functionality, so the
    search only checks the time between each found document, so if a matcher
    is slow the search could exceed the time limit.
    """

    def __init__(self, child, timelimit, greedy=False, use_alarm=True):
        """
        :param child: the collector to wrap.
        :param timelimit: the maximum amount of time (in seconds) to
            allow for searching. If the search takes longer than this, it will
            raise a ``TimeLimit`` exception.
        :param greedy: if ``True``, the collector will finish adding the most
            recent hit before raising the ``TimeLimit`` exception.
        :param use_alarm: if ``True`` (the default), the collector will try to
            use signal.SIGALRM (on UNIX).
        """
        self.child = child
        self.timelimit = timelimit
        self.greedy = greedy

        if use_alarm:
            import signal

            self.use_alarm = use_alarm and hasattr(signal, "SIGALRM")
        else:
            self.use_alarm = False

        self.timer = None
        self.timedout = False

    def prepare(self, top_searcher, q, context):
        self.child.prepare(top_searcher, q, context)

        self.timedout = False
        if self.use_alarm:
            import signal

            signal.signal(signal.SIGALRM, self._was_signaled)

        # Start a timer thread. If the timer fires, it will call this object's
        # _timestop() method
        self.timer = threading.Timer(self.timelimit, self._timestop)
        self.timer.start()

    def _timestop(self):
        # Called when the timer expires
        self.timer = None
        # Set an attribute that will be noticed in the collect_matches() loop
        self.timedout = True

        if self.use_alarm:
            import signal

            os.kill(os.getpid(), signal.SIGALRM)

    def _was_signaled(self, signum, frame):
        raise TimeLimit

    def collect_matches(self):
        child = self.child
        greedy = self.greedy

        for sub_docnum in child.matches():
            # If the timer fired since the last loop and we're not greedy,
            # raise the exception
            if self.timedout and not greedy:
                raise TimeLimit

            child.collect(sub_docnum)

            # If the timer fired since we entered the loop or it fired earlier
            # but we were greedy, raise now
            if self.timedout:
                raise TimeLimit

    def finish(self):
        if self.timer:
            self.timer.cancel()
        self.timer = None
        self.child.finish()


class TermsCollector(WrappingCollector):
    """A collector that remembers which terms appeared in which terms appeared
    in each matched document.

    This collector is used if you specify ``terms=True`` in the
    :meth:` whoosh.searching.Searcher.search` method.

    If you have a reference to the collector can also use
    ``TermsCollector.termslist`` to access the term lists directly::

        uc = collectors.UnlimitedCollector()
        tc = TermsCollector(uc)
        mysearcher.search_with_collector(myquery, tc)
        # tc.termdocs is a dictionary mapping (fieldname, text) tuples to
        # sets of document numbers
        print(tc.termdocs)
        # tc.docterms is a dictionary mapping docnums to lists of
        # (fieldname, text) tuples
        print(tc.docterms)
    """

    def __init__(self, child, settype=set):
        self.child = child
        self.settype = settype

    def prepare(self, top_searcher, q, context):
        # This collector requires a valid matcher at each step
        self.child.prepare(top_searcher, q, context.set(needs_current=True))

        # A dictionary mapping (fieldname, text) pairs to arrays of docnums
        self.termdocs = defaultdict(lambda: array("I"))
        # A dictionary mapping docnums to lists of (fieldname, text) pairs
        self.docterms = defaultdict(list)

    def set_subsearcher(self, subsearcher, offset):
        WrappingCollector.set_subsearcher(self, subsearcher, offset)

        # Store a list of all the term matchers in the matcher tree
        self.termmatchers = list(self.child.matcher.term_matchers())

    def collect(self, sub_docnum):
        child = self.child
        termdocs = self.termdocs
        docterms = self.docterms

        child.collect(sub_docnum)

        global_docnum = child.offset + sub_docnum

        # For each term matcher...
        for tm in self.termmatchers:
            # If the term matcher is matching the current document...
            if tm.is_active() and tm.id() == sub_docnum:
                # Add it to the list of matching documents for the term
                term = tm.term()
                termdocs[term].append(global_docnum)
                docterms[global_docnum].append(term)

    def results(self):
        r = self.child.results()
        r.termdocs = dict(self.termdocs)
        r.docterms = dict(self.docterms)
        return r
