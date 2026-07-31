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
"""Numeric, date, boolean, identifier, stored, column, and keyword field types."""

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


class ID(FieldType):
    """
    Configured field type that indexes the entire value of the field as one
    token. This is useful for data you don't want to tokenize, such as the path
    of a file.
    """

    def __init__(self, stored=False, unique=False, field_boost=1.0, sortable=False, analyzer=None):
        """
        :param stored: Whether the value of this field is stored with the
            document.
        """

        self.analyzer = analyzer or analysis.IDAnalyzer()
        # Don't store any information other than the doc ID
        self.format = formats.Existence(field_boost=field_boost)
        self.stored = stored
        self.unique = unique
        self.set_sortable(sortable)


class IDLIST(FieldType):
    """
    Configured field type for fields containing IDs separated by whitespace
    and/or punctuation (or anything else, using the expression param).
    """

    def __init__(self, stored=False, unique=False, expression=None, field_boost=1.0):
        """
        :param stored: Whether the value of this field is stored with the
            document.
        :param unique: Whether the value of this field is unique per-document.
        :param expression: The regular expression object to use to extract
            tokens. The default expression breaks tokens on CRs, LFs, tabs,
            spaces, commas, and semicolons.
        """

        expression = expression or re.compile(r"[^\r\n\t ,;]+")
        self.analyzer = analysis.RegexAnalyzer(expression=expression)
        # Don't store any information other than the doc ID
        self.format = formats.Existence(field_boost=field_boost)
        self.stored = stored
        self.unique = unique


