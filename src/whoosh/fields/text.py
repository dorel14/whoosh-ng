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
"""Text-based field types."""

import datetime
import fnmatch
import re
import struct
import sys
from array import array
from decimal import Decimal

from whoosh import analysis, columns, formats
from whoosh.fields.base import FieldType
from whoosh.system import emptybytes, pack_byte
from whoosh.util.numeric import NaN, from_sortable, to_sortable, typecode_max
from whoosh.util.text import utf8decode, utf8encode
from whoosh.util.times import datetime_to_long, long_to_datetime


class TEXT(FieldType):
    """
    Configured field type for text fields (for example, the body text of an
    article). The default is to store positional information to allow phrase
    searching. This field type is always scorable.
    """

    def __init__(
        self,
        analyzer=None,
        phrase=True,
        chars=False,
        stored=False,
        field_boost=1.0,
        multitoken_query="default",
        spelling=False,
        sortable=False,
        lang=None,
        vector=None,
        spelling_prefix="spell_",
    ):
        """
        :param analyzer: The analysis.Analyzer to use to index the field
            contents. See the analysis module for more information. If you omit
            this argument, the field uses analysis.StandardAnalyzer.
        :param phrase: Whether the store positional information to allow phrase
            searching.
        :param chars: Whether to store character ranges along with positions.
            If this is True, "phrase" is also implied.
        :param stored: Whether to store the value of this field with the
            document. Since this field type generally contains a lot of text,
            you should avoid storing it with the document unless you need to,
            for example to allow fast excerpts in the search results.
        :param spelling: if True, and if the field's analyzer changes the form
            of term text (such as a stemming analyzer), this field will store
            extra information in a separate field (named using the
            ``spelling_prefix`` keyword argument) to allow spelling suggestions
            to use the unchanged word forms as spelling suggestions.
        :param sortable: If True, make this field sortable using the default
            column type. If you pass a :class:`whoosh.columns.Column` instance
            instead of True, the field will use the given column type.
        :param lang: automaticaly configure a
            :class:`whoosh.analysis.LanguageAnalyzer` for the given language.
            This is ignored if you also specify an ``analyzer``.
        :param vector: if this value evaluates to true, store a list of the
            terms in this field in each document. If the value is an instance
            of :class:`whoosh.formats.Format`, the index will use the object to
            store the term vector. Any other true value (e.g. ``vector=True``)
            will use the field's index format to store the term vector as well.
        """

        if analyzer:
            self.analyzer = analyzer
        elif lang:
            self.analyzer = analysis.LanguageAnalyzer(lang)
        else:
            self.analyzer = analysis.StandardAnalyzer()

        if chars:
            formatclass = formats.Characters
        elif phrase:
            formatclass = formats.Positions
        else:
            formatclass = formats.Frequency
        self.format = formatclass(field_boost=field_boost)

        if sortable:
            if isinstance(sortable, columns.Column):
                self.column_type = sortable
            else:
                self.column_type = columns.VarBytesColumn()
        else:
            self.column_type = None

        self.spelling = spelling
        self.spelling_prefix = spelling_prefix
        self.multitoken_query = multitoken_query
        self.scorable = True
        self.stored = stored

        if isinstance(vector, formats.Format):
            self.vector = vector
        elif vector:
            self.vector = self.format
        else:
            self.vector = None

    def subfields(self):
        yield "", self

        # If the user indicated this is a spellable field, and the analyzer
        # is morphic, then also index into a spelling-only field that stores
        # minimal information
        if self.separate_spelling():
            yield self.spelling_prefix, SpellField(self.analyzer)

    def separate_spelling(self):
        return self.spelling and self.analyzer.has_morph()

    def spelling_fieldname(self, fieldname):
        if self.separate_spelling():
            return self.spelling_prefix + fieldname
        else:
            return fieldname


