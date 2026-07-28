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
"""The :class:`SegmentReader` and :class:`EmptyReader` classes."""

from abc import abstractmethod
from bisect import bisect_right
from heapq import heapify, heappop, heapreplace, nlargest
from math import log

from cached_property import cached_property

from whoosh import columns
from whoosh.filedb.filestore import OverlayStorage
from whoosh.matching import MultiMatcher
from whoosh.reading._base import ReaderClosed, TermNotFound
from whoosh.reading.index_reader import IndexReader
from whoosh.support.levenshtein import distance
from whoosh.system import emptybytes


class SegmentReader(IndexReader):
    def __init__(self, storage, schema, segment, generation=None, codec=None):
        self.schema = schema
        self.is_closed = False

        self._segment = segment
        self._segid = self._segment.segment_id()
        self._gen = generation

        # self.files is a storage object from which to load the segment files.
        # This is different from the general storage (which will be used for
        # caches) if the segment is in a compound file.
        if segment.is_compound():
            # Open the compound file as a storage object
            files = segment.open_compound_file(storage)
            # Use an overlay here instead of just the compound storage, in rare
            # circumstances a segment file may be added after the segment is
            # written
            self._storage = OverlayStorage(files, storage)
        else:
            self._storage = storage

        # Get subreaders from codec
        self._codec = codec if codec else segment.codec()
        self._terms = self._codec.terms_reader(self._storage, segment)
        self._perdoc = self._codec.per_document_reader(self._storage, segment)

    def codec(self):
        return self._codec

    def segment(self):
        return self._segment

    def segments(self):
        return [self.segment()]

    def storage(self):
        return self._storage

    def has_deletions(self):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.has_deletions()

    def doc_count(self):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.doc_count()

    def doc_count_all(self):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.doc_count_all()

    def is_deleted(self, docnum):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.is_deleted(docnum)

    def generation(self):
        return self._gen

    def __repr__(self):
        return f"{self.__class__.__name__}({self._storage!r}, {self._segment!r})"

    def __contains__(self, term):
        if self.is_closed:
            raise ReaderClosed
        fieldname, text = term
        if fieldname not in self.schema:
            return False
        text = self._text_to_bytes(fieldname, text)
        return (fieldname, text) in self._terms

    def close(self):
        if self.is_closed:
            raise ReaderClosed("Reader already closed")
        self._terms.close()
        self._perdoc.close()

        # It's possible some weird codec that doesn't use storage might have
        # passed None instead of a storage object
        if self._storage:
            self._storage.close()

        self.is_closed = True

    def stored_fields(self, docnum):
        if self.is_closed:
            raise ReaderClosed
        assert docnum >= 0
        schema = self.schema
        sfs = self._perdoc.stored_fields(docnum)
        # Double-check with schema to filter out removed fields
        return dict(item for item in sfs.items() if item[0] in schema)

    # Delegate doc methods to the per-doc reader

    def all_doc_ids(self):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.all_doc_ids()

    def iter_docs(self):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.iter_docs()

    def all_stored_fields(self):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.all_stored_fields()

    def field_length(self, fieldname):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.field_length(fieldname)

    def min_field_length(self, fieldname):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.min_field_length(fieldname)

    def max_field_length(self, fieldname):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.max_field_length(fieldname)

    def doc_field_length(self, docnum, fieldname, default=0):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.doc_field_length(docnum, fieldname, default)

    def has_vector(self, docnum, fieldname):
        if self.is_closed:
            raise ReaderClosed
        return self._perdoc.has_vector(docnum, fieldname)

    #

    def _test_field(self, fieldname):
        if self.is_closed:
            raise ReaderClosed
        if fieldname not in self.schema:
            raise TermNotFound(f"No field {fieldname!r}")
        if self.schema[fieldname].format is None:
            raise TermNotFound(f"Field {fieldname!r} is not indexed")

    def indexed_field_names(self):
        return self._terms.indexed_field_names()

    def all_terms(self):
        if self.is_closed:
            raise ReaderClosed
        schema = self.schema
        return ((fieldname, text) for fieldname, text in self._terms.terms() if fieldname in schema)

    def terms_from(self, fieldname, prefix):
        self._test_field(fieldname)
        prefix = self._text_to_bytes(fieldname, prefix)
        schema = self.schema
        return (
            (fname, text)
            for fname, text in self._terms.terms_from(fieldname, prefix)
            if fname in schema
        )

    def term_info(self, fieldname, text):
        self._test_field(fieldname)
        text = self._text_to_bytes(fieldname, text)
        try:
            return self._terms.term_info(fieldname, text)
        except KeyError:
            raise TermNotFound(f"{fieldname}:{text!r}")

    def expand_prefix(self, fieldname, prefix):
        self._test_field(fieldname)
        prefix = self._text_to_bytes(fieldname, prefix)
        return IndexReader.expand_prefix(self, fieldname, prefix)

    def lexicon(self, fieldname):
        self._test_field(fieldname)
        return IndexReader.lexicon(self, fieldname)

    def __iter__(self):
        if self.is_closed:
            raise ReaderClosed
        schema = self.schema
        return ((term, terminfo) for term, terminfo in self._terms.items() if term[0] in schema)

    def iter_from(self, fieldname, text):
        self._test_field(fieldname)
        schema = self.schema
        text = self._text_to_bytes(fieldname, text)
        for term, terminfo in self._terms.items_from(fieldname, text):
            if term[0] not in schema:
                continue
            yield (term, terminfo)

    def frequency(self, fieldname, text):
        self._test_field(fieldname)
        text = self._text_to_bytes(fieldname, text)
        try:
            return self._terms.frequency(fieldname, text)
        except KeyError:
            return 0

    def doc_frequency(self, fieldname, text):
        self._test_field(fieldname)
        text = self._text_to_bytes(fieldname, text)
        try:
            return self._terms.doc_frequency(fieldname, text)
        except KeyError:
            return 0

    @cached_property
    def deleted_docs_set(self):
        return frozenset(self._perdoc.deleted_docs())

    def postings(self, fieldname, text, scorer=None):
        from whoosh.matching.wrappers import FilterMatcher

        if self.is_closed:
            raise ReaderClosed
        if fieldname not in self.schema:
            raise TermNotFound(f"No  field {fieldname!r}")
        text = self._text_to_bytes(fieldname, text)
        format_ = self.schema[fieldname].format
        matcher = self._terms.matcher(fieldname, text, format_, scorer=scorer)
        deleted = self.deleted_docs_set
        if deleted:
            matcher = FilterMatcher(matcher, deleted, exclude=True)
        return matcher

    def vector(self, docnum, fieldname, format_=None):
        if self.is_closed:
            raise ReaderClosed
        if fieldname not in self.schema:
            raise TermNotFound(f"No  field {fieldname!r}")
        vformat = format_ or self.schema[fieldname].vector
        if not vformat:
            raise Exception(f"No vectors are stored for field {fieldname!r}")
        return self._perdoc.vector(docnum, fieldname, vformat)

    def cursor(self, fieldname):
        if self.is_closed:
            raise ReaderClosed
        fieldobj = self.schema[fieldname]
        return self._terms.cursor(fieldname, fieldobj)

    def terms_within(self, fieldname, text, maxdist, prefix=0):
        # Replaces the horribly inefficient base implementation with one based
        # on skipping through the word list efficiently using a DFA

        fieldobj = self.schema[fieldname]
        spellfield = fieldobj.spelling_fieldname(fieldname)
        auto = self._codec.automata(self._storage, self._segment)
        fieldcur = self.cursor(spellfield)
        return auto.terms_within(fieldcur, text, maxdist, prefix)

    # Column methods

    def has_column(self, fieldname):
        if self.is_closed:
            raise ReaderClosed
        coltype = self.schema[fieldname].column_type
        return coltype and self._perdoc.has_column(fieldname)

    def column_reader(self, fieldname, column=None, reverse=False, translate=True):
        if self.is_closed:
            raise ReaderClosed

        fieldobj = self.schema[fieldname]
        column = column or fieldobj.column_type
        if not column:
            raise Exception(f"No column for field {fieldname!r} in {self!r}")

        if self._perdoc.has_column(fieldname):
            creader = self._perdoc.column_reader(fieldname, column)
            if reverse:
                creader.set_reverse()
        else:
            # This segment doesn't have a column file for this field, so create
            # a fake column reader that always returns the default value.
            default = column.default_value(reverse)
            creader = columns.EmptyColumnReader(default, self.doc_count_all())

        if translate:
            # Wrap the column in a Translator to give the caller
            # nice values instead of sortable representations
            fcv = fieldobj.from_column_value
            creader = columns.TranslatingColumnReader(creader, fcv)

        return creader


