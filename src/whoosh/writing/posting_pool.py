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

import sys

from whoosh.externalsort import SortingPool
from whoosh.util import random_name


def _posting_size(item):
    """Return a reliable estimate of the memory size of a posting tuple
    ``(fieldname, textbytes, docnum, weight, vbytes)``.

    Uses :func:`sys.getsizeof` on the tuple and its elements, with a fallback to
    item-counting when ``sys.getsizeof`` is unavailable or raises. This replaces
    the previous implementation's hard-coded per-type byte constants, which were
    fragile and dependent on the CPython object layout.
    """

    try:
        size = sys.getsizeof(item)
        for sub in item:
            try:
                size += sys.getsizeof(sub)
            except Exception:
                size += 1
        fieldname, textbytes, docnum, weight, vbytes = item
        size += len(fieldname) + len(textbytes)
        if vbytes is not None:
            size += len(vbytes)
        return size
    except Exception:
        return 1 + len(item)


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