class SpellField(FieldType):
    """
    This is a utility field type meant to be returned by ``TEXT.subfields()``
    when it needs a minimal field to store the spellable words.
    """

    def __init__(self, analyzer):
        self.format = formats.Frequency()
        self.analyzer = analyzer
        self.column_type = None
        self.scorabe = False
        self.stored = False
        self.unique = False
        self.indexed = True
        self.spelling = False

    # All the text analysis methods add "nomorph" to the keywords to get
    # unmorphed term texts

    def index(self, value, boost=1.0, **kwargs):
        kwargs["nomorph"] = True
        return FieldType.index(self, value, boost=boost, **kwargs)

    def tokenzie(self, value, **kwargs):
        kwargs["nomorph"] = True
        return FieldType.tokenize(self, value, **kwargs)

    def process_text(self, qstring, mode="", **kwargs):
        kwargs["nomorph"] = True
        return FieldType.process_text(self, qstring, mode=mode, **kwargs)


class NGRAM(FieldType):
    """
    Configured field that indexes text as N-grams. For example, with a field
    type NGRAM(3,4), the value "hello" will be indexed as tokens
    "hel", "hell", "ell", "ello", "llo". This field type chops the entire text
    into N-grams, including whitespace and punctuation. See :class:`NGRAMWORDS`
    for a field type that breaks the text into words first before chopping the
    words into N-grams.
    """

    scorable = True

    def __init__(
        self,
        minsize=2,
        maxsize=4,
        stored=False,
        field_boost=1.0,
        queryor=False,
        phrase=False,
        sortable=False,
    ):
        """
        :param minsize: The minimum length of the N-grams.
        :param maxsize: The maximum length of the N-grams.
        :param stored: Whether to store the value of this field with the
            document. Since this field type generally contains a lot of text,
            you should avoid storing it with the document unless you need to,
            for example to allow fast excerpts in the search results.
        :param queryor: if True, combine the N-grams with an Or query. The
            default is to combine N-grams with an And query.
        :param phrase: store positions on the N-grams to allow exact phrase
            searching. The default is off.
        """

        formatclass = formats.Frequency
        if phrase:
            formatclass = formats.Positions

        self.analyzer = analysis.NgramAnalyzer(minsize, maxsize)
        self.format = formatclass(field_boost=field_boost)
        self.analyzer = analysis.NgramAnalyzer(minsize, maxsize)
        self.stored = stored
        self.queryor = queryor
        self.set_sortable(sortable)

    def self_parsing(self):
        return True

    def parse_query(self, fieldname, qstring, boost=1.0):
        from whoosh import query

        terms = []
        for g in self.process_text(qstring, mode="query"):
            if g == "*":
                terms.append(query.Wildcard(fieldname, g, boost=boost))
            else:
                terms.append(query.Term(fieldname, g, boost=boost))
        cls = query.Or if self.queryor else query.And

        return cls(terms, boost=boost)


class NGRAMWORDS(NGRAM):
    """
    Configured field that chops text into words using a tokenizer,
    lowercases the words, and then chops the words into N-grams.
    """

    scorable = True

    def __init__(
        self,
        minsize=2,
        maxsize=4,
        stored=False,
        field_boost=1.0,
        tokenizer=None,
        at=None,
        queryor=False,
        sortable=False,
    ):
        """
        :param minsize: The minimum length of the N-grams.
        :param maxsize: The maximum length of the N-grams.
        :param stored: Whether to store the value of this field with the
            document. Since this field type generally contains a lot of text,
            you should avoid storing it with the document unless you need to,
            for example to allow fast excerpts in the search results.
        :param tokenizer: an instance of :class:`whoosh.analysis.Tokenizer`
            used to break the text into words.
        :param at: if 'start', only takes N-grams from the start of the word.
            If 'end', only takes N-grams from the end. Otherwise the default
            is to take all N-grams from each word.
        :param queryor: if True, combine the N-grams with an Or query. The
            default is to combine N-grams with an And query.
        """

        self.analyzer = analysis.NgramWordAnalyzer(minsize, maxsize, tokenizer, at=at)
        self.format = formats.Frequency(field_boost=field_boost)
        self.stored = stored
        self.queryor = queryor
        self.set_sortable(sortable)
