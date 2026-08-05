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
"""The :class:`SegmentWriter` codec-based writer."""

from bisect import bisect_right
from contextlib import contextmanager, suppress

from whoosh import columns
from whoosh.fields import UnknownFieldError
from whoosh.index import LockError
from whoosh.util import fib, random_name
from whoosh.util.filelock import try_for
from whoosh.util.text import utf8encode
from whoosh.writing._base import IndexingError, groupmanager
from whoosh.writing.merge_policies import CLEAR, MERGE_SMALL, NO_MERGE, OPTIMIZE
from whoosh.writing.posting_pool import PostingPool
from whoosh.writing.writer import IndexWriter


class SegmentWriter(IndexWriter):
    def __init__(
        self,
        ix,
        poolclass=None,
        timeout=0.0,
        delay=0.1,
        _lk=True,
        limitmb=128,
        docbase=0,
        codec=None,
        compound=True,
        tempname=None,
        **kwargs,
    ):
        # Lock the index
        self.writelock = None
        if _lk:
            self.writelock = ix.lock("WRITELOCK")
            if not try_for(self.writelock.acquire, timeout=timeout, delay=delay):
                raise LockError

        if codec is None:
            from whoosh.codec import default_codec

            codec = default_codec()
        self.codec = codec

        # Get info from the index
        self.storage = ix.storage
        self.indexname = ix.indexname
        info = ix._read_toc()
        self.generation = info.generation + 1
        self.schema = info.schema
        self.segments = info.segments
        self.docnum = self.docbase = docbase
        self._setup_doc_offsets()

        # Internals
        # Each writer gets an ISOLATED temporary storage so concurrent writers
        # (threads or processes) never share scratch files (issue #391). When
        # ``tempname`` is None a unique directory is created automatically; the
        # multiprocessing writer passes a single shared ``tempname`` so its
        # parent and sub-processes can exchange job files through the same
        # directory without colliding with other writers.
        self.tempname = tempname
        self._tempstorage = self.storage.temp_storage(tempname)
        newsegment = codec.new_segment(self.storage, self.indexname)
        self.newsegment = newsegment
        self.compound = compound and newsegment.should_assemble()
        self.is_closed = False
        self._added = False
        self.pool = PostingPool(self._tempstorage, self.newsegment, limitmb=limitmb)

        # Set up writers
        self.perdocwriter = codec.per_document_writer(self.storage, newsegment)
        self.fieldwriter = codec.field_writer(self.storage, newsegment)

        self.merge = True
        self.optimize = False
        self.mergetype = None
        self._searcher = None

    def __repr__(self):
        # Author: Ronald Evers
        # Origin bitbucket issue: https://bitbucket.org/mchaput/whoosh/issues/483
        # newsegment might not be set due to LockError
        # so use getattr to be safe
        return f"<{self.__class__.__name__} {getattr(self, 'newsegment', None)!r}>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            with suppress(Exception):
                self.cancel()
            return False
        try:
            self.commit()
        except Exception:
            with suppress(Exception):
                self.cancel()
            raise

    def _check_state(self):
        if self.is_closed:
            raise IndexingError("This writer is closed")

    def _setup_doc_offsets(self):
        self._doc_offsets = []
        base = 0
        for s in self.segments:
            self._doc_offsets.append(base)
            base += s.doc_count_all()

    def _document_segment(self, docnum):
        # Returns the index.Segment object containing the given document
        # number.
        offsets = self._doc_offsets
        if len(offsets) == 1:
            return 0
        return bisect_right(offsets, docnum) - 1

    def _segment_and_docnum(self, docnum):
        # Returns an (index.Segment, segment_docnum) pair for the segment
        # containing the given document number.

        segmentnum = self._document_segment(docnum)
        offset = self._doc_offsets[segmentnum]
        segment = self.segments[segmentnum]
        return segment, docnum - offset

    def _process_posts(self, items, startdoc, docmap):
        schema = self.schema
        for fieldname, text, docnum, weight, vbytes in items:
            if fieldname not in schema:
                continue
            if docmap is not None:
                newdoc = docmap[docnum]
            else:
                newdoc = startdoc + docnum

            yield (fieldname, text, newdoc, weight, vbytes)

    def temp_storage(self):
        return self._tempstorage

    def add_field(self, fieldname, fieldspec, **kwargs):
        self._check_state()
        if self._added:
            raise Exception("Can't modify schema after adding data to writer")
        super().add_field(fieldname, fieldspec, **kwargs)

    def remove_field(self, fieldname):
        self._check_state()
        if self._added:
            raise Exception("Can't modify schema after adding data to writer")
        super().remove_field(fieldname)

    def has_deletions(self):
        """
        Returns True if the current index has documents that are marked deleted
        but haven't been optimized out of the index yet.
        """

        return any(s.has_deletions() for s in self.segments)

    def delete_document(self, docnum, delete=True):
        self._check_state()
        if docnum >= sum(seg.doc_count_all() for seg in self.segments):
            raise IndexingError(f"No document ID {docnum!r} in this index")
        segment, segdocnum = self._segment_and_docnum(docnum)
        segment.delete_document(segdocnum, delete=delete)

    def deleted_count(self):
        """
        :returns: the total number of deleted documents in the index.
        """

        return sum(s.deleted_count() for s in self.segments)

    def is_deleted(self, docnum):
        segment, segdocnum = self._segment_and_docnum(docnum)
        return segment.is_deleted(segdocnum)

    def reader(self, reuse=None):
        from whoosh.index import FileIndex

        self._check_state()
        return FileIndex._reader(
            self.storage, self.schema, self.segments, self.generation, reuse=reuse
        )

    def iter_postings(self):
        return self.pool.iter_postings()

    def add_postings_to_pool(self, reader, startdoc, docmap):
        items = self._process_posts(reader.iter_postings(), startdoc, docmap)
        add_post = self.pool.add
        for item in items:
            add_post(item)

    def write_postings(self, lengths, items, startdoc, docmap):
        items = self._process_posts(items, startdoc, docmap)
        self.fieldwriter.add_postings(self.schema, lengths, items)

    def write_per_doc(self, fieldnames, reader):
        # Very bad hack: reader should be an IndexReader, but may be a
        # PerDocumentReader if this is called from multiproc, where the code
        # tries to be efficient by merging per-doc and terms separately.
        # TODO: fix this!

        schema = self.schema
        if reader.has_deletions():
            docmap = {}
        else:
            docmap = None

        pdw = self.perdocwriter
        # Open all column readers
        cols = {}
        for fieldname in fieldnames:
            fieldobj = schema[fieldname]
            coltype = fieldobj.column_type
            if coltype and reader.has_column(fieldname):
                creader = reader.column_reader(fieldname, coltype)
                if isinstance(creader, columns.TranslatingColumnReader):
                    creader = creader.raw_column()
                cols[fieldname] = creader

        for docnum, stored in reader.iter_docs():
            if docmap is not None:
                docmap[docnum] = self.docnum

            pdw.start_doc(self.docnum)
            # Set disjunction includes dynamic fields (can be different for each document)
            for fieldname in fieldnames | {s for s in stored if s in self.schema}:
                fieldobj = schema[fieldname]
                length = reader.doc_field_length(docnum, fieldname)
                pdw.add_field(fieldname, fieldobj, stored.get(fieldname), length)

                if fieldobj.vector and reader.has_vector(docnum, fieldname):
                    v = reader.vector(docnum, fieldname, fieldobj.vector)
                    pdw.add_vector_matcher(fieldname, fieldobj, v)

                if fieldname in cols:
                    cv = cols[fieldname][docnum]
                    pdw.add_column_value(fieldname, fieldobj.column_type, cv)

            pdw.finish_doc()
            self.docnum += 1

        return docmap

    def add_reader(self, reader):
        self._check_state()
        basedoc = self.docnum
        ndxnames = {fname for fname in reader.indexed_field_names() if fname in self.schema}
        fieldnames = set(self.schema.names()) | ndxnames

        docmap = self.write_per_doc(fieldnames, reader)
        self.add_postings_to_pool(reader, basedoc, docmap)
        self._added = True

    def _check_fields(self, schema, fieldnames):
        # Check if the caller gave us a bogus field
        for name in fieldnames:
            if name not in schema:
                raise UnknownFieldError(f"No field named {name!r} in {schema}")

    def add_document(self, **fields):
        self._check_state()
        perdocwriter = self.perdocwriter
        schema = self.schema
        docnum = self.docnum
        add_post = self.pool.add

        docboost = self._doc_boost(fields)
        fieldnames = sorted([name for name in fields if not name.startswith("_")])
        self._check_fields(schema, fieldnames)

        perdocwriter.start_doc(docnum)
        try:
            for fieldname in fieldnames:
                value = fields.get(fieldname)
                if value is None:
                    continue
                field = schema[fieldname]

                length = 0
                if field.indexed:
                    fieldboost = self._field_boost(fields, fieldname, docboost)
                    items = field.index(value)
                    scorable = field.scorable
                    for tbytes, freq, weight, vbytes in items:
                        weight *= fieldboost
                        if scorable:
                            length += freq
                        add_post((fieldname, tbytes, docnum, weight, vbytes))

                if field.separate_spelling():
                    spellfield = field.spelling_fieldname(fieldname)
                    for word in field.spellable_words(value):
                        word = utf8encode(word)[0]

                        add_post((spellfield, word, 0, 1, vbytes))

                vformat = field.vector
                if vformat:
                    analyzer = field.analyzer
                    vitems = vformat.word_values(value, analyzer, mode="index")
                    vitems = sorted((text, weight, vbytes) for text, _, weight, vbytes in vitems)
                    perdocwriter.add_vector_items(fieldname, field, vitems)

                customval = fields.get(f"_stored_{fieldname}", value)

                sv = customval if field.stored else None
                perdocwriter.add_field(fieldname, field, sv, length)

                column = field.column_type
                if column and customval is not None:
                    cv = field.to_column_value(customval)
                    perdocwriter.add_column_value(fieldname, column, cv)
        except ValueError as ex:
            perdocwriter.cancel_doc()
            raise ex

        perdocwriter.finish_doc()
        self._added = True
        self.docnum += 1

    def _add_batch(self, docs):
        """Optimized batch document addition.

        Reduces Python overhead by caching attribute lookups and pre-
        validating the schema once per batch instead of per document.
        """
        if not docs:
            return

        self._check_state()
        perdocwriter = self.perdocwriter
        schema = self.schema
        pool_add = self.pool.add
        docnum = self.docnum
        docbase = self.docbase

        for fields in docs:
            docboost = self._doc_boost(fields)
            fieldnames = sorted(name for name in fields if not name.startswith("_"))
            self._check_fields(schema, fieldnames)

            perdocwriter.start_doc(docnum)
            try:
                for fieldname in fieldnames:
                    value = fields.get(fieldname)
                    if value is None:
                        continue
                    field = schema[fieldname]

                    length = 0
                    if field.indexed:
                        fieldboost = self._field_boost(fields, fieldname, docboost)
                        items = field.index(value)
                        scorable = field.scorable
                        for tbytes, freq, weight, vbytes in items:
                            weight *= fieldboost
                            if scorable:
                                length += freq
                            pool_add((fieldname, tbytes, docnum, weight, vbytes))

                    if field.separate_spelling():
                        spellfield = field.spelling_fieldname(fieldname)
                        for word in field.spellable_words(value):
                            word = utf8encode(word)[0]
                            pool_add((spellfield, word, 0, 1, vbytes))

                    vformat = field.vector
                    if vformat:
                        analyzer = field.analyzer
                        vitems = vformat.word_values(value, analyzer, mode="index")
                        vitems = sorted(
                            (text, weight, vbytes) for text, _, weight, vbytes in vitems
                        )
                        perdocwriter.add_vector_items(fieldname, field, vitems)

                    customval = fields.get(f"_stored_{fieldname}", value)

                    sv = customval if field.stored else None
                    perdocwriter.add_field(fieldname, field, sv, length)

                    column = field.column_type
                    if column and customval is not None:
                        cv = field.to_column_value(customval)
                        perdocwriter.add_column_value(fieldname, column, cv)
            except ValueError:
                perdocwriter.cancel_doc()
                raise

            perdocwriter.finish_doc()
            self._added = True
            docnum += 1

        self.docnum = docnum

    def doc_count(self):
        return self.docnum - self.docbase

    def get_segment(self):
        newsegment = self.newsegment
        newsegment.set_doc_count(self.docnum)
        return newsegment

    def per_document_reader(self):
        if not self.perdocwriter.is_closed:
            raise RuntimeError("Per-doc writer is still open")
        return self.codec.per_document_reader(self.storage, self.get_segment())

    def searcher(self, **kwargs):
        # If possible, cache a Searcher that doesn't close until we want it to.
        # We have a write lock, nothing is changing. Only cache if kwargs is emtpy
        # and the SegmentWriter is still open.
        if kwargs or self.is_closed:
            return super().searcher(**kwargs)

        if self._searcher is None:
            s = super().searcher()
            self._searcher = s
            s._orig_close = s.close  # type: ignore[attr-defined]  # called in _finish()
            s.close = lambda: None
        return self._searcher

    # The following methods break out the commit functionality into smaller
    # pieces to allow MpWriter to call them individually

    def _merge_segments(self, mergetype, optimize, merge):
        # The writer supports two ways of setting mergetype/optimize/merge:
        # as attributes or as keyword arguments to commit(). Originally there
        # were just the keyword arguments, but then I added the ability to use
        # the writer as a context manager using "with", so the user no longer
        # explicitly called commit(), hence the attributes
        mergetype = mergetype if mergetype is not None else self.mergetype
        optimize = optimize if optimize is not None else self.optimize
        merge = merge if merge is not None else self.merge

        if mergetype:
            pass
        elif optimize:
            mergetype = OPTIMIZE
        elif not merge:
            mergetype = NO_MERGE
        else:
            mergetype = MERGE_SMALL

        # Call the merge policy function. The policy may choose to merge
        # other segments into this writer's pool
        return mergetype(self, self.segments)

    def _flush_segment(self):
        self.perdocwriter.close()
        if self.codec.length_stats:
            pdr = self.per_document_reader()
        else:
            pdr = None
        postings = self.pool.iter_postings()
        self.fieldwriter.add_postings(self.schema, pdr, postings)
        self.fieldwriter.close()
        if pdr:
            pdr.close()

    def _close_segment(self):
        if not self.perdocwriter.is_closed:
            self.perdocwriter.close()
        if not self.fieldwriter.is_closed:
            self.fieldwriter.close()
        self.pool.cleanup()

    def _assemble_segment(self):
        if self.compound:
            # Assemble the segment files into a compound file
            newsegment = self.get_segment()
            newsegment.create_compound_file(self.storage)
            newsegment.compound = True

    def _partial_segment(self):
        # For use by a parent multiprocessing writer: Closes out the segment
        # but leaves the pool files intact so the parent can access them
        self._check_state()
        self.perdocwriter.close()
        self.fieldwriter.close()
        # Don't call self.pool.cleanup()! We want to grab the pool files.
        return self.get_segment()

    def _finalize_segment(self):
        # Finish writing segment
        self._flush_segment()
        # Close segment files
        self._close_segment()
        # Assemble compound segment if necessary
        self._assemble_segment()

        return self.get_segment()

    def _commit_toc(self, segments):
        from whoosh.index import TOC, clean_files

        # Write a new TOC with the new segment list (and delete old files)
        toc = TOC(self.schema, segments, self.generation)
        toc.write(self.storage, self.indexname)
        # Delete leftover files
        clean_files(self.storage, self.indexname, self.generation, segments)

    def _finish(self):
        if self._searcher is not None:
            # Close the cached Searcher if we have one.
            self._searcher._orig_close()  # type: ignore[attr-defined]
            self._searcher = None
        self._tempstorage.destroy()
        if self.writelock:
            self.writelock.release()
        self.is_closed = True
        # self.storage.close()

    # Finalization methods

    def commit(self, mergetype=None, optimize=None, merge=None, callback=None):
        """Finishes writing and saves all additions and changes to disk.

        There are four possible ways to use this method::

            # Merge small segments but leave large segments, trying to
            # balance fast commits with fast searching:
            writer.commit()

            # Merge all segments into a single segment:
            writer.commit(optimize=True)

            # Don't merge any existing segments:
            writer.commit(merge=False)

            # Use a custom merge function
            writer.commit(mergetype=my_merge_function)

        :param mergetype: a custom merge function taking a Writer object and
            segment list as arguments, and returning a new segment list. If you
            supply a ``mergetype`` function, the values of the ``optimize`` and
            ``merge`` arguments are ignored.
        :param optimize: if True, all existing segments are merged with the
            documents you've added to this writer (and the value of the
            ``merge`` argument is ignored).
        :param merge: if False, do not merge small segments.
        :param callback: optional callable ``callback(stage, **kwargs)`` called
            at key points during commit. Stages are ``"merge"``, ``"segment"``,
            ``"toc"``, and ``"finish"``.
        """

        self._check_state()
        # Merge old segments if necessary
        if callback:
            callback("merge", segments=len(self.segments))
        finalsegments = self._merge_segments(mergetype, optimize, merge)
        if callback:
            callback("merge", segments=len(finalsegments))
        if self._added:
            # Flush the current segment being written and add it to the
            # list of remaining segments returned by the merge policy
            # function
            if callback:
                callback("segment", started=True)
            finalsegments.append(self._finalize_segment())
            if callback:
                callback("segment", ended=True)
        else:
            # Close segment files
            self._close_segment()
        # Write TOC
        if callback:
            callback("toc", started=True, segments=len(finalsegments))
        self._commit_toc(finalsegments)
        if callback:
            callback("toc", ended=True)

        # Final cleanup
        if callback:
            callback("finish")
        self._finish()

    def cancel(self):
        self._check_state()
        self._close_segment()
        self._finish()