class NUMERIC(FieldType):
    """
    Special field type that lets you index integer or floating point
    numbers in relatively short fixed-width terms. The field converts numbers
    to sortable bytes for you before indexing.

    You specify the numeric type of the field (``int`` or ``float``) when you
    create the ``NUMERIC`` object. The default is ``int``. For ``int``, you can
    specify a size in bits (``32`` or ``64``). For both ``int`` and ``float``
    you can specify a ``signed`` keyword argument (default is ``True``).

    >>> schema = Schema(path=STORED, position=NUMERIC(int, 64, signed=False))
    >>> ix = storage.create_index(schema)
    >>> with ix.writer() as w:
    ...     w.add_document(path="/a", position=5820402204)
    ...

    You can also use the NUMERIC field to store Decimal instances by specifying
    a type of ``int`` or ``long`` and the ``decimal_places`` keyword argument.
    This simply multiplies each number by ``(10 ** decimal_places)`` before
    storing it as an integer. Of course this may throw away decimal prcesision
    (by truncating, not rounding) and imposes the same maximum value limits as
    ``int``/``long``, but these may be acceptable for certain applications.

    >>> from decimal import Decimal
    >>> schema = Schema(path=STORED, position=NUMERIC(int, decimal_places=4))
    >>> ix = storage.create_index(schema)
    >>> with ix.writer() as w:
    ...     w.add_document(path="/a", position=Decimal("123.45")
    ...

    """

    def __init__(
        self,
        numtype=int,
        bits=32,
        stored=False,
        unique=False,
        field_boost=1.0,
        decimal_places=0,
        shift_step=4,
        signed=True,
        sortable=False,
        default=None,
    ):
        """
        :param numtype: the type of numbers that can be stored in this field,
            either ``int``, ``float``. If you use ``Decimal``,
            use the ``decimal_places`` argument to control how many decimal
            places the field will store.
        :param bits: When ``numtype`` is ``int``, the number of bits to use to
            store the number: 8, 16, 32, or 64.
        :param stored: Whether the value of this field is stored with the
            document.
        :param unique: Whether the value of this field is unique per-document.
        :param decimal_places: specifies the number of decimal places to save
            when storing Decimal instances. If you set this, you will always
            get Decimal instances back from the field.
        :param shift_steps: The number of bits of precision to shift away at
            each tiered indexing level. Values should generally be 1-8. Lower
            values yield faster searches but take up more space. A value
            of `0` means no tiered indexing.
        :param signed: Whether the numbers stored in this field may be
            negative.
        """

        # Allow users to specify strings instead of Python types in case
        # docstring isn't clear
        if numtype == "int":
            numtype = int
        if numtype == "float":
            numtype = float
        # Raise an error if the user tries to use a type other than int or
        # float
        if numtype is Decimal:
            numtype = int
            if not decimal_places:
                raise TypeError(
                    "To store Decimal instances, you must set the decimal_places argument"
                )
        elif numtype not in (int, float):
            raise TypeError(f"Can't use {numtype!r} as a type, use int or float")
        # Sanity check
        if numtype is float and decimal_places:
            raise Exception(
                "A float type and decimal_places argument %r are incompatible" % decimal_places
            )

        intsizes = [8, 16, 32, 64]
        intcodes = ["B", "H", "I", "Q"]
        # Set up field configuration based on type and size
        if numtype is float:
            bits = 64  # Floats are converted to 64 bit ints
        else:
            if bits not in intsizes:
                raise Exception(f"Invalid bits {bits!r}, use 8, 16, 32, or 64")
        # Type code for the *sortable* representation
        self.sortable_typecode = intcodes[intsizes.index(bits)]
        self._struct = struct.Struct(">" + str(self.sortable_typecode))

        self.numtype = numtype
        self.bits = bits
        self.stored = stored
        self.unique = unique
        self.decimal_places = decimal_places
        self.shift_step = shift_step
        self.signed = signed
        self.analyzer = analysis.IDAnalyzer()
        # Don't store any information other than the doc ID
        self.format = formats.Existence(field_boost=field_boost)
        self.min_value, self.max_value = self._min_max()

        # Column configuration
        if default is None:
            if numtype is int:
                default = typecode_max[self.sortable_typecode]
            else:
                default = NaN
        elif not self.is_valid(default):
            raise Exception(f"The default {default!r} is not a valid number for this field")

        self.default = default
        self.set_sortable(sortable)

    def __getstate__(self):
        d = self.__dict__.copy()
        if "_struct" in d:
            del d["_struct"]
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self._struct = struct.Struct(">" + str(self.sortable_typecode))
        if "min_value" not in d:
            d["min_value"], d["max_value"] = self._min_max()

    def _min_max(self):
        numtype = self.numtype
        bits = self.bits
        signed = self.signed

        # Calculate the minimum and maximum possible values for error checking
        min_value = from_sortable(numtype, bits, signed, 0)
        max_value = from_sortable(numtype, bits, signed, 2**bits - 1)

        return min_value, max_value

    def default_column(self):
        return columns.NumericColumn(self.sortable_typecode, default=self.default)

    def is_valid(self, x):
        try:
            x = self.to_bytes(x)
        except ValueError:
            return False
        except OverflowError:
            return False

        return True

    def index(self, num, **kwargs):
        # If the user gave us a list of numbers, recurse on the list
        if isinstance(num, (list, tuple)):
            for n in num:
                yield from self.index(n)
            return

        # word, freq, weight, valuestring
        if self.shift_step:
            for shift in range(0, self.bits, self.shift_step):
                yield (self.to_bytes(num, shift), 1, 1.0, emptybytes)
        else:
            yield (self.to_bytes(num), 1, 1.0, emptybytes)

    def prepare_number(self, x):
        if x == emptybytes or x is None:
            return x

        dc = self.decimal_places
        if dc and isinstance(x, (str, Decimal)):
            x = Decimal(x) * (10**dc)
        elif isinstance(x, Decimal):
            raise TypeError(
                "Can't index a Decimal object unless you specified decimal_places on the field"
            )

        try:
            x = self.numtype(x)
        except OverflowError:
            raise ValueError(f"Value {x!r} overflowed number type {self.numtype!r}")

        if x < self.min_value or x > self.max_value:
            raise ValueError(
                "Numeric field value %s out of range [%s, %s]" % (x, self.min_value, self.max_value)
            )
        return x

    def unprepare_number(self, x):
        dc = self.decimal_places
        if dc:
            s = str(x)
            x = Decimal(s[:-dc] + "." + s[-dc:])
        return x

    def to_column_value(self, x):
        if isinstance(x, (list, tuple, array)):
            x = x[0]
        x = self.prepare_number(x)
        return to_sortable(self.numtype, self.bits, self.signed, x)

    def from_column_value(self, x):
        x = from_sortable(self.numtype, self.bits, self.signed, x)
        return self.unprepare_number(x)

    def to_bytes(self, x, shift=0):
        # Try to avoid re-encoding; this sucks because on Python 2 we can't
        # tell the difference between a string and encoded bytes, so we have
        # to require the user use unicode when they mean string
        if isinstance(x, bytes):
            return x

        if x == emptybytes or x is None:
            return self.sortable_to_bytes(0)

        x = self.prepare_number(x)
        x = to_sortable(self.numtype, self.bits, self.signed, x)
        return self.sortable_to_bytes(x, shift)

    def sortable_to_bytes(self, x, shift=0):
        if shift:
            x >>= shift
        return pack_byte(shift) + self._struct.pack(x)

    def from_bytes(self, bs):
        x = self._struct.unpack(bs[1:])[0]
        x = from_sortable(self.numtype, self.bits, self.signed, x)
        x = self.unprepare_number(x)
        return x

    def process_text(self, text, **kwargs):
        return (self.to_bytes(text),)

    def self_parsing(self):
        return True

    def parse_query(self, fieldname, qstring, boost=1.0):
        from whoosh import query
        from whoosh.qparser.common import QueryParserError

        if qstring == "*":
            return query.Every(fieldname, boost=boost)

        if not self.is_valid(qstring):
            raise QueryParserError(f"{qstring!r} is not a valid number")

        token = self.to_bytes(qstring)
        return query.Term(fieldname, token, boost=boost)

    def parse_range(self, fieldname, start, end, startexcl, endexcl, boost=1.0):
        from whoosh import query
        from whoosh.qparser.common import QueryParserError

        if start is not None:
            if not self.is_valid(start):
                raise QueryParserError(f"Range start {start!r} is not a valid number")
            start = self.prepare_number(start)
        if end is not None:
            if not self.is_valid(end):
                raise QueryParserError(f"Range end {end!r} is not a valid number")
            end = self.prepare_number(end)
        return query.NumericRange(fieldname, start, end, startexcl, endexcl, boost=boost)

    def sortable_terms(self, ixreader, fieldname):
        zero = b"\x00"
        for token in ixreader.lexicon(fieldname):
            if token[0:1] != zero:
                # Only yield the full-precision values
                break
            yield token


