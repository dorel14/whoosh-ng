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
"""The :class:`ResultsPage` class for paged search results."""

from math import ceil

class ResultsPage:
    """Represents a single page out of a longer list of results, as returned
    by :func:`whoosh.searching.Searcher.search_page`. Supports a subset of the
    interface of the :class:`~whoosh.searching.Results` object, namely getting
    stored fields with __getitem__ (square brackets), iterating, and the
    ``score()`` and ``docnum()`` methods.

    The ``offset`` attribute contains the results number this page starts at
    (numbered from 0). For example, if the page length is 10, the ``offset``
    attribute on the second page will be ``10``.

    The ``pagecount`` attribute contains the number of pages available.

    The ``pagenum`` attribute contains the page number. This may be less than
    the page you requested if the results had too few pages. For example, if
    you do::

        ResultsPage(results, 5)

    but the results object only contains 3 pages worth of hits, ``pagenum``
    will be 3.

    The ``pagelen`` attribute contains the number of results on this page
    (which may be less than the page length you requested if this is the last
    page of the results).

    The ``total`` attribute contains the total number of hits in the results.

    >>> mysearcher = myindex.searcher()
    >>> pagenum = 2
    >>> page = mysearcher.find_page(pagenum, myquery)
    >>> print("Page %s of %s, results %s to %s of %s" %
    ...       (pagenum, page.pagecount, page.offset+1,
    ...        page.offset+page.pagelen, page.total))
    >>> for i, fields in enumerate(page):
    ...   print("%s. %r" % (page.offset + i + 1, fields))
    >>> mysearcher.close()

    To set highlighter attributes (for example ``formatter``), access the
    underlying :class:`Results` object::

        page.results.formatter = highlight.UppercaseFormatter()

    """

    __slots__ = (
        "results",
        "total",
        "pagecount",
        "pagenum",
        "offset",
        "pagelen",
    )

    def __init__(self, results, pagenum, pagelen=10):
        """
        :param results: a :class:`~whoosh.searching.Results` object.
        :param pagenum: which page of the results to use, numbered from ``1``.
        :param pagelen: the number of hits per page.
        """

        self.results = results
        self.total = len(results)

        if pagenum < 1:
            raise ValueError("pagenum must be >= 1")

        self.pagecount = int(ceil(self.total / pagelen))
        self.pagenum = min(self.pagecount, pagenum)

        offset = (self.pagenum - 1) * pagelen
        if (offset + pagelen) > self.total:
            pagelen = self.total - offset
        self.offset = offset
        self.pagelen = pagelen

    def __getitem__(self, n):
        offset = self.offset
        if isinstance(n, slice):
            start, stop, step = n.indices(self.pagelen)
            return self.results.__getitem__(slice(start + offset, stop + offset, step))
        else:
            return self.results.__getitem__(n + offset)

    def __iter__(self):
        return iter(self.results[self.offset : self.offset + self.pagelen])

    def __len__(self):
        return self.total

    def scored_length(self):
        return self.results.scored_length()

    def score(self, n):
        """Returns the score of the hit at the nth position on this page."""
        return self.results.score(n + self.offset)

    def docnum(self, n):
        """Returns the document number of the hit at the nth position on this
        page.
        """
        return self.results.docnum(n + self.offset)

    def is_last_page(self):
        """Returns True if this object represents the last page of results."""

        return self.pagecount == 0 or self.pagenum == self.pagecount