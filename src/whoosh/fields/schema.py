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
"""The :class:`Schema`, :class:`SchemaClass`, and :class:`MetaSchema` types."""

import datetime
import fnmatch
import re
import struct
import sys
from array import array
from decimal import Decimal

from whoosh import analysis, columns, formats
from whoosh.fields.base import (
    FieldConfigurationError,
    FieldType,
    UnknownFieldError,
    ensure_schema,
    merge_fielddict,
    merge_schema,
    merge_schemas,
)
from whoosh.fields.numeric import BOOLEAN, COLUMN, DATETIME, ID, IDLIST, KEYWORD, NUMERIC, STORED
from whoosh.fields.text import NGRAM, NGRAMWORDS, TEXT, SpellField
from whoosh.fields.wrappers import FieldWrapper, ReverseField
from whoosh.system import emptybytes, pack_byte
from whoosh.util.numeric import NaN, from_sortable, to_sortable, typecode_max
from whoosh.util.text import utf8decode, utf8encode
from whoosh.util.times import datetime_to_long, long_to_datetime


class MetaSchema(type):
    _clsfields: dict = {}

    def __new__(cls, name, bases, attrs):
        super_new = super().__new__
        if not any(b for b in bases if isinstance(b, MetaSchema)):
            # If this isn't a subclass of MetaSchema, don't do anything special
            return super_new(cls, name, bases, attrs)

        # Create the class
        special_attrs = {}
        for key in list(attrs.keys()):
            if key.startswith("__"):
                special_attrs[key] = attrs.pop(key)
        new_class = super_new(cls, name, bases, special_attrs)

        fields = {}
        for b in bases:
            if hasattr(b, "_clsfields"):
                fields.update(b._clsfields)
        fields.update(attrs)
        new_class._clsfields = fields
        return new_class

    def schema(self):
        return Schema(**self._clsfields)