class DATETIME(NUMERIC):
    """
    Special field type that lets you index datetime objects. The field
    converts the datetime objects to sortable text for you before indexing.

    Since this field is based on Python's datetime module it shares all the
    limitations of that module, such as the inability to represent dates before
    year 1 in the proleptic Gregorian calendar. However, since this field
    stores datetimes as an integer number of microseconds, it could easily
    represent a much wider range of dates if the Python datetime implementation
    ever supports them.

    >>> schema = Schema(path=STORED, date=DATETIME)
    >>> ix = storage.create_index(schema)
    >>> w = ix.writer()
    >>> w.add_document(path="/a", date=datetime.now())
    >>> w.commit()
    """

    def __init__(self, stored=False, unique=False, sortable=False):
        """
        :param stored: Whether the value of this field is stored with the
            document.
        :param unique: Whether the value of this field is unique per-document.
        """

        super().__init__(int, 64, stored=stored, unique=unique, shift_step=8, sortable=sortable)

    def prepare_datetime(self, x):
        from whoosh.util.times import floor

        if isinstance(x, str):
            # For indexing, support same strings as for query parsing --
            # convert unicode to datetime object
            x = self._parse_datestring(x)
            x = floor(x)  # this makes most sense (unspecified = lowest)

        if isinstance(x, datetime.datetime):
            return datetime_to_long(x)
        elif isinstance(x, bytes):
            return x
        else:
            raise Exception(f"{x!r} is not a datetime")

    def to_column_value(self, x):
        if isinstance(x, bytes):
            raise Exception(f"{x!r} is not a datetime")
        if isinstance(x, (list, tuple)):
            x = x[0]
        return self.prepare_datetime(x)

    def from_column_value(self, x):
        return long_to_datetime(x)

    def to_bytes(self, x, shift=0):
        x = self.prepare_datetime(x)
        return NUMERIC.to_bytes(self, x, shift=shift)

    def from_bytes(self, bs):
        x = NUMERIC.from_bytes(self, bs)
        return long_to_datetime(x)

    def _parse_datestring(self, qstring):
        # This method parses a very simple datetime representation of the form
        # YYYY[MM[DD[hh[mm[ss[uuuuuu]]]]]]
        from whoosh.util.times import adatetime, fix, is_void

        qstring = qstring.replace(" ", "").replace("-", "").replace(".", "")
        year = month = day = hour = minute = second = microsecond = None
        if len(qstring) >= 4:
            year = int(qstring[:4])
        if len(qstring) >= 6:
            month = int(qstring[4:6])
        if len(qstring) >= 8:
            day = int(qstring[6:8])
        if len(qstring) >= 10:
            hour = int(qstring[8:10])
        if len(qstring) >= 12:
            minute = int(qstring[10:12])
        if len(qstring) >= 14:
            second = int(qstring[12:14])
        if len(qstring) == 20:
            microsecond = int(qstring[14:])

        at = fix(adatetime(year, month, day, hour, minute, second, microsecond))
        if is_void(at):
            raise Exception(f"{qstring!r} is not a parseable date")
        return at

    def parse_query(self, fieldname, qstring, boost=1.0):
        from whoosh import query
        from whoosh.util.times import is_ambiguous

        try:
            at = self._parse_datestring(qstring)
        except:
            e = sys.exc_info()[1]
            return query.error_query(e)

        if is_ambiguous(at):
            startnum = datetime_to_long(at.floor())
            endnum = datetime_to_long(at.ceil())
            return query.NumericRange(fieldname, startnum, endnum, boost=boost)
        else:
            return query.Term(fieldname, at, boost=boost)

    def parse_range(self, fieldname, start, end, startexcl, endexcl, boost=1.0):
        from whoosh import query

        if start is None and end is None:
            return query.Every(fieldname, boost=boost)

        if start is not None:
            startdt = self._parse_datestring(start).floor()
            start = datetime_to_long(startdt)

        if end is not None:
            enddt = self._parse_datestring(end).ceil()
            end = datetime_to_long(enddt)

        return query.NumericRange(fieldname, start, end, boost=boost)


