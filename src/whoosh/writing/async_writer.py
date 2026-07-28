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
"""The :class:`AsyncWriter` wrapper."""

import threading
import time

from whoosh.index import LockError
from whoosh.writing._base import IndexingError, groupmanager
from whoosh.writing.writer import IndexWriter


class AsyncWriter(threading.Thread, IndexWriter):
    """Convenience wrapper for a writer object that might fail due to locking
    (i.e. the ``filedb`` writer). This object will attempt once to obtain the
    underlying writer, and if it's successful, will simply pass method calls on
    to it.

    If this object *can't* obtain a writer immediately, it will *buffer*
    delete, add, and update method calls in memory until you call ``commit()``.
    At that point, this object will start running in a separate thread, trying
    to obtain the writer over and over, and once it obtains it, "replay" all
    the buffered method calls on it.

    In a typical scenario where you're adding a single or a few documents to
    the index as the result of a Web transaction, this lets you just create the
    writer, add, and commit, without having to worry about index locks,
    retries, etc.

    For example, to get an aynchronous writer, instead of this:

    >>> writer = myindex.writer()

    Do this:

    >>> from whoosh.writing import AsyncWriter
    >>> writer = AsyncWriter(myindex)
    """

    def __init__(self, index, delay=0.25, writerargs=None):
        """
        :param index: the :class:`whoosh.index.Index` to write to.
        :param delay: the delay (in seconds) between attempts to instantiate
            the actual writer.
        :param writerargs: an optional dictionary specifying keyword arguments
            to to be passed to the index's ``writer()`` method.
        """

        threading.Thread.__init__(self)
        self.running = False
        self.started = False
        self.committed = False
        self.cancelled = False
        self.error = None
        self.index = index
        self.writerargs = writerargs or {}
        self.delay = delay
        self.events = []
        try:
            self.writer = self.index.writer(**self.writerargs)
        except LockError:
            self.writer = None

    def reader(self):
        return self.index.reader()

    def searcher(self, **kwargs):
        from whoosh.searching import Searcher

        return Searcher(self.reader(), fromindex=self.index, **kwargs)

    def _record(self, method, args, kwargs):
        if self.writer:
            getattr(self.writer, method)(*args, **kwargs)
        else:
            self.events.append((method, args, kwargs))

    def run(self):
        self.running = True
        try:
            # If cancel() was called before the thread started, do nothing.
            if self.cancelled:
                return

            writer = self.writer
            # Acquire the underlying writer, retrying if the index is locked
            # (issue #369).
            while writer is None:
                try:
                    writer = self.index.writer(**self.writerargs)
                except LockError:
                    time.sleep(self.delay)

            # Replay the buffered calls and commit.
            for method, args, kwargs in self.events:
                getattr(writer, method)(*args, **kwargs)
            writer.commit(*self.commitargs, **self.commitkwargs)
            self.committed = True
        except Exception as e:
            # Surface the failure so it is observable via wait()/self.error
            # instead of being swallowed by the background thread (issue #578).
            self.error = e
            raise
        finally:
            self.running = False

    def wait(self, timeout=None):
        """Joins the background thread (if it was started) and re-raises any
        exception that occurred during the asynchronous commit, so failures are
        observable (issue #578). Returns ``True`` if the commit completed.

        :param timeout: maximum time (seconds) to wait for the thread.
        """

        if self.started:
            self.join(timeout)
        if self.error is not None:
            raise self.error
        return self.committed

    def delete_document(self, *args, **kwargs):
        self._record("delete_document", args, kwargs)

    def add_document(self, *args, **kwargs):
        self._record("add_document", args, kwargs)

    def update_document(self, *args, **kwargs):
        self._record("update_document", args, kwargs)

    def add_field(self, *args, **kwargs):
        self._record("add_field", args, kwargs)

    def remove_field(self, *args, **kwargs):
        self._record("remove_field", args, kwargs)

    def delete_by_term(self, *args, **kwargs):
        self._record("delete_by_term", args, kwargs)

    def commit(self, *args, **kwargs):
        if self.committed:
            raise RuntimeError("AsyncWriter.commit() has already been called; this writer is spent")
        if self.writer:
            self.writer.commit(*args, **kwargs)
            self.committed = True
        else:
            self.commitargs, self.commitkwargs = args, kwargs
            if self.started:
                raise RuntimeError(
                    "AsyncWriter.commit() is already running in a background "
                    "thread; call commit() only once"
                )
            self.started = True
            self.start()

    def cancel(self, *args, **kwargs):
        if self.writer:
            self.writer.cancel(*args, **kwargs)
            self.committed = True
        else:
            # The buffered events are dropped; the background thread, if
            # started, should not replay or commit anything.
            self.cancelled = True

