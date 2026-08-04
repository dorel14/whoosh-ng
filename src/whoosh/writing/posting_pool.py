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
"""Customized sorting pool for postings."""

from whoosh.externalsort import SortingPool
from whoosh.util import random_name


def _posting_size(item):
    """Return a lightweight estimate of the memory size of a posting tuple.

    Uses the known structure of the posting item instead of ``sys.getsizeof``
    to avoid the allocator overhead on hot paths. The value is only used to
    decide when to flush the current run, so a small estimation error is
    acceptable.
    """

    try:
        fieldname, textbytes, docnum, weight, vbytes = item
        size = 64
        size += len(fieldname) + len(textbytes)
        if vbytes is not None:
            size += len(vbytes)
        return size
    except Exception:
        return 64


class PostingPool(SortingPool):
    # Subclass whoosh.externalsort.SortingPool to use knowledge of
    # postings to set run size in bytes instead of items

    namechars = "abcdefghijklmnopqrstuvwxyz0123456789"

    def __init__(self, tempstore, segment, limitmb=128, **kwargs):
        SortingPool.__init__(self, **kwargs)
        self.tempstore = tempstore
        self.segment = segment
        self.limit = limitmb * 1024 * 1024
        self.currentsize = 0
        self.fieldnames = set()

    def _new_run(self):
        path = f"{random_name()}.run"
        f = self.tempstore.create_file(path).raw_file()
        return path, f

    def _open_run(self, path):
        return self.tempstore.open_file(path).raw_file()

    def _remove_run(self, path):
        return self.tempstore.delete_file(path)

    def add(self, item):
        assert isinstance(item[1], bytes), f"tbytes={item[1]!r}"
        if item[4] is not None:
            assert isinstance(item[4], bytes), f"vbytes={item[4]!r}"
        self.fieldnames.add(item[0])
        self.currentsize += _posting_size(item)
        if self.currentsize > self.limit:
            self.save()
        self.current.append(item)

    def iter_postings(self):
        # This is just an alias for items() to be consistent with the
        # iter_postings()/add_postings() interface of a lot of other classes
        return self.items()

    def save(self):
        SortingPool.save(self)
        self.currentsize = 0