class BOOLEAN(FieldType):
    """
    Special field type that lets you index boolean values (True and False).
    The field converts the boolean values to text for you before indexing.

    >>> schema = Schema(path=STORED, done=BOOLEAN)
    >>> ix = storage.create_index(schema)
    >>> w = ix.writer()
    >>> w.add_document(path="/a", done=False)
    >>> w.commit()
    """

    bytestrings = (b"f", b"t")
    trues = frozenset(["t", "true", "yes", "1"])
    falses = frozenset(["f", "false", "no", "0"])

    def __init__(self, stored=False, field_boost=1.0):
        """
        :param stored: Whether the value of this field is stored with the
            document.
        """

        self.stored = stored
        # Don't store any information other than the doc ID
        self.format = formats.Existence(field_boost=field_boost)

    def _obj_to_bool(self, x):
        # We special case strings such as "true", "false", "yes", "no", but
        # otherwise call bool() on the query value. This lets you pass objects
        # as query values and do the right thing.

        if isinstance(x, str) and x.lower() in self.trues:
            x = True
        elif isinstance(x, str) and x.lower() in self.falses:
            x = False
        else:
            x = bool(x)
        return x

    def to_bytes(self, x):
        if isinstance(x, bytes):
            return x
        elif isinstance(x, str):
            x = x.lower() in self.trues
        else:
            x = bool(x)
        bs = self.bytestrings[int(x)]
        return bs

    def index(self, bit, **kwargs):
        if isinstance(bit, str):
            bit = bit.lower() in self.trues
        else:
            bit = bool(bit)
        # word, freq, weight, valuestring
        return [(self.bytestrings[int(bit)], 1, 1.0, emptybytes)]

    def self_parsing(self):
        return True

    def parse_query(self, fieldname, qstring, boost=1.0):
        from whoosh import query

        if qstring == "*":
            return query.Every(fieldname, boost=boost)

        return query.Term(fieldname, self._obj_to_bool(qstring), boost=boost)


class STORED(FieldType):
    """
    Configured field type for fields you want to store but not index.
    """

    indexed = False
    stored = True

    def __init__(self):
        pass


class COLUMN(FieldType):
    """
    Configured field type for fields you want to store as a per-document
    value column but not index.
    """

    indexed = False
    stored = False

    def __init__(self, columnobj=None):
        if columnobj is None:
            columnobj = columns.VarBytesColumn()
        if not isinstance(columnobj, columns.Column):
            raise TypeError(f"{columnobj!r} is not a column object")
        self.column_type = columnobj

    def to_bytes(self, v):
        return v

    def from_bytes(self, b):
        return b


class KEYWORD(FieldType):
    """
    Configured field type for fields containing space-separated or
    comma-separated keyword-like data (such as tags). The default is to not
    store positional information (so phrase searching is not allowed in this
    field) and to not make the field scorable.
    """

    def __init__(
        self,
        stored=False,
        lowercase=False,
        commas=False,
        scorable=False,
        unique=False,
        field_boost=1.0,
        sortable=False,
        vector=None,
        analyzer=None,
    ):
        """
        :param stored: Whether to store the value of the field with the
            document.
        :param commas: Whether this is a comma-separated field. If this is False
            (the default), it is treated as a space-separated field.
        :param scorable: Whether this field is scorable.
        """

        if not analyzer:
            analyzer = analysis.KeywordAnalyzer(lowercase=lowercase, commas=commas)
        self.analyzer = analyzer

        # Store field lengths and weights along with doc ID
        self.format = formats.Frequency(field_boost=field_boost)
        self.scorable = scorable
        self.stored = stored
        self.unique = unique

        if isinstance(vector, formats.Format):
            self.vector = vector
        elif vector:
            self.vector = self.format
        else:
            self.vector = None

        if sortable:
            self.column_type = self.default_column()
