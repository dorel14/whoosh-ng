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
"""Field type base class, exceptions, and schema merge helpers."""

import datetime
import fnmatch
import re
import struct
import sys
from array import array
from decimal import Decimal

from whoosh import analysis, columns, formats
from whoosh.system import emptybytes, pack_byte
from whoosh.util.numeric import NaN, from_sortable, to_sortable, typecode_max
from whoosh.util.text import utf8decode, utf8encode
from whoosh.util.times import datetime_to_long, long_to_datetime


class FieldConfigurationError(Exception):
    pass


class UnknownFieldError(Exception):
    pass


class FieldType:
    """
    Represents a field configuration.

    The FieldType object supports the following attributes:

    * format (formats.Format): the storage format for posting blocks.

    * analyzer (analysis.Analyzer): the analyzer to use to turn text into
      terms.

    * scorable (boolean): whether searches against this field may be scored.
      This controls whether the index stores per-document field lengths for
      this field.

    * stored (boolean): whether the content of this field is stored for each
      document. For example, in addition to indexing the title of a document,
      you usually want to store the title so it can be presented as part of
      the search results.

    * unique (boolean): whether this field's value is unique to each document.
      For example, 'path' or 'ID'. IndexWriter.update_document() will use
      fields marked as 'unique' to find the previous version of a document
      being updated.

    * multitoken_query is a string indicating what kind of query to use when
      a "word" in a user query parses into multiple tokens. The string is
      interpreted by the query parser. The strings understood by the default
      query parser are "first" (use first token only), "and" (join the tokens
      with an AND query), "or" (join the tokens with OR), "phrase" (join
      the tokens with a phrase query), and "default" (use the query parser's
      default join type).

    * vector (formats.Format or boolean): the format to use to store term
        vectors. If not a ``Format`` object, any true value means to use the
        index format as the term vector format. Any flase value means don't
        store term vectors for this field.

    The constructor for the base field type simply lets you supply your own
    attribute values.  Subclasses may configure some or all of this for you.
    """

    analyzer = format = scorable = stored = unique = vector = None
    indexed = True
    multitoken_query = "default"
    sortable_typecode = None
    column_type = None

    def __init__(
        self,
        format,
        analyzer,
        scorable=False,
        stored=False,
        unique=False,
        multitoken_query="default",
        sortable=False,
        vector=None,
    ):
        self.format = format
        self.analyzer = analyzer
        self.scorable = scorable
        self.stored = stored
        self.unique = unique
        self.multitoken_query = multitoken_query
        self.set_sortable(sortable)

        if isinstance(vector, formats.Format):
            self.vector = vector
        elif vector:
            self.vector = self.format
        else:
            self.vector = None

    def __repr__(self):
        return f"{self.__class__.__name__}(format={self.format!r}, scorable={self.scorable}, stored={self.stored}, unique={self.unique})"

    def __eq__(self, other):
        return all(
            (
                isinstance(other, FieldType),
                (self.format == other.format),
                (self.scorable == other.scorable),
                (self.stored == other.stored),
                (self.unique == other.unique),
                (self.column_type == other.column_type),
            )
        )

    def __ne__(self, other):
        return not (self.__eq__(other))

    # Text

    def index(self, value, **kwargs):
        """Returns an iterator of (btext, frequency, weight, encoded_value)
        tuples for each unique word in the input value.

        The default implementation uses the ``analyzer`` attribute to tokenize
        the value into strings, then encodes them into bytes using UTF-8.
        """

        if not self.format:
            raise Exception(
                "%s field %r cannot index without a format" % (self.__class__.__name__, self)
            )
        if not isinstance(value, (str, list, tuple)):
            raise ValueError(f"{value!r} is not unicode or sequence")
        assert isinstance(self.format, formats.Format)

        if "mode" not in kwargs:
            kwargs["mode"] = "index"

        word_values = self.format.word_values
        ana = self.analyzer
        for tstring, freq, wt, vbytes in word_values(value, ana, **kwargs):
            yield (utf8encode(tstring)[0], freq, wt, vbytes)

    def tokenize(self, value, **kwargs):
        """
        Analyzes the given string and returns an iterator of Token objects
        (note: for performance reasons, actually the same token yielded over
        and over with different attributes).
        """

        if not self.analyzer:
            raise Exception(f"{self.__class__} field has no analyzer")
        return self.analyzer(value, **kwargs)

    def process_text(self, qstring, mode="", **kwargs):
        """
        Analyzes the given string and returns an iterator of token texts.

        >>> field = fields.TEXT()
        >>> list(field.process_text("The ides of March"))
        ["ides", "march"]
        """

        if not self.format:
            raise Exception(f"{self} field has no format")
        return (t.text for t in self.tokenize(qstring, mode=mode, **kwargs))

    # Conversion

    def to_bytes(self, value):
        """
        Returns a bytes representation of the given value, appropriate to be
        written to disk. The default implementation assumes a unicode value and
        encodes it using UTF-8.
        """

        if isinstance(value, (list, tuple)):
            value = value[0]
        if not isinstance(value, bytes):
            value = utf8encode(value)[0]
        return value

    def to_column_value(self, value):
        """
        Returns an object suitable to be inserted into the document values
        column for this field. The default implementation simply calls
        ``self.to_bytes(value)``.
        """

        return self.to_bytes(value)

    def from_bytes(self, bs):
        return utf8decode(bs)[0]

    def from_column_value(self, value):
        return self.from_bytes(value)

    # Columns/sorting

    def set_sortable(self, sortable):
        if sortable:
            if isinstance(sortable, columns.Column):
                self.column_type = sortable
            else:
                self.column_type = self.default_column()
        else:
            self.column_type = None

    def sortable_terms(self, ixreader, fieldname):
        """
        Returns an iterator of the "sortable" tokens in the given reader and
        field. These values can be used for sorting. The default implementation
        simply returns all tokens in the field.

        This can be overridden by field types such as NUMERIC where some values
        in a field are not useful for sorting.
        """

        return ixreader.lexicon(fieldname)

    def default_column(self):
        return columns.VarBytesColumn()

    # Parsing

    def self_parsing(self):
        """
        Subclasses should override this method to return True if they want
        the query parser to call the field's ``parse_query()`` method instead
        of running the analyzer on text in this field. This is useful where
        the field needs full control over how queries are interpreted, such
        as in the numeric field type.
        """

        return False

    def parse_query(self, fieldname, qstring, boost=1.0):
        """
        When ``self_parsing()`` returns True, the query parser will call
        this method to parse basic query text.
        """

        raise NotImplementedError(self.__class__.__name__)

    def parse_range(self, fieldname, start, end, startexcl, endexcl, boost=1.0):
        """
        When ``self_parsing()`` returns True, the query parser will call
        this method to parse range query text. If this method returns None
        instead of a query object, the parser will fall back to parsing the
        start and end terms using process_text().
        """

        return None

    # Spelling

    def separate_spelling(self):
        """
        Returns True if the field stores unstemmed words in a separate field for
        spelling suggestions.
        """

        return False

    def spelling_fieldname(self, fieldname):
        """
        Returns the name of a field to use for spelling suggestions instead of
        this field.

        :param fieldname: the name of this field.
        """

        return fieldname

    def spellable_words(self, value):
        """Returns an iterator of each unique word (in sorted order) in the
        input value, suitable for inclusion in the field's word graph.

        The default behavior is to call the field analyzer with the keyword
        argument ``no_morph=True``, which should make the analyzer skip any
        morphological transformation filters (e.g. stemming) to preserve the
        original form of the words. Exotic field types may need to override
        this behavior.
        """

        if isinstance(value, (list, tuple)):
            words = value
        else:
            words = [token.text for token in self.analyzer(value, no_morph=True)]

        return iter(sorted(set(words)))

    # Utility

    def subfields(self):
        """
        Returns an iterator of ``(name_prefix, fieldobject)`` pairs for the
        fields that need to be indexed when content is put in this field. The
        default implementation simply yields ``("", self)``.
        """

        yield "", self

    def supports(self, name):
        """
        Returns True if the underlying format supports the given posting
        value type.

        >>> field = TEXT()
        >>> field.supports("positions")
        True
        >>> field.supports("chars")
        False
        """

        return self.format.supports(name)

    def clean(self):
        """
        Clears any cached information in the field and any child objects.
        """

        if self.format and hasattr(self.format, "clean"):
            self.format.clean()

    # Events

    def on_add(self, schema, fieldname):
        pass

    def on_remove(self, schema, fieldname):
        pass


def ensure_schema(schema):
    from whoosh.fields.schema import Schema

    if isinstance(schema, type) and issubclass(schema, Schema):
        schema = schema.schema()
    if not isinstance(schema, Schema):
        raise FieldConfigurationError(f"{schema!r} is not a Schema")
    return schema


def merge_fielddict(d1, d2):
    keyset = set(d1.keys()) | set(d2.keys())
    out = {}
    for name in keyset:
        field1 = d1.get(name)
        field2 = d2.get(name)
        if field1 and field2 and field1 != field2:
            raise Exception(f"Inconsistent field {name!r}: {field1!r} != {field2!r}")
        out[name] = field1 or field2
    return out


def merge_schema(s1, s2):
    from whoosh.fields.schema import Schema

    schema = Schema()
    schema._fields = merge_fielddict(s1._fields, s2._fields)
    schema._dyn_fields = merge_fielddict(s1._dyn_fields, s2._dyn_fields)
    return schema


def merge_schemas(schemas):
    from whoosh.fields.schema import Schema

    schema = schemas[0]
    for i in range(1, len(schemas)):
        schema = merge_schema(schema, schemas[i])
    return schema