class EmptyReader(IndexReader):
    def __init__(self, schema):
        self.schema = schema

    def __contains__(self, term):
        return False

    def __iter__(self):
        return iter([])

    def segments(self):
        return None

    def cursor(self, fieldname):
        from whoosh.codec.base import EmptyCursor

        return EmptyCursor()

    def indexed_field_names(self):
        return []

    def all_terms(self):
        return iter([])

    def term_info(self, fieldname, text):
        raise TermNotFound((fieldname, text))

    def iter_from(self, fieldname, text):
        return iter([])

    def iter_field(self, fieldname, prefix=""):
        return iter([])

    def iter_prefix(self, fieldname, prefix=""):
        return iter([])

    def lexicon(self, fieldname):
        return iter([])

    def has_deletions(self):
        return False

    def is_deleted(self, docnum):
        return False

    def stored_fields(self, docnum):
        raise KeyError(f"No document number {docnum}")

    def all_stored_fields(self):
        return iter([])

    def doc_count_all(self):
        return 0

    def doc_count(self):
        return 0

    def frequency(self, fieldname, text):
        return 0

    def doc_frequency(self, fieldname, text):
        return 0

    def field_length(self, fieldname):
        return 0

    def min_field_length(self, fieldname):
        return 0

    def max_field_length(self, fieldname):
        return 0

    def doc_field_length(self, docnum, fieldname, default=0):
        return default

    def postings(self, fieldname, text, scorer=None):
        raise TermNotFound(f"{fieldname}:{text!r}")

    def has_vector(self, docnum, fieldname):
        return False

    def vector(self, docnum, fieldname, format_=None):
        raise KeyError(f"No document number {docnum}")

    def most_frequent_terms(self, fieldname, number=5, prefix=""):
        return iter([])

    def most_distinctive_terms(self, fieldname, number=5, prefix=None):
        return iter([])

