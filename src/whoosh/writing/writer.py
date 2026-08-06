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
"""The :class:`IndexWriter` base class and helper functions."""

from abc import abstractmethod

from whoosh.writing._base import IndexingError, groupmanager


class IndexWriter:
    """High-level object for writing to an index.

    To get a writer for a particular index, call
    :meth:`~whoosh.index.Index.writer` on the Index object.

    >>> writer = myindex.writer()

    You can use this object as a context manager. If an exception is thrown
    from within the context it calls :meth:`~IndexWriter.cancel` to clean up
    temporary files, otherwise it calls :meth:`~IndexWriter.commit` when the
    context exits.

    >>> with myindex.writer() as w:
    ...     w.add_document(title="First document", content="Hello there.")
    ...     w.add_document(title="Second document", content="This is easy!")
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.cancel()
        else:
            self.commit()

    def group(self):
        """Returns a context manager that calls
        :meth:`~IndexWriter.start_group` and :meth:`~IndexWriter.end_group` for
        you, allowing you to use a ``with`` statement to group hierarchical
        documents::

            with myindex.writer() as w:
                with w.group():
                    w.add_document(kind="class", name="Accumulator")
                    w.add_document(kind="method", name="add")
                    w.add_document(kind="method", name="get_result")
                    w.add_document(kind="method", name="close")

                with w.group():
                    w.add_document(kind="class", name="Calculator")
                    w.add_document(kind="method", name="add")
                    w.add_document(kind="method", name="multiply")
                    w.add_document(kind="method", name="get_result")
                    w.add_document(kind="method", name="close")
        """

        return groupmanager(self)

    def start_group(self):
        """Start indexing a group of hierarchical documents. The backend should
        ensure that these documents are all added to the same segment::

            with myindex.writer() as w:
                w.start_group()
                w.add_document(kind="class", name="Accumulator")
                w.add_document(kind="method", name="add")
                w.add_document(kind="method", name="get_result")
                w.add_document(kind="method", name="close")
                w.end_group()

                w.start_group()
                w.add_document(kind="class", name="Calculator")
                w.add_document(kind="method", name="add")
                w.add_document(kind="method", name="multiply")
                w.add_document(kind="method", name="get_result")
                w.add_document(kind="method", name="close")
                w.end_group()

        A more convenient way to group documents is to use the
        :meth:`~IndexWriter.group` method and the ``with`` statement.
        """

        pass

    def end_group(self):
        """Finish indexing a group of hierarchical documents. See
        :meth:`~IndexWriter.start_group`.
        """

        pass

    def add_field(self, fieldname, fieldtype, **kwargs):
        """Adds a field to the index's schema.

        :param fieldname: the name of the field to add.
        :param fieldtype: an instantiated :class:`whoosh.fields.FieldType`
            object.
        """

        self.schema.add(fieldname, fieldtype, **kwargs)  # type: ignore[attr-defined]

    def remove_field(self, fieldname, **kwargs):
        """Removes the named field from the index's schema. Depending on the
        backend implementation, this may or may not actually remove existing
        data for the field from the index. Optimizing the index should always
        clear out existing data for a removed field.
        """

        self.schema.remove(fieldname, **kwargs)  # type: ignore[attr-defined]

    @abstractmethod
    def reader(self, **kwargs):
        """Returns a reader for the existing index."""

        raise NotImplementedError

    def searcher(self, **kwargs):
        from whoosh.searching import Searcher

        return Searcher(self.reader(), **kwargs)

    def delete_by_term(self, fieldname, text, searcher=None):
        """Deletes any documents containing "term" in the "fieldname" field.
        This is useful when you have an indexed field containing a unique ID
        (such as "pathname") for each document.

        :returns: the number of documents deleted.
        """

        from whoosh.query.terms import Term

        q = Term(fieldname, text)
        return self.delete_by_query(q, searcher=searcher)

    def delete_by_query(self, q, searcher=None):
        """Deletes any documents matching a query object.

        :returns: the number of documents deleted.
        """

        if searcher:
            s = searcher
        else:
            s = self.searcher()

        try:
            count = 0
            for docnum in s.docs_for_query(q, for_deletion=True):
                self.delete_document(docnum)
                count += 1
        finally:
            if not searcher:
                s.close()

        return count

    @abstractmethod
    def delete_document(self, docnum, delete=True):
        """Deletes a document by number."""
        raise NotImplementedError

    @abstractmethod
    def add_document(self, **fields):
        """The keyword arguments map field names to the values to index/store::

            w = myindex.writer()
            w.add_document(path=u"/a", title=u"First doc", text=u"Hello")
            w.commit()

        Depending on the field type, some fields may take objects other than
        unicode strings. For example, NUMERIC fields take numbers, and DATETIME
        fields take ``datetime.datetime`` objects::

            from datetime import datetime, timedelta
            from whoosh import index
            from whoosh.fields import Schema, DATETIME, NUMERIC, TEXT

            schema = Schema(date=DATETIME, size=NUMERIC(float), content=TEXT)
            myindex = index.create_in("indexdir", schema)

            w = myindex.writer()
            w.add_document(date=datetime.now(), size=5.5, content=u"Hello")
            w.commit()

        Instead of a single object (i.e., unicode string, number, or datetime),
        you can supply a list or tuple of objects. For unicode strings, this
        bypasses the field's analyzer. For numbers and dates, this lets you add
        multiple values for the given field::

            date1 = datetime.now()
            date2 = datetime(2005, 12, 25)
            date3 = datetime(1999, 1, 1)
            w.add_document(date=[date1, date2, date3], size=[9.5, 10],
                           content=[u"alfa", u"bravo", u"charlie"])

        For fields that are both indexed and stored, you can specify an
        alternate value to store using a keyword argument in the form
        "_stored_<fieldname>". For example, if you have a field named "title"
        and you want to index the text "a b c" but store the text "e f g", use
        keyword arguments like this::

            writer.add_document(title=u"a b c", _stored_title=u"e f g")

        You can boost the weight of all terms in a certain field by specifying
        a ``_<fieldname>_boost`` keyword argument. For example, if you have a
        field named "content", you can double the weight of this document for
        searches in the "content" field like this::

            writer.add_document(content="a b c", _title_boost=2.0)

        You can boost every field at once using the ``_boost`` keyword. For
        example, to boost fields "a" and "b" by 2.0, and field "c" by 3.0::

            writer.add_document(a="alfa", b="bravo", c="charlie",
                                _boost=2.0, _c_boost=3.0)

        Note that some scoring algroithms, including Whoosh's default BM25F,
        do not work with term weights less than 1, so you should generally not
        use a boost factor less than 1.

        See also :meth:`Writer.update_document`.
        """

        raise NotImplementedError

    @abstractmethod
    def add_reader(self, reader):
        raise NotImplementedError

    def _doc_boost(self, fields, default=1.0):
        if "_boost" in fields:
            return float(fields["_boost"])
        else:
            return default

    def _field_boost(self, fields, fieldname, default=1.0):
        boostkw = f"_{fieldname}_boost"
        if boostkw in fields:
            return float(fields[boostkw])
        else:
            return default

    def _unique_fields(self, fields):
        # Check which of the supplied fields are unique
        unique_fields = [
            name
            for name, field in self.schema.items()  # type: ignore[attr-defined]
            if name in fields and field.unique  # type: ignore[attr-defined]
        ]
        return unique_fields

    def update_document(self, **fields):
        """The keyword arguments map field names to the values to index/store.

        This method adds a new document to the index, and automatically deletes
        any documents with the same values in any fields marked "unique" in the
        schema::

            schema = fields.Schema(path=fields.ID(unique=True, stored=True),
                                   content=fields.TEXT)
            myindex = index.create_in("index", schema)

            w = myindex.writer()
            w.add_document(path=u"/", content=u"Mary had a lamb")
            w.commit()

            w = myindex.writer()
            w.update_document(path=u"/", content=u"Mary had a little lamb")
            w.commit()

            assert myindex.doc_count() == 1

        It is safe to use ``update_document`` in place of ``add_document``; if
        there is no existing document to replace, it simply does an add.

        You cannot currently pass a list or tuple of values to a "unique"
        field.

        Because this method has to search for documents with the same unique
        fields and delete them before adding the new document, it is slower
        than using ``add_document``.

        * Marking more fields "unique" in the schema will make each
          ``update_document`` call slightly slower.

        * When you are updating multiple documents, it is faster to batch
          delete all changed documents and then use ``add_document`` to add
          the replacements instead of using ``update_document``.

        Note that this method will only replace a *committed* document;
        currently it cannot replace documents you've added to the IndexWriter
        but haven't yet committed. For example, if you do this:

        >>> writer.update_document(unique_id=u"1", content=u"Replace me")
        >>> writer.update_document(unique_id=u"1", content=u"Replacement")

        ...this will add two documents with the same value of ``unique_id``,
        instead of the second document replacing the first.

        See :meth:`Writer.add_document` for information on
        ``_stored_<fieldname>``, ``_<fieldname>_boost``, and ``_boost`` keyword
        arguments.
        """

        # Delete the set of documents matching the unique terms
        unique_fields = self._unique_fields(fields)
        if unique_fields:
            with self.searcher() as s:
                uniqueterms = [(name, fields[name]) for name in unique_fields]
                docs = s._find_unique(uniqueterms)
                for docnum in docs:
                    self.delete_document(docnum)

        # Add the given fields
        self.add_document(**fields)

    def batch_update_documents(self, docs):
        """Batch version of :meth:`update_document`.

        Accepts an iterable of field mappings. For each document, deletes any
        existing documents matching the unique fields, then adds the new
        document. Opens a single searcher for the whole batch instead of one
        per document, which is significantly faster for large batches.

        :param docs: iterable of ``dict``-like objects mapping field names to
            values, e.g. ``[{"id": "1", "content": "..."}, ...]``.
        """
        if not docs:
            return

        unique_fields = set()
        for fields in docs:
            uf = self._unique_fields(fields)
            if uf:
                unique_fields.update(uf)

        if unique_fields:
            seen = {}
            deduped = []
            for fields in docs:
                key = tuple((name, fields[name]) for name in unique_fields if name in fields)
                if key:
                    seen[key] = fields
                else:
                    deduped.append(fields)
            deduped.extend(seen.values())
            batch = deduped
        else:
            batch = list(docs)

        with self.searcher() as s:
            for fields in batch:
                uniqueterms = [(name, fields[name]) for name in unique_fields if name in fields]
                if uniqueterms:
                    docs_to_delete = s._find_unique(uniqueterms)
                    for docnum in docs_to_delete:
                        self.delete_document(docnum)
                self.add_document(**fields)

    def add_batch(self, docs, batch_size=None):
        """Batch version of :meth:`add_document`.

        Accepts an iterable of field mappings and adds them to the index.
        This method reduces Python overhead by batching schema validation and
        field lookups, providing significant speedups for large document sets.

        :param docs: iterable of ``dict``-like objects mapping field names to
            values, e.g. ``[{"title": "Hello", "content": "..."}, ...]``.
        :param batch_size: optional hint for internal chunking. If None, all
            documents are processed in a single batch.
        """
        if batch_size is None:
            self._add_batch(list(docs))
        else:
            chunk = []
            for doc in docs:
                chunk.append(doc)
                if len(chunk) >= batch_size:
                    self._add_batch(chunk)
                    chunk = []
            if chunk:
                self._add_batch(chunk)

    def _add_batch(self, docs):
        """Internal batch add implementation. Subclasses should override."""
        for fields in docs:
            self.add_document(**fields)

    def commit(self):
        """Finishes writing and unlocks the index."""
        pass

    def cancel(self):
        """Cancels any documents/deletions added by this object
        and unlocks the index.
        """
        pass


def add_spelling(ix, fieldnames, commit=True):
    """Adds spelling files to an existing index that was created without
    them, and modifies the schema so the given fields have the ``spelling``
    attribute. Only works on filedb indexes.

    >>> ix = index.open_dir("testindex")
    >>> add_spelling(ix, ["content", "tags"])

    :param ix: a :class:`whoosh.filedb.fileindex.FileIndex` object.
    :param fieldnames: a list of field names to create word graphs for.
    :param force: if True, overwrites existing word graph files. This is only
        useful for debugging.
    """

    from whoosh.automata import fst
    from whoosh.reading import SegmentReader

    writer = ix.writer()
    storage = writer.storage
    schema = writer.schema
    segments = writer.segments

    for segment in segments:
        ext = segment.codec().FST_EXT

        r = SegmentReader(storage, schema, segment)
        f = segment.create_file(storage, ext)
        gw = fst.GraphWriter(f)
        for fieldname in fieldnames:
            gw.start_field(fieldname)
            for word in r.lexicon(fieldname):
                gw.insert(word)
            gw.finish_field()
        gw.close()

    for fieldname in fieldnames:
        schema[fieldname].spelling = True

    if commit:
        writer.commit(merge=False)
