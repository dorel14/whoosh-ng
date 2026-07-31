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

# pyright: reportAttributeAccessIssue=false
"""The :class:`Results` class returned by a :class:`Searcher`."""

import copy

from whoosh import classify, highlight
from whoosh.searching._base import NoTermsException
from whoosh.searching.hit import Hit


class Results:
    """This object is returned by a Searcher. This object represents the
    results of a search query. You can mostly use it as if it was a list of
    dictionaries, where each dictionary is the stored fields of the document at
    that position in the results.

    Note that a Results object keeps a reference to the Searcher that created
    it, so keeping a reference to a Results object keeps the Searcher alive and
    so keeps all files used by it open.
    """

    def __init__(
        self,
        searcher,
        q,
        top_n,
        docset=None,
        facetmaps=None,
        runtime=0,
        highlighter=None,
    ):
        """
        :param searcher: the :class:`Searcher` object that produced these
            results.
        :param query: the original query that created these results.
        :param top_n: a list of (score, docnum) tuples representing the top
            N search results.
        """

        self.searcher = searcher
        self.q = q
        self.top_n = top_n
        self.docset = docset
        self._facetmaps = facetmaps or {}
        self.runtime = runtime
        self.highlighter = highlighter or highlight.Highlighter()
        self.collector = None
        self._total = None
        self._char_cache = {}

    def __repr__(self):
        return f"<Top {len(self.top_n)} Results for {self.q!r} runtime={self.runtime}>"

    def __len__(self):
        """Returns the total number of documents that matched the query. Note
        this may be more than the number of scored documents, given the value
        of the ``limit`` keyword argument to :meth:`Searcher.search`.

        If this Results object was created by searching with a ``limit``
        keyword, then computing the exact length of the result set may be
        expensive for large indexes or large result sets. You may consider
        using :meth:`Results.has_exact_length`,
        :meth:`Results.estimated_length`, and
        :meth:`Results.estimated_min_length` to display an estimated size of
        the result set instead of an exact number.
        """

        if self._total is None:
            self._total = self.collector.count()  # type: ignore[union-attr]
        return self._total

    def __getitem__(self, n):
        if isinstance(n, slice):
            start, stop, step = n.indices(len(self.top_n))
            return [
                Hit(self, self.top_n[i][1], i, self.top_n[i][0]) for i in range(start, stop, step)
            ]
        else:
            if n >= len(self.top_n):
                raise IndexError(f"results[{n!r}]: Results only has {len(self.top_n)} hits")
            return Hit(self, self.top_n[n][1], n, self.top_n[n][0])

    def __iter__(self):
        """Yields a :class:`Hit` object for each result in ranked order."""

        for i in range(len(self.top_n)):
            yield Hit(self, self.top_n[i][1], i, self.top_n[i][0])

    def __contains__(self, docnum):
        """Returns True if the given document number matched the query."""

        return docnum in self.docs()

    def __nonzero__(self):
        return not self.is_empty()

    __bool__ = __nonzero__

    def is_empty(self):
        """Returns True if not documents matched the query."""

        return self.scored_length() == 0

    def items(self):
        """Returns an iterator of (docnum, score) pairs for the scored
        documents in the results.
        """

        return ((docnum, score) for score, docnum in self.top_n)

    def fields(self, n):
        """Returns the stored fields for the document at the ``n`` th position
        in the results. Use :meth:`Results.docnum` if you want the raw
        document number instead of the stored fields.
        """

        return self.searcher.stored_fields(self.top_n[n][1])

    def facet_names(self):
        """Returns the available facet names, for use with the ``groups()``
        method.
        """

        return self._facetmaps.keys()

    def groups(self, name=None):
        """If you generated facet groupings for the results using the
        `groupedby` keyword argument to the ``search()`` method, you can use
        this method to retrieve the groups. You can use the ``facet_names()``
        method to get the list of available facet names.

        >>> results = searcher.search(my_query, groupedby=["tag", "price"])
        >>> results.facet_names()
        ["tag", "price"]
        >>> results.groups("tag")
        {"new": [12, 1, 4], "apple": [3, 10, 5], "search": [11]}

        If you only used one facet, you can call the method without a facet
        name to get the groups for the facet.

        >>> results = searcher.search(my_query, groupedby="tag")
        >>> results.groups()
        {"new": [12, 1, 4], "apple": [3, 10, 5, 0], "search": [11]}

        By default, this returns a dictionary mapping category names to a list
        of document numbers, in the same relative order as they appear in the
        results.

        >>> results = mysearcher.search(myquery, groupedby="tag")
        >>> docnums = results.groups()
        >>> docnums['new']
        [12, 1, 4]

        You can then use :meth:`Searcher.stored_fields` to get the stored
        fields associated with a document ID.

        If you specified a different ``maptype`` for the facet when you
        searched, the values in the dictionary depend on the
        :class:`whoosh.sorting.FacetMap`.

        >>> myfacet = sorting.FieldFacet("tag", maptype=sorting.Count)
        >>> results = mysearcher.search(myquery, groupedby=myfacet)
        >>> counts = results.groups()
        {"new": 3, "apple": 4, "search": 1}
        """

        if (name is None or name == "facet") and len(self._facetmaps) == 1:
            # If there's only one facet, just use it; convert keys() to list
            # for Python 3
            name = list(self._facetmaps.keys())[0]
        elif name not in self._facetmaps:
            raise KeyError(f"{name!r} not in facet names {self.facet_names()!r}")
        return self._facetmaps[name].as_dict()

    def has_exact_length(self):
        """Returns True if this results object already knows the exact number
        of matching documents.
        """

        if self.collector:
            return self.collector.computes_count()
        else:
            return self._total is not None

    def estimated_length(self):
        """The estimated maximum number of matching documents, or the
        exact number of matching documents if it's known.
        """

        if self.has_exact_length():
            return len(self)
        else:
            return self.q.estimate_size(self.searcher.reader())

    def estimated_min_length(self):
        """The estimated minimum number of matching documents, or the
        exact number of matching documents if it's known.
        """

        if self.has_exact_length():
            return len(self)
        else:
            return self.q.estimate_min_size(self.searcher.reader())

    def scored_length(self):
        """Returns the number of scored documents in the results, equal to or
        less than the ``limit`` keyword argument to the search.

        >>> r = mysearcher.search(myquery, limit=20)
        >>> len(r)
        1246
        >>> r.scored_length()
        20

        This may be fewer than the total number of documents that match the
        query, which is what ``len(Results)`` returns.
        """

        return len(self.top_n)

    def docs(self):
        """Returns a set-like object containing the document numbers that
        matched the query.
        """

        if self.docset is None:
            self.docset = set(self.collector.all_ids())  # type: ignore[union-attr]
        return self.docset

    def copy(self):
        """Returns a deep copy of this results object."""

        r = copy.copy(self)
        r.docset = set(self.docset) if self.docset is not None else None
        r.top_n = list(self.top_n)
        return r

    def score(self, n):
        """Returns the score for the document at the Nth position in the list
        of ranked documents. If the search was not scored, this may return
        None.
        """

        return self.top_n[n][0]

    def docnum(self, n):
        """Returns the document number of the result at position n in the list
        of ranked documents.
        """
        return self.top_n[n][1]

    def query_terms(self, expand=False, fieldname=None):
        return self.q.existing_terms(self.searcher.reader(), fieldname=fieldname, expand=expand)

    def has_matched_terms(self):
        """Returns True if the search recorded which terms matched in which
        documents.

        >>> r = searcher.search(myquery)
        >>> r.has_matched_terms()
        False
        >>>
        """

        return hasattr(self, "docterms") and hasattr(self, "termdocs")

    def matched_terms(self):
        """Returns the set of ``("fieldname", "text")`` tuples representing
        terms from the query that matched one or more of the TOP N documents
        (this does not report terms for documents that match the query but did
        not score high enough to make the top N results). You can compare this
        set to the terms from the original query to find terms which didn't
        occur in any matching documents.

        This is only valid if you used ``terms=True`` in the search call to
        record matching terms. Otherwise it will raise an exception.

        >>> q = myparser.parse("alfa OR bravo OR charlie")
        >>> results = searcher.search(q, terms=True)
        >>> results.terms()
        set([("content", "alfa"), ("content", "charlie")])
        >>> q.all_terms() - results.terms()
        set([("content", "bravo")])
        """

        if not self.has_matched_terms():
            raise NoTermsException
        return set(self.termdocs.keys())

    def _get_fragmenter(self):
        return self.highlighter.fragmenter

    def _set_fragmenter(self, f):
        self.highlighter.fragmenter = f

    fragmenter = property(_get_fragmenter, _set_fragmenter)

    def _get_formatter(self):
        return self.highlighter.formatter

    def _set_formatter(self, f):
        self.highlighter.formatter = f

    formatter = property(_get_formatter, _set_formatter)

    def _get_scorer(self):
        return self.highlighter.scorer

    def _set_scorer(self, s):
        self.highlighter.scorer = s

    scorer = property(_get_scorer, _set_scorer)

    def _get_order(self):
        return self.highlighter.order

    def _set_order(self, o):
        self.highlighter.order = o

    order = property(_get_order, _set_order)

    def key_terms(self, fieldname, docs=10, numterms=5, model=classify.Bo1Model, normalize=True):
        """Returns the 'numterms' most important terms from the top 'docs'
        documents in these results. "Most important" is generally defined as
        terms that occur frequently in the top hits but relatively infrequently
        in the collection as a whole.

        :param fieldname: Look at the terms in this field. This field must
            store vectors.
        :param docs: Look at this many of the top documents of the results.
        :param numterms: Return this number of important terms.
        :param model: The classify.ExpansionModel to use. See the classify
            module.
        :returns: list of unicode strings.
        """

        if not len(self):
            return []
        docs = min(docs, len(self))

        reader = self.searcher.reader()

        expander = classify.Expander(reader, fieldname, model=model)
        for _, docnum in self.top_n[:docs]:
            expander.add_document(docnum)

        return expander.expanded_terms(numterms, normalize=normalize)

    def extend(self, results):
        """Appends hits from 'results' (that are not already in this
        results object) to the end of these results.

        :param results: another results object.
        """

        docs = self.docs()
        for item in results.top_n:
            if item[1] not in docs:
                self.top_n.append(item)
        self.docset = docs | results.docs()
        self._total = len(self.docset)

    def filter(self, results):
        """Removes any hits that are not also in the other results object."""

        if not len(results):
            return

        otherdocs = results.docs()
        items = [item for item in self.top_n if item[1] in otherdocs]
        self.docset = self.docs() & otherdocs
        self.top_n = items

    def upgrade(self, results, reverse=False):
        """Re-sorts the results so any hits that are also in 'results' appear
        before hits not in 'results', otherwise keeping their current relative
        positions. This does not add the documents in the other results object
        to this one.

        :param results: another results object.
        :param reverse: if True, lower the position of hits in the other
            results object instead of raising them.
        """

        if not len(results):
            return

        otherdocs = results.docs()
        arein = [item for item in self.top_n if item[1] in otherdocs]
        notin = [item for item in self.top_n if item[1] not in otherdocs]

        if reverse:
            items = notin + arein
        else:
            items = arein + notin

        self.top_n = items

    def upgrade_and_extend(self, results):
        """Combines the effects of extend() and upgrade(): hits that are also
        in 'results' are raised. Then any hits from the other results object
        that are not in this results object are appended to the end.

        :param results: another results object.
        """

        if not len(results):
            return

        docs = self.docs()
        otherdocs = results.docs()

        arein = [item for item in self.top_n if item[1] in otherdocs]
        notin = [item for item in self.top_n if item[1] not in otherdocs]
        other = [item for item in results.top_n if item[1] not in docs]

        self.docset = docs | otherdocs
        self.top_n = arein + notin + other
