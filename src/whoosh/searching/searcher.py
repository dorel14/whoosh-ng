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
"""The :class:`Searcher` class for searching an index."""

import weakref

from whoosh import classify, highlight, query, scoring
from whoosh.fields import UnknownFieldError
from whoosh.idsets import BitSet, DocIdSet
from whoosh.reading import TermNotFound
from whoosh.searching.context import SearchContext
from whoosh.searching.results import Results
from whoosh.searching.results_page import ResultsPage


class Searcher:
    """Wraps an :class:`~whoosh.reading.IndexReader` object and provides
    methods for searching the index.
    """

    def __init__(
        self,
        reader,
        weighting=scoring.BM25F,
        closereader=True,
        fromindex=None,
        parent=None,
    ):
        """
        :param reader: An :class:`~whoosh.reading.IndexReader` object for
            the index to search.
        :param weighting: A :class:`whoosh.scoring.Weighting` object to use to
            score found documents.
        :param closereader: Whether the underlying reader will be closed when
            the searcher is closed.
        :param fromindex: An optional reference to the index of the underlying
            reader. This is required for :meth:`Searcher.up_to_date` and
            :meth:`Searcher.refresh` to work.
        """

        self.ixreader = reader
        self.is_closed = False
        self._closereader = closereader
        self._ix = fromindex
        self._doccount = self.ixreader.doc_count_all()
        # Cache for PostingCategorizer objects (supports fields without columns)
        self._field_caches = {}

        if parent:
            self.parent = weakref.ref(parent)
            self.schema = parent.schema
            self._idf_cache = parent._idf_cache
            self._filter_cache = parent._filter_cache
        else:
            self.parent = None
            self.schema = self.ixreader.schema
            self._idf_cache = {}
            self._filter_cache = {}

        if type(weighting) is type:
            self.weighting = weighting()
        elif isinstance(weighting, str):
            # Issue #494: accept a registered weighting name, e.g.
            # weighting="BM25F" / "TFIDF".
            from whoosh import scoring

            self.weighting = scoring.weighting_from_name(weighting)
        else:
            self.weighting = weighting

        self.leafreaders = None
        self.subsearchers = None
        if not self.ixreader.is_atomic():
            self.leafreaders = self.ixreader.leaf_readers()
            self.subsearchers = [(self._subsearcher(r), offset) for r, offset in self.leafreaders]

        # Delegated attributes are resolved via __getattr__ to avoid
        # eagerly copying references onto this instance.

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    _READER_DELEGATES = (
        "stored_fields",
        "all_stored_fields",
        "has_vector",
        "vector",
        "vector_as",
        "lexicon",
        "field_terms",
        "frequency",
        "doc_frequency",
        "term_info",
        "doc_field_length",
        "corrector",
        "iter_docs",
    )

    def __getattr__(self, name):
        if name in self._READER_DELEGATES:
            return getattr(self.ixreader, name)
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    def _subsearcher(self, reader):
        return self.__class__(reader, fromindex=self._ix, weighting=self.weighting, parent=self)  # type: ignore[arg-type]

    def _offset_for_subsearcher(self, subsearcher):
        for ss, offset in self.subsearchers:  # type: ignore[union-attr]
            if ss is subsearcher:
                return offset

    def leaf_searchers(self):
        if self.is_atomic():
            return [(self, 0)]
        else:
            return self.subsearchers

    def is_atomic(self):
        return self.reader().is_atomic()

    def has_parent(self):
        return self.parent is not None

    def get_parent(self) -> "Searcher":
        """Returns the parent of this searcher (if has_parent() is True), or
        else self.
        """

        if self.has_parent():
            # Call the weak reference to get the parent searcher
            return self.parent()  # type: ignore[operator]
        else:
            return self

    def doc_count(self):
        """Returns the number of UNDELETED documents in the index."""

        return self.ixreader.doc_count()

    def doc_count_all(self):
        """Returns the total number of documents, DELETED OR UNDELETED, in
        the index.
        """

        return self._doccount

    def field_length(self, fieldname):
        if self.has_parent():
            return self.get_parent().field_length(fieldname)
        else:
            return self.reader().field_length(fieldname)

    def max_field_length(self, fieldname):
        if self.has_parent():
            return self.get_parent().max_field_length(fieldname)
        else:
            return self.reader().max_field_length(fieldname)

    def up_to_date(self):
        """Returns True if this Searcher represents the latest version of the
        index, for backends that support versioning.
        """

        if not self._ix:
            raise ValueError("No reference to index")  # Replace generic exception with ValueError
        return self._ix.latest_generation() == self.ixreader.generation()

    def refresh(self):
        """Returns a fresh searcher for the latest version of the index::

            my_searcher = my_searcher.refresh()

        If the index has not changed since this searcher was created, this
        searcher is simply returned.

        This method may CLOSE underlying resources that are no longer needed
        by the refreshed searcher, so you CANNOT continue to use the original
        searcher after calling ``refresh()`` on it.
        """

        if not self._ix:
            raise ValueError("No reference to index")
        if self._ix.latest_generation() == self.reader().generation():
            return self

        # Get a new reader, re-using resources from the current reader if
        # possible
        self.is_closed = True
        newreader = self._ix.reader(reuse=self.ixreader)
        return self.__class__(newreader, fromindex=self._ix, weighting=self.weighting)  # type: ignore[arg-type]

    def close(self):
        if self._closereader:
            self.ixreader.close()
        self.is_closed = True

    def avg_field_length(self, fieldname, default=None):
        if not self.schema[fieldname].scorable:
            return default
        return self.field_length(fieldname) / (self._doccount or 1)

    def reader(self):
        """Returns the underlying :class:`~whoosh.reading.IndexReader`."""
        return self.ixreader

    def context(self, **kwargs):
        """Generates a :class:`SearchContext` for this searcher."""

        if "weighting" not in kwargs:
            kwargs["weighting"] = self.weighting

        return SearchContext(**kwargs)

    def boolean_context(self):
        """Shortcut returns a SearchContext set for unscored (boolean)
        searching.
        """

        return self.context(needs_current=False, weighting=None)

    def postings(self, fieldname, text, weighting=None, qf=1):
        """Returns a :class:`whoosh.matching.Matcher` for the postings of the
        given term. Unlike the :func:`whoosh.reading.IndexReader.postings`
        method, this method automatically sets the scoring functions on the
        matcher from the searcher's weighting object.
        """

        weighting = weighting or self.weighting
        globalscorer = weighting.scorer(self, fieldname, text, qf=qf)  # type: ignore[attr-defined]

        if self.is_atomic():
            return self.ixreader.postings(fieldname, text, scorer=globalscorer)
        else:
            from whoosh.matching import MultiMatcher

            matchers = []
            docoffsets = []
            term = (fieldname, text)
            for subsearcher, offset in self.subsearchers:  # type: ignore[union-attr]
                r = subsearcher.reader()
                if term in r:
                    # Make a segment-specific scorer; the scorer should call
                    # searcher.parent() to get global stats
                    scorer = weighting.scorer(subsearcher, fieldname, text, qf=qf)  # type: ignore[attr-defined]
                    m = r.postings(fieldname, text, scorer=scorer)
                    matchers.append(m)
                    docoffsets.append(offset)

            if not matchers:
                raise TermNotFound(fieldname, text)

            return MultiMatcher(matchers, docoffsets, globalscorer)

    def idf(self, fieldname, text):
        """Calculates the Inverse Document Frequency of the current term (calls
        idf() on the searcher's Weighting object).
        """

        # This method just calls the Weighting object's idf() method, but
        # caches the result. So Weighting objects should call *this* method
        # which will then call *their own* idf() methods.

        cache = self._idf_cache
        term = (fieldname, text)
        if term in cache:
            return cache[term]

        idf = self.weighting.idf(self, fieldname, text)  # type: ignore[attr-defined]
        cache[term] = idf
        return idf

    def document(self, **kw):
        """Convenience method returns the stored fields of a document
        matching the given keyword arguments, where the keyword keys are
        field names and the values are terms that must appear in the field.

        This method is equivalent to::

            searcher.stored_fields(searcher.document_number(<keyword args>))

        Where Searcher.documents() returns a generator, this function returns
        either a dictionary or None. Use it when you assume the given keyword
        arguments either match zero or one documents (i.e. at least one of the
        fields is a unique key).

        >>> stored_fields = searcher.document(path=u"/a/b")
        >>> if stored_fields:
        ...   print(stored_fields['title'])
        ... else:
        ...   print("There is no document with the path /a/b")
        """

        for p in self.documents(**kw):
            return p

    def documents(self, **kw):
        """Convenience method returns the stored fields of a document
        matching the given keyword arguments, where the keyword keys are field
        names and the values are terms that must appear in the field.

        Returns a generator of dictionaries containing the stored fields of any
        documents matching the keyword arguments. If you do not specify any
        arguments (``Searcher.documents()``), this method will yield **all**
        documents.

        >>> for stored_fields in searcher.documents(emailto=u"matt@whoosh.ca"):
        ...   print("Email subject:", stored_fields['subject'])
        """

        ixreader = self.ixreader
        return (ixreader.stored_fields(docnum) for docnum in self.document_numbers(**kw))

    def _kw_to_text(self, kw):
        for k, v in kw.items():
            field = self.schema[k]
            kw[k] = field.to_bytes(v)

    def _query_for_kw(self, kw):
        subqueries = []
        for key, value in kw.items():
            subqueries.append(query.Term(key, value))
        if subqueries:
            q = query.And(subqueries).normalize()
        else:
            q = query.Every()
        return q

    def document_number(self, **kw):
        """Returns the document number of the document matching the given
        keyword arguments, where the keyword keys are field names and the
        values are terms that must appear in the field.

        >>> docnum = searcher.document_number(path=u"/a/b")

        Where Searcher.document_numbers() returns a generator, this function
        returns either an int or None. Use it when you assume the given keyword
        arguments either match zero or one documents (i.e. at least one of the
        fields is a unique key).

        :rtype: int
        """

        # In the common case where only one keyword was given, just use
        # first_id() instead of building a query.

        self._kw_to_text(kw)
        if len(kw) == 1:
            k, v = list(kw.items())[0]
            try:
                return self.reader().first_id(k, v)
            except TermNotFound:
                return None
        else:
            m = self._query_for_kw(kw).matcher(self, self.boolean_context())
            if m.is_active():
                return m.id()

    def document_numbers(self, **kw):
        """Returns a generator of the document numbers for documents matching
        the given keyword arguments, where the keyword keys are field names and
        the values are terms that must appear in the field. If you do not
        specify any arguments (``Searcher.document_numbers()``), this method
        will yield **all** document numbers.

        >>> docnums = list(searcher.document_numbers(emailto="matt@whoosh.ca"))
        """

        self._kw_to_text(kw)
        return self.docs_for_query(self._query_for_kw(kw))

    def _find_unique(self, uniques):
        # uniques is a list of ("unique_field_name", "field_value") tuples
        delset = set()
        for name, value in uniques:
            docnum = self.document_number(**{name: value})
            if docnum is not None:
                delset.add(docnum)
        return delset

    def _query_to_comb(self, fq):
        return BitSet(self.docs_for_query(fq), size=self.doc_count_all())

    def _filter_to_comb(self, obj):
        if obj is None:
            return None
        if isinstance(obj, (set, DocIdSet)):
            c = obj
        elif isinstance(obj, Results):
            c = obj.docs()
        elif isinstance(obj, ResultsPage):
            c = obj.results.docs()
        elif isinstance(obj, query.Query):
            c = self._query_to_comb(obj)
        else:
            raise ValueError(f"Don't know what to do with filter object {obj}")

        return c

    def suggest(self, fieldname, text, limit=5, maxdist=2, prefix=0):
        """Returns a sorted list of suggested corrections for the given
        mis-typed word ``text`` based on the contents of the given field::

            >>> searcher.suggest("content", "specail")
            ["special"]

        This is a convenience method. If you are planning to get suggestions
        for multiple words in the same field, it is more efficient to get a
        :class:`~whoosh.spelling.Corrector` object and use it directly::

            corrector = searcher.corrector("fieldname")
            for word in words:
                print(corrector.suggest(word))

        :param limit: only return up to this many suggestions. If there are not
            enough terms in the field within ``maxdist`` of the given word, the
            returned list will be shorter than this number.
        :param maxdist: the largest edit distance from the given word to look
            at. Numbers higher than 2 are not very effective or efficient.
        :param prefix: require suggestions to share a prefix of this length
            with the given word. This is often justifiable since most
            misspellings do not involve the first letter of the word. Using a
            prefix dramatically decreases the time it takes to generate the
            list of words.
        """

        c = self.reader().corrector(fieldname)
        return c.suggest(text, limit=limit, maxdist=maxdist, prefix=prefix)

    def key_terms(self, docnums, fieldname, numterms=5, model=classify.Bo1Model, normalize=True):
        """Returns the 'numterms' most important terms from the documents
        listed (by number) in 'docnums'. You can get document numbers for the
        documents your interested in with the document_number() and
        document_numbers() methods.

        "Most important" is generally defined as terms that occur frequently in
        the top hits but relatively infrequently in the collection as a whole.

        >>> docnum = searcher.document_number(path=u"/a/b")
        >>> keywords_and_scores = searcher.key_terms([docnum], "content")

        This method returns a list of ("term", score) tuples. The score may be
        useful if you want to know the "strength" of the key terms, however to
        just get the terms themselves you can just do this:

        >>> kws = [kw for kw, score in searcher.key_terms([docnum], "content")]

        :param fieldname: Look at the terms in this field. This field must
            store vectors.
        :param docnums: A sequence of document numbers specifying which
            documents to extract key terms from.
        :param numterms: Return this number of important terms.
        :param model: The classify.ExpansionModel to use. See the classify
            module.
        :param normalize: normalize the scores.
        :returns: a list of ("term", score) tuples.
        """

        expander = classify.Expander(self.ixreader, fieldname, model=model)
        for docnum in docnums:
            expander.add_document(docnum)
        return expander.expanded_terms(numterms, normalize=normalize)

    def key_terms_from_text(
        self, fieldname, text, numterms=5, model=classify.Bo1Model, normalize=True
    ):
        """Return the 'numterms' most important terms from the given text.

        :param numterms: Return this number of important terms.
        :param model: The classify.ExpansionModel to use. See the classify
            module.
        """

        expander = classify.Expander(self.ixreader, fieldname, model=model)
        expander.add_text(text)
        return expander.expanded_terms(numterms, normalize=normalize)

    def more_like(
        self,
        docnum,
        fieldname,
        text=None,
        top=10,
        numterms=5,
        model=classify.Bo1Model,
        normalize=False,
        filter=None,
    ):
        """Returns a :class:`Results` object containing documents similar to
        the given document, based on "key terms" in the given field::

            # Get the ID for the document you're interested in
            docnum = search.document_number(path=u"/a/b/c")

            r = searcher.more_like(docnum)

            print("Documents like", searcher.stored_fields(docnum)["title"])
            for hit in r:
                print(hit["title"])

        :param fieldname: the name of the field to use to test similarity.
        :param text: by default, the method will attempt to load the contents
            of the field from the stored fields for the document, or from a
            term vector. If the field isn't stored or vectored in the index,
            but you have access to the text another way (for example, loading
            from a file or a database), you can supply it using the ``text``
            parameter.
        :param top: the number of results to return.
        :param numterms: the number of "key terms" to extract from the hit and
            search for. Using more terms is slower but gives potentially more
            and more accurate results.
        :param model: (expert) a :class:`whoosh.classify.ExpansionModel` to use
            to compute "key terms".
        :param normalize: whether to normalize term weights.
        :param filter: a query, Results object, or set of docnums. The results
            will only contain documents that are also in the filter object.
        """

        if text:
            kts = self.key_terms_from_text(
                fieldname, text, numterms=numterms, model=model, normalize=normalize
            )
        else:
            kts = self.key_terms(
                [docnum], fieldname, numterms=numterms, model=model, normalize=normalize
            )
        # Create an Or query from the key terms
        q = query.Or([query.Term(fieldname, word, boost=weight) for word, weight in kts])

        return self.search(q, limit=top, filter=filter, mask={docnum})

    def search_page(self, query, pagenum, pagelen=10, **kwargs):
        """This method is Like the :meth:`Searcher.search` method, but returns
        a :class:`ResultsPage` object. This is a convenience function for
        getting a certain "page" of the results for the given query, which is
        often useful in web search interfaces.

        For example::

            querystring = request.get("q")
            query = queryparser.parse("content", querystring)

            pagenum = int(request.get("page", 1))
            pagelen = int(request.get("perpage", 10))

            results = searcher.search_page(query, pagenum, pagelen=pagelen)
            print("Page %d of %d" % (results.pagenum, results.pagecount))
            print("Showing results %d-%d of %d"
                  % (results.offset + 1, results.offset + results.pagelen + 1,
                     len(results)))
            for hit in results:
                print("%d: %s" % (hit.rank + 1, hit["title"]))

        (Note that results.pagelen might be less than the pagelen argument if
        there aren't enough results to fill a page.)

        Any additional keyword arguments you supply are passed through to
        :meth:`Searcher.search`. For example, you can get paged results of a
        sorted search::

            results = searcher.search_page(q, 2, sortedby="date", reverse=True)

        Currently, searching for page 100 with pagelen of 10 takes the same
        amount of time as using :meth:`Searcher.search` to find the first 1000
        results. That is, this method does not have any special optimizations
        or efficiencies for getting a page from the middle of the full results
        list. (A future enhancement may allow using previous page results to
        improve the efficiency of finding the next page.)

        This method will raise a ``ValueError`` if you ask for a page number
        higher than the number of pages in the resulting query.

        :param query: the :class:`whoosh.query.Query` object to match.
        :param pagenum: the page number to retrieve, starting at ``1`` for the
            first page.
        :param pagelen: the number of results per page.
        :returns: :class:`ResultsPage`
        """

        if pagenum < 1:
            raise ValueError("pagenum must be >= 1")

        results = self.search(query, limit=pagenum * pagelen, **kwargs)
        return ResultsPage(results, pagenum, pagelen)

    def find(self, defaultfield, querystring, **kwargs):
        from whoosh.qparser import QueryParser

        qp = QueryParser(defaultfield, schema=self.ixreader.schema)
        q = qp.parse(querystring)
        return self.search(q, **kwargs)

    def docs_for_query(self, q, for_deletion=False):
        """Returns an iterator of document numbers for documents matching the
        given :class:`whoosh.query.Query` object.
        """

        # If we're getting the document numbers so we can delete them, use the
        # deletion_docs method instead of docs; this lets special queries
        # (e.g. nested queries) override what gets deleted
        if for_deletion:
            method = q.deletion_docs
        else:
            method = q.docs

        if self.subsearchers:
            for s, offset in self.subsearchers:
                for docnum in method(s):
                    yield docnum + offset
        else:
            for docnum in method(self):
                yield docnum

    def collector(
        self,
        limit=10,
        sortedby=None,
        reverse=False,
        groupedby=None,
        collapse=None,
        collapse_limit=1,
        collapse_order=None,
        optimize=True,
        filter=None,
        mask=None,
        terms=False,
        maptype=None,
        scored=True,
    ):
        """Low-level method: returns a configured
        :class:`whoosh.collectors.Collector` object based on the given
        arguments. You can use this object with
        :meth:`Searcher.search_with_collector` to search.

        See the documentation for the :meth:`Searcher.search` method for a
        description of the parameters.

        This method may be useful to get a basic collector object and then wrap
        it with another collector from ``whoosh.collectors`` or with a custom
        collector of your own::

            # Equivalent of
            # results = mysearcher.search(myquery, limit=10)
            # but with a time limt...

            # Create a TopCollector
            c = mysearcher.collector(limit=10)

            # Wrap it with a TimeLimitedCollector with a time limit of
            # 10.5 seconds
            from whoosh.collectors import TimeLimitedCollector
            c = TimeLimitCollector(c, 10.5)

            # Search using the custom collector
            results = mysearcher.search_with_collector(myquery, c)
        """

        from whoosh import collectors

        if limit is not None and limit < 1:
            raise ValueError("limit must be >= 1")

        if not scored and not sortedby:
            c = collectors.UnsortedCollector()
        elif sortedby:
            c = collectors.SortingCollector(sortedby, limit=limit, reverse=reverse)
        elif groupedby or reverse or not limit or limit >= self.doc_count():
            # A collector that gathers every matching document
            c = collectors.UnlimitedCollector(reverse=reverse)
        else:
            # A collector that uses block quality optimizations and a heap
            # queue to only collect the top N documents
            c = collectors.TopCollector(limit, usequality=optimize)

        if groupedby:
            c = collectors.FacetCollector(c, groupedby, maptype=maptype)
        if terms:
            c = collectors.TermsCollector(c)
        if collapse:
            c = collectors.CollapseCollector(
                c, collapse, limit=collapse_limit, order=collapse_order
            )

        # Filtering wraps last so it sees the docs first
        if filter or mask:
            c = collectors.FilterCollector(c, filter, mask)
        return c

    def search(self, q, **kwargs):
        """Runs a :class:`whoosh.query.Query` object on this searcher and
        returns a :class:`Results` object. See :doc:`/searching` for more
        information.

        This method takes many keyword arguments (documented below).

        See :doc:`/facets` for information on using ``sortedby`` and/or
        ``groupedby``. See :ref:`collapsing` for more information on using
        ``collapse``, ``collapse_limit``, and ``collapse_order``.

        :param query: a :class:`whoosh.query.Query` object to use to match
            documents.
        :param limit: the maximum number of documents to score. If you're only
            interested in the top N documents, you can set limit=N to limit the
            scoring for a faster search. Default is 10.
        :param scored: whether to score the results. Overriden by ``sortedby``.
            If both ``scored=False`` and ``sortedby=None``, the results will be
            in arbitrary order, but will usually be computed faster than
            scored or sorted results.
        :param sortedby: see :doc:`/facets`.
        :param reverse: Reverses the direction of the sort. Default is False.
        :param groupedby: see :doc:`/facets`.
        :param optimize: use optimizations to get faster results when possible.
            Default is True.
        :param filter: a query, Results object, or set of docnums. The results
            will only contain documents that are also in the filter object.
        :param mask: a query, Results object, or set of docnums. The results
            will not contain any documents that are in the mask object.
        :param terms: if True, record which terms were found in each matching
            document. See :doc:`/searching` for more information. Default is
            False.
        :param maptype: by default, the results of faceting with ``groupedby``
            is a dictionary mapping group names to ordered lists of document
            numbers in the group. You can pass a
            :class:`whoosh.sorting.FacetMap` subclass to this keyword argument
            to specify a different (usually faster) method for grouping. For
            example, ``maptype=sorting.Count`` would store only the count of
            documents in each group, instead of the full list of document IDs.
        :param collapse: a :doc:`facet </facets>` to use to collapse the
            results. See :ref:`collapsing` for more information.
        :param collapse_limit: the maximum number of documents to allow with
            the same collapse key. See :ref:`collapsing` for more information.
        :param collapse_order: an optional ordering :doc:`facet </facets>`
            to control which documents are kept when collapsing. The default
            (``collapse_order=None``) uses the results order (e.g. the highest
            scoring documents in a scored search).
        :rtype: :class:`Results`
        """

        # Call the collector() method to build a collector based on the
        # parameters passed to this method
        c = self.collector(**kwargs)
        # Call the lower-level method to run the collector
        self.search_with_collector(q, c)
        # Return the results object from the collector
        return c.results()

    def search_with_collector(self, q, collector, context=None):
        """Low-level method: runs a :class:`whoosh.query.Query` object on this
        searcher using the given :class:`whoosh.collectors.Collector` object
        to collect the results::

            myquery = query.Term("content", "cabbage")

            uc = collectors.UnlimitedCollector()
            tc = TermsCollector(uc)

            mysearcher.search_with_collector(myquery, tc)
            print(tc.docterms)
            print(tc.results())

        Note that this method does not return a :class:`Results` object. You
        need to access the collector to get a results object or other
        information the collector might hold after the search.

        :param q: a :class:`whoosh.query.Query` object to use to match
            documents.
        :param collector: a :class:`whoosh.collectors.Collector` object to feed
            the results into.
        """

        # Get the search context object from the searcher
        context = context or self.context()
        # Allow collector to set up based on the top-level information
        collector.prepare(self, q, context)

        collector.run()

    def correct_query(
        self, q, qstring, correctors=None, terms=None, maxdist=2, prefix=0, aliases=None
    ):
        """
        Returns a corrected version of the given user query using a default
        :class:`whoosh.spelling.ReaderCorrector`.

        The default:

        * Corrects any words that don't appear in the index.

        * Takes suggestions from the words in the index. To make certain fields
          use custom correctors, use the ``correctors`` argument to pass a
          dictionary mapping field names to :class:`whoosh.spelling.Corrector`
          objects.

        Expert users who want more sophisticated correction behavior can create
        a custom :class:`whoosh.spelling.QueryCorrector` and use that instead
        of this method.

        Returns a :class:`whoosh.spelling.Correction` object with a ``query``
        attribute containing the corrected :class:`whoosh.query.Query` object
        and a ``string`` attributes containing the corrected query string.

        >>> from whoosh import qparser, highlight
        >>> qtext = 'mary "litle lamb"'
        >>> q = qparser.QueryParser("text", myindex.schema)
        >>> mysearcher = myindex.searcher()
        >>> correction = mysearcher().correct_query(q, qtext)
        >>> correction.query
        <query.And ...>
        >>> correction.string
        'mary "little lamb"'
        >>> mysearcher.close()

        You can use the ``Correction`` object's ``format_string`` method to
        format the corrected query string using a
        :class:`whoosh.highlight.Formatter` object. For example, you can format
        the corrected string as HTML, emphasizing the changed words.

        >>> hf = highlight.HtmlFormatter(classname="change")
        >>> correction.format_string(hf)
        'mary "<strong class="change term0">little</strong> lamb"'

        :param q: the :class:`whoosh.query.Query` object to correct.
        :param qstring: the original user query from which the query object was
            created. You can pass None instead of a string, in which the
            second item in the returned tuple will also be None.
        :param correctors: an optional dictionary mapping fieldnames to
            :class:`whoosh.spelling.Corrector` objects. By default, this method
            uses the contents of the index to spell check the terms in the
            query. You can use this argument to "override" some fields with a
            different correct, for example a
            :class:`whoosh.spelling.GraphCorrector`.
        :param terms: a sequence of ``("fieldname", "text")`` tuples to correct
            in the query. By default, this method corrects terms that don't
            appear in the index. You can use this argument to override that
            behavior and explicitly specify the terms that should be corrected.
        :param maxdist: the maximum number of "edits" (insertions, deletions,
            subsitutions, or transpositions of letters) allowed between the
            original word and any suggestion. Values higher than ``2`` may be
            slow.
        :param prefix: suggested replacement words must share this number of
            initial characters with the original word. Increasing this even to
            just ``1`` can dramatically speed up suggestions, and may be
            justifiable since spellling mistakes rarely involve the first
            letter of a word.
        :param aliases: an optional dictionary mapping field names in the query
            to different field names to use as the source of spelling
            suggestions. The mappings in ``correctors`` are applied after this.
        :rtype: :class:`whoosh.spelling.Correction`
        """

        reader = self.reader()

        # Dictionary of field name alias mappings
        if aliases is None:
            aliases = {}
        # Dictionary of custom per-field correctors
        if correctors is None:
            correctors = {}

        # Remap correctors dict according to aliases
        d = {}
        for fieldname, corr in correctors.items():
            fieldname = aliases.get(fieldname, fieldname)
            d[fieldname] = corr
        correctors = d

        # Fill in default corrector objects for fields that don't have a custom
        # one in the "correctors" dictionary
        fieldnames = self.schema.names()
        for fieldname in fieldnames:
            fieldname = aliases.get(fieldname, fieldname)
            if fieldname not in correctors:
                correctors[fieldname] = self.reader().corrector(fieldname)

        # Get any missing terms in the query in the fields we're correcting
        if terms is None:
            terms = []
            for token in q.all_tokens():
                aname = aliases.get(token.fieldname, token.fieldname)
                text = token.text
                if aname in correctors and (aname, text) not in reader:
                    # Note that we use the original, not aliases fieldname here
                    # so if we correct the query we know what it was
                    terms.append((token.fieldname, token.text))

        # Make q query corrector
        from whoosh import spelling

        sqc = spelling.SimpleQueryCorrector(
            correctors, terms, aliases, maxdist=maxdist, prefix=prefix
        )
        return sqc.correct_query(q, qstring)
