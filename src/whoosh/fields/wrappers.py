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
"""Field wrapper types."""

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

from whoosh.fields.base import FieldType


class FieldWrapper(FieldType):
    def __init__(self, subfield, prefix):
        if isinstance(subfield, type):
            subfield = subfield()
        self.subfield = subfield
        self.name_prefix = prefix

        # By default we'll copy all the subfield's attributes -- override these
        # in subclass constructor for things you want to change
        self.analyzer = subfield.analyzer
        self.format = subfield.format
        self.column_type = subfield.column_type
        self.scorable = subfield.scorable
        self.stored = subfield.stored
        self.unique = subfield.unique
        self.indexed = subfield.indexed
        self.vector = subfield.vector

    def __eq__(self, other):
        return self.subfield.__eq__(other)

    def __ne__(self, other):
        return self.subfield.__ne__(other)

    # Text

    # def index(self, value, boost=1.0, **kwargs):
    #     return self.subfield.index(value, boost, **kwargs)
    #
    # def tokenize(self, value, **kwargs):
    #     return self.subfield.tokenize(value, **kwargs)
    #
    # def process_text(self, qstring, mode='', **kwargs):
    #     return self.subfield.process_text(qstring, mode, **kwargs)

    # Conversion

    def to_bytes(self, value):
        return self.subfield.to_bytes(value)

    def to_column_value(self, value):
        return self.subfield.to_column_value(value)

    def from_bytes(self, bs):
        return self.subfield.from_bytes(bs)

    def from_column_value(self, value):
        return self.subfield.from_column_value(value)

    # Sorting/columns

    def set_sortable(self, sortable):
        self.subfield.set_sortable(sortable)

    def sortable_terms(self, ixreader, fieldname):
        return self.subfield.sortable_terms(ixreader, fieldname)

    def default_column(self):
        return self.subfield.default_column()

    # Parsing

    def self_parsing(self):
        return self.subfield.self_parsing()

    def parse_query(self, fieldname, qstring, boost=1.0):
        return self.subfield.parse_query(fieldname, qstring, boost)

    def parse_range(self, fieldname, start, end, startexcl, endexcl, boost=1.0):
        self.subfield.parse_range(fieldname, start, end, startexcl, endexcl, boost)

    # Utility

    def subfields(self):
        # The default FieldWrapper.subfields() implementation DOES NOT split
        # out the subfield here -- you need to override if that's what you want
        yield "", self

    def supports(self, name):
        return self.subfield.supports(name)

    def clean(self):
        self.subfield.clean()

    # Events

    def on_add(self, schema, fieldname):
        self.subfield.on_add(schema, fieldname)

    def on_remove(self, schema, fieldname):
        self.subfield.on_remove(schema, fieldname)


class ReverseField(FieldWrapper):
    def __init__(self, subfield, prefix="rev_"):
        FieldWrapper.__init__(self, subfield, prefix)
        self.analyzer = subfield.analyzer | analysis.ReverseTextFilter()

        self.scorable = False
        self.set_sortable(False)
        self.stored = False
        self.unique = False
        self.vector = False

    def subfields(self):
        yield "", self.subfield
        yield self.name_prefix, self
