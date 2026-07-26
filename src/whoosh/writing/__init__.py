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
"""Classes and functions for writing to an index.

This package is a refactored version of the former monolithic
``whoosh.writing`` module. The public API (class and function names) is
unchanged: importing from ``whoosh.writing`` continues to work exactly as
before.
"""

from whoosh.writing._base import IndexingError, PostingWriter, groupmanager
from whoosh.writing.async_writer import AsyncWriter
from whoosh.writing.buffered_writer import BufferedWriter, BatchWriter
from whoosh.writing.merge_policies import CLEAR, MERGE_SMALL, NO_MERGE, OPTIMIZE
from whoosh.writing.posting_pool import PostingPool
from whoosh.writing.segment_writer import SegmentWriter
from whoosh.writing.writer import IndexWriter, add_spelling

__all__ = (
    "IndexingError",
    "PostingWriter",
    "groupmanager",
    "NO_MERGE",
    "MERGE_SMALL",
    "OPTIMIZE",
    "CLEAR",
    "PostingPool",
    "IndexWriter",
    "SegmentWriter",
    "AsyncWriter",
    "add_spelling",
    "BufferedWriter",
    "BatchWriter",
)