class Schema:
    """
    Represents the collection of fields in an index. Maps field names to
    FieldType objects which define the behavior of each field.

    Low-level parts of the index use field numbers instead of field names for
    compactness. This class has several methods for converting between the
    field name, field number, and field object itself.
    """

    def __init__(self, **fields):
        """
        All keyword arguments to the constructor are treated as fieldname =
        fieldtype pairs. The fieldtype can be an instantiated FieldType object,
        or a FieldType sub-class (in which case the Schema will instantiate it
        with the default constructor before adding it).

        For example::

            s = Schema(content = TEXT,
                       title = TEXT(stored = True),
                       tags = KEYWORD(stored = True))
        """

        self._fields = {}
        self._subfields = {}
        self._dyn_fields = {}
        self._name_to_number = {}

        for name in sorted(fields.keys()):
            self.add(name, fields[name])

        self.name_to_number = self._name_to_number

    def copy(self):
        """
        Returns a shallow copy of the schema. The field instances are not
        deep copied, so they are shared between schema copies.
        """

        return self.__class__(**self._fields)

    def __eq__(self, other):
        return other.__class__ is self.__class__ and list(self.items()) == list(other.items())

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.names()!r}>"

    def __iter__(self):
        """
        Returns the field objects in this schema.
        """

        return iter(self._fields.values())

    def __getitem__(self, name):
        """
        Returns the field associated with the given field name or number.
        """

        # Allow field numbers
        if isinstance(name, int):
            if name < 0 or name >= len(self._name_to_number):
                raise IndexError(f"No field number {name!r}")
            # Invert _name_to_number to get name from number
            num_to_name = {num: n for n, num in self._name_to_number.items()}
            name = num_to_name[name]

        # If the name is in the dictionary, just return it
        if name in self._fields:
            return self._fields[name]

        # Check if the name matches a dynamic field
        for expr, fieldtype in self._dyn_fields.values():
            if expr.match(name):
                return fieldtype

        raise KeyError(f"No field named {name!r}")

    def __len__(self):
        """
        Returns the number of fields in this schema.
        """

        return len(self._fields)

    def __contains__(self, fieldname):
        """
        Returns True if a field by the given name is in this schema.
        """

        # Defined in terms of __getitem__ so that there's only one method to
        # override to provide dynamic fields
        try:
            field = self[fieldname]
            return field is not None
        except KeyError:
            return False

    def __setstate__(self, state):
        if "_subfields" not in state:
            state["_subfields"] = {}
        self.__dict__.update(state)

    def to_bytes(self, fieldname, value):
        return self[fieldname].to_bytes(value)

    def items(self):
        """
        Returns a list of ("fieldname", field_object) pairs for the fields
        in this schema.
        """

        return sorted(self._fields.items())

    def names(self, check_names=None):
        """
        Returns a list of the names of the fields in this schema.

        :param check_names: (optional) sequence of field names to check
            whether the schema accepts them as (dynamic) field names -
            acceptable names will also be in the result list.
            Note: You may also have static field names in check_names, that
            won't create duplicates in the result list. Unsupported names
            will not be in the result list.
        """

        fieldnames = set(self._fields.keys())
        if check_names is not None:
            check_names = set(check_names) - fieldnames
            fieldnames.update(fieldname for fieldname in check_names if fieldname in self)
        return sorted(fieldnames)

    def clean(self):
        for field in self:
            field.clean()

    def add(self, name, fieldtype, glob=False):
        """
        Adds a field to this schema.

        :param name: The name of the field.
        :param fieldtype: An instantiated fields.FieldType object, or a
            FieldType subclass. If you pass an instantiated object, the schema
            will use that as the field configuration for this field. If you
            pass a FieldType subclass, the schema will automatically
            instantiate it with the default constructor.
        """

        # If the user passed a type rather than an instantiated field object,
        # instantiate it automatically
        if type(fieldtype) is type:
            try:
                fieldtype = fieldtype()
            except:
                e = sys.exc_info()[1]
                raise FieldConfigurationError(
                    f"Error: {e} instantiating field {name!r}: {fieldtype!r}"
                )

        if not isinstance(fieldtype, FieldType):
            raise FieldConfigurationError(f"{fieldtype!r} is not a FieldType object")

        self._subfields[name] = sublist = []
        for prefix, subfield in fieldtype.subfields():
            fname = prefix + name
            sublist.append(fname)

            # Check field name
            if fname.startswith("_"):
                raise FieldConfigurationError("Names cannot start with _")
            elif " " in fname:
                raise FieldConfigurationError("Names cannot contain spaces")
            elif fname in self._fields or (glob and fname in self._dyn_fields):
                raise FieldConfigurationError(f"{fname!r} already in schema")

            # Add the field
            if glob:
                expr = re.compile(fnmatch.translate(name))
                self._dyn_fields[fname] = (expr, subfield)
            else:
                fieldtype.on_add(self, fname)
                self._fields[fname] = subfield
                self._name_to_number[fname] = len(self._name_to_number)

    def remove(self, fieldname):
        if fieldname in self._fields:
            self._fields[fieldname].on_remove(self, fieldname)
            del self._fields[fieldname]

            if fieldname in self._subfields:
                for subname in self._subfields[fieldname]:
                    if subname in self._fields:
                        del self._fields[subname]
                del self._subfields[fieldname]

        elif fieldname in self._dyn_fields:
            del self._dyn_fields[fieldname]

        else:
            raise KeyError(f"No field named {fieldname!r}")

    def indexable_fields(self, fieldname):
        if fieldname in self._subfields:
            for subname in self._subfields[fieldname]:
                yield subname, self._fields[subname]
        else:
            # Use __getitem__ here instead of getting it directly from _fields
            # because it might be a glob
            yield fieldname, self[fieldname]

    def has_scorable_fields(self):
        return any(ftype.scorable for ftype in self)

    def stored_names(self):
        """
        Returns a list of the names of fields that are stored.
        """

        return [name for name, field in self.items() if field.stored]

    def scorable_names(self):
        """
        Returns a list of the names of fields that store field
        lengths.
        """

        return [name for name, field in self.items() if field.scorable]


class SchemaClass(Schema, metaclass=MetaSchema):
    """
    Allows you to define a schema using declarative syntax, similar to
    Django models::

        class MySchema(SchemaClass):
            path = ID
            date = DATETIME
            content = TEXT

    You can use inheritance to share common fields between schemas::

        class Parent(SchemaClass):
            path = ID(stored=True)
            date = DATETIME

        class Child1(Parent):
            content = TEXT(positions=False)

        class Child2(Parent):
            tags = KEYWORD

    This class overrides ``__new__`` so instantiating your sub-class always
    results in an instance of ``Schema``.

    >>> class MySchema(SchemaClass):
    ...     title = TEXT(stored=True)
    ...     content = TEXT
    ...
    >>> s = MySchema()
    >>> type(s)
    <class 'whoosh.fields.Schema'>

    """

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(Schema)
        kw = getattr(cls, "_clsfields", {}).copy()
        kw.update(kwargs)
        obj.__init__(*args, **kw)
        return obj

