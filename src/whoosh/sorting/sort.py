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
"""Sorting helpers."""

from array import array
from collections import defaultdict


def add_sortable(writer, fieldname, facet, column=None):
    """Adds a per-document value column to an existing field which was created
    without the ``sortable`` keyword argument.

    >>> from whoosh import index, sorting
    >>> ix = index.open_dir("indexdir")
    >>> with ix.writer() as w:
    ...   facet = sorting.FieldFacet("price")
    ...   sorting.add_sortable(w, "price", facet)
    ...

    :param writer: a :class:`whoosh.writing.IndexWriter` object.
    :param fieldname: the name of the field to add the per-document sortable
        values to. If this field doesn't exist in the writer's schema, the
        function will add a :class:`whoosh.fields.COLUMN` field to the schema,
        and you must specify the column object to using the ``column`` keyword
        argument.
    :param facet: a :class:`FacetType` object to use to generate the
        per-document values.
    :param column: a :class:`whosh.columns.ColumnType` object to use to store
        the per-document values. If you don't specify a column object, the
        function will use the default column type for the given field.
    """

    storage = writer.storage
    schema = writer.schema

    field = None
    if fieldname in schema:
        field = schema[fieldname]
        if field.column_type:
            raise Exception(f"{fieldname!r} field is already sortable")

    if column:
        if fieldname not in schema:
            from whoosh.fields import COLUMN

            field = COLUMN(column)
            schema.add(fieldname, field)
    else:
        if fieldname in schema:
            column = field.default_column()
        else:
            raise Exception(f"Field {fieldname!r} does not exist")

    searcher = writer.searcher()
    catter = facet.categorizer(searcher)
    for subsearcher, docoffset in searcher.leaf_searchers():
        catter.set_searcher(subsearcher, docoffset)
        reader = subsearcher.reader()

        if reader.has_column(fieldname):
            raise Exception(f"{fieldname!r} field already has a column")

        codec = reader.codec()
        segment = reader.segment()

        colname = codec.column_filename(segment, fieldname)
        colfile = storage.create_file(colname)
        try:
            colwriter = column.writer(colfile)
            for docnum in reader.all_doc_ids():
                v = catter.key_to_name(catter.key_for(None, docnum))
                cv = field.to_column_value(v)
                colwriter.add(docnum, cv)
            colwriter.finish(reader.doc_count_all())
        finally:
            colfile.close()

    field.column_type = column
