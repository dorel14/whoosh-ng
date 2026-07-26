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
"""The :class:`Hit` class representing a single search result."""

from whoosh import classify
from whoosh.searching._base import NoTermsException


class Hit:
    """Represents a single search result ("hit") in a Results object.

    This object acts like a dictionary of the matching document's stored
    fields. If for some reason you need an actual ``dict`` object, use
    ``Hit.fields()`` to get one.

    >>> r = searcher.search(query.Term("content", "render"))
    >>> r[0]
    < Hit {title = u"Rendering the scene"} >
    >>> r[0].rank
    0
    >>> r[0].docnum == 4592
    True
    >>> r[0].score
    2.52045682
    >>> r[0]["title"]
    "Rendering the scene"
    >>> r[0].keys()
    ["title"]
    """

    __slots__ = (
        "results",
        "searcher",
        "reader",
        "pos",
        "rank",
        "docnum",
        "score",
        "_fields",
    )

    def __init__(self, results, docnum, pos=None, score=None):
        """
        :param results: the Results object this hit belongs to.
        :param pos: the position in the results list of this hit, for example
            pos = 0 means this is the first (highest scoring) hit.
        :param docnum: the document number of this hit.
        :param score: the score of this hit.
        """

        self.results = results
        self.searcher = results.searcher
        self.reader = self.searcher.reader()
        self.pos = self.rank = pos
        self.docnum = docnum
        self.score = score
        self._fields = None

    def fields(self):
        """Returns a dictionary of the stored fields of the document this
        object represents.
        """

        if self._fields is None:
            self._fields = self.searcher.stored_fields(self.docnum)
        return self._fields

    def matched_terms(self):
        """Returns the set of ``("fieldname", "text")`` tuples representing
        terms from the query that matched in this document. You can
        compare this set to the terms from the original query to find terms
        which didn't occur in this document.

        This is only valid if you used ``terms=True`` in the search call to
        record matching terms. Otherwise it will raise an exception.

        >>> q = myparser.parse("alfa OR bravo OR charlie")
        >>> results = searcher.search(q, terms=True)
        >>> for hit in results:
        ...   print(hit["title"])
        ...   print("Contains:", hit.matched_terms())
        ...   print("Doesn't contain:", q.all_terms() - hit.matched_terms())
        """

        if not self.results.has_matched_terms():
            raise NoTermsException
        return self.results.docterms.get(self.docnum, [])

    def highlights(self, fieldname, text=None, top=3, minscore=1, strict_phrase=False):
        """Returns highlighted snippets from the given field::

            r = searcher.search(myquery)
            for hit in r:
                print(hit["title"])
                print(hit.highlights("content"))

        See :doc:`/highlight`.

        To change the fragmeter, formatter, order, or scorer used in
        highlighting, you can set attributes on the results object::

            from whoosh import highlight

            results = searcher.search(myquery, terms=True)
            results.fragmenter = highlight.SentenceFragmenter()

        ...or use a custom :class:`whoosh.highlight.Highlighter` object::

            hl = highlight.Highlighter(fragmenter=sf)
            results.highlighter = hl

        :param fieldname: the name of the field you want to highlight.
        :param text: by default, the method will attempt to load the contents
            of the field from the stored fields for the document. If the field
            you want to highlight isn't stored in the index, but you have
            access to the text another way (for example, loading from a file or
            a database), you can supply it using the ``text`` parameter.
        :param top: the maximum number of fragments to return.
        :param minscore: the minimum score for fragments to appear in the
            highlights.
        """

        hliter = self.results.highlighter
        return hliter.highlight_hit(
            self,
            fieldname,
            text=text,
            top=top,
            minscore=minscore,
            strict_phrase=strict_phrase,
        )

    def more_like_this(
        self,
        fieldname,
        text=None,
        top=10,
        numterms=5,
        model=classify.Bo1Model,
        normalize=True,
        filter=None,
    ):
        """Returns a new Results object containing documents similar to this
        hit, based on "key terms" in the given field::

            r = searcher.search(myquery)
            for hit in r:
                print(hit["title"])
                print("Top 3 similar documents:")
                for subhit in hit.more_like_this("content", top=3):
                  print("  ", subhit["title"])

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
        """

        return self.searcher.more_like(
            self.docnum,
            fieldname,
            text=text,
            top=top,
            numterms=numterms,
            model=model,
            normalize=normalize,
            filter=filter,
        )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.fields()!r}>"

    def __eq__(self, other):
        if isinstance(other, Hit):
            return self.fields() == other.fields()
        elif isinstance(other, dict):
            return self.fields() == other
        else:
            return False

    def __len__(self):
        return len(self.fields())

    def __iter__(self):
        return self.fields().keys()

    def __getitem__(self, fieldname):
        if fieldname in self.fields():
            return self._fields[fieldname]  # type: ignore[index]

        reader = self.reader
        if reader.has_column(fieldname):
            cr = reader.column_reader(fieldname)
            return cr[self.docnum]

        raise KeyError(fieldname)

    def __contains__(self, key):
        return key in self.fields() or self.reader.has_column(key)

    def items(self):
        return list(self.fields().items())

    def keys(self):
        return list(self.fields().keys())

    def values(self):
        return list(self.fields().values())

    def iteritems(self):
        return self.fields().items()

    def iterkeys(self):
        return self.fields().keys()

    def itervalues(self):
        return self.fields().values()

    def __delitem__(self, key):
        raise NotImplementedError("You cannot modify a search result")
