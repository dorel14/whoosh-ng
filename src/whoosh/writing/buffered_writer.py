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
"""The :class:`BufferedWriter` class."""

import threading

from whoosh.writing._base import IndexingError, groupmanager
from whoosh.writing.writer import IndexWriter

class BufferedWriter(IndexWriter):
    """Convenience class that acts like a writer but buffers added documents
    before dumping the buffered documents as a batch into the actual index.

    In scenarios where you are continuously adding single documents very
    rapidly (for example a web application where lots of users are adding
    content simultaneously), using a BufferedWriter is *much* faster than
    opening and committing a writer for each document you add. If you're adding
    batches of documents at a time, you can just use a regular writer.

    (This class may also be useful for batches of ``update_document`` calls. In
    a normal writer, ``update_document`` calls cannot update documents you've
    added *in that writer*. With ``BufferedWriter``, this will work.)

    To use this class, create it from your index and *keep it open*, sharing
    it between threads.

    >>> from whoosh.writing import BufferedWriter
    >>> writer = BufferedWriter(myindex, period=120, limit=20)
    >>> # Then you can use the writer to add and update documents
    >>> writer.add_document(...)
    >>> writer.add_document(...)
    >>> writer.add_document(...)
    >>> # Before the writer goes out of scope, call close() on it
    >>> writer.close()

    .. note::
        This object stores documents in memory and may keep an underlying
        writer open, so you must explicitly call the
        :meth:`~BufferedWriter.close` method on this object before it goes out
        of scope to release the write lock and make sure any uncommitted
        changes are saved.

    You can read/search the combination of the on-disk index and the
    buffered documents in memory by calling ``BufferedWriter.reader()`` or
    ``BufferedWriter.searcher()``. This allows quasi-real-time search, where
    documents are available for searching as soon as they are buffered in
    memory, before they are committed to disk.

    .. tip::
        By using a searcher from the shared writer, multiple *threads* can
        search the buffered documents. Of course, other *processes* will only
        see the documents that have been written to disk. If you want indexed
        documents to become available to other processes as soon as possible,
        you have to use a traditional writer instead of a ``BufferedWriter``.

    You can control how often the ``BufferedWriter`` flushes the in-memory
    index to disk using the ``period`` and ``limit`` arguments. ``period`` is
    the maximum number of seconds between commits. ``limit`` is the maximum
    number of additions to buffer between commits.

    You don't need to call ``commit()`` on the ``BufferedWriter`` manually.
    Doing so will just flush the buffered documents to disk early. You can
    continue to make changes after calling ``commit()``, and you can call
    ``commit()`` multiple times.
    """

    def __init__(self, index, period=60, limit=10, writerargs=None, commitargs=None):
        """
        :param index: the :class:`whoosh.index.Index` to write to.
        :param period: the maximum amount of time (in seconds) between commits.
            Set this to ``0`` or ``None`` to not use a timer. Do not set this
            any lower than a few seconds.
        :param limit: the maximum number of documents to buffer before
            committing.
        :param writerargs: dictionary specifying keyword arguments to be passed
            to the index's ``writer()`` method when creating a writer.
        """

        self.index = index
        self.period = period
        self.limit = limit
        self.writerargs = writerargs or {}
        self.commitargs = commitargs or {}

        self.lock = threading.RLock()
        self.writer = self.index.writer(**self.writerargs)

        self._make_ram_index()
        self.bufferedcount = 0

        # Start timer
        if self.period:
            self.timer = threading.Timer(self.period, self.commit)
            self.timer.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _make_ram_index(self):
        from whoosh.codec.memory import MemoryCodec

        self.codec = MemoryCodec()

    def _get_ram_reader(self):
        return self.codec.reader(self.schema)

    @property
    def schema(self):
        return self.writer.schema

    def reader(self, **kwargs):
        from whoosh.reading import MultiReader

        # Hold the writer lock for the whole assembly so a concurrent commit()
        # cannot swap out self.writer (and its backing index) mid-read, which
        # previously caused crashes when .searcher() was called from multiple
        # threads (issue #449).
        with self.lock:
            reader = self.writer.reader()
            ramreader = self._get_ram_reader()

            # If there are in-memory docs, combine the readers
            if ramreader.doc_count():
                if reader.is_atomic():
                    reader = MultiReader([reader, ramreader])
                else:
                    reader.add_reader(ramreader)

        return reader

    def searcher(self, **kwargs):
        from whoosh.searching import Searcher

        return Searcher(self.reader(), fromindex=self.index, **kwargs)

    def close(self):
        self.commit(restart=False)

    def commit(self, restart=True):
        if self.period:
            self.timer.cancel()

        # Hold the writer lock for the entire swap so a concurrent
        # ``reader()``/``searcher()`` (which also takes this lock) never
        # observes ``self.writer`` mid-replacement -- i.e. never calls
        # ``CodeWriter.reader()`` on a writer that has just been closed, which
        # previously raised ``IndexingError("This writer is closed")`` from
        # other threads (issue #449).
        with self.lock:
            ramreader = self._get_ram_reader()
            self._make_ram_index()

            if self.bufferedcount:
                self.writer.add_reader(ramreader)
            self.writer.commit(**self.commitargs)
            self.bufferedcount = 0

            if restart:
                self.writer = self.index.writer(**self.writerargs)
                if self.period:
                    self.timer = threading.Timer(self.period, self.commit)
                    self.timer.start()

    def add_reader(self, reader):
        # Pass through to the underlying on-disk index
        self.writer.add_reader(reader)
        self.commit()

    def add_document(self, **fields):
        with self.lock:
            # Hijack a writer to make the calls into the codec
            with self.codec.writer(self.writer.schema) as w:
                w.add_document(**fields)

            self.bufferedcount += 1
            if self.bufferedcount >= self.limit:
                self.commit()

    def update_document(self, **fields):
        with self.lock:
            IndexWriter.update_document(self, **fields)

    def delete_document(self, docnum, delete=True):
        with self.lock:
            base = self.index.doc_count_all()
            if docnum < base:
                self.writer.delete_document(docnum, delete=delete)
            else:
                ramsegment = self.codec.segment
                ramsegment.delete_document(docnum - base, delete=delete)

    def is_deleted(self, docnum):
        base = self.index.doc_count_all()
        if docnum < base:
            return self.writer.is_deleted(docnum)
        else:
            return self._get_ram_reader().is_deleted(docnum - base)

# Backwards compatibility with old name
BatchWriter = BufferedWriter
