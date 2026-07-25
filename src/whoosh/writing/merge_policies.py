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
"""Merge policies for :class:`whoosh.writing.SegmentWriter`."""

from whoosh.util import fib

# A merge policy is a callable that takes the Index object, the SegmentWriter
# object, and the current segment list (not including the segment being
# written), and returns an updated segment list (not including the segment
# being written).

def NO_MERGE(writer, segments):
    """This policy does not merge any existing segments."""
    _ = writer
    return segments

def MERGE_SMALL(writer, segments):
    """This policy merges small segments, where "small" is defined using a
    heuristic based on the fibonacci sequence.
    """

    from whoosh.reading import SegmentReader

    unchanged_segments = []
    segments_to_merge = []

    sorted_segment_list = sorted(segments, key=lambda s: s.doc_count_all())
    total_docs = 0

    merge_point_found = False
    for i, seg in enumerate(sorted_segment_list):
        count = seg.doc_count_all()
        if count > 0:
            total_docs += count

        if merge_point_found:  # append the remaining to unchanged
            unchanged_segments.append(seg)
        else:  # look for a merge point
            segments_to_merge.append((seg, i))  # merge every segment up to the merge point
            if i > 3 and total_docs < fib(i + 5):
                merge_point_found = True

    if merge_point_found and len(segments_to_merge) > 1:
        for seg, i in segments_to_merge:
            reader = SegmentReader(writer.storage, writer.schema, seg)
            writer.add_reader(reader)
            reader.close()
        return unchanged_segments
    else:
        return segments

def OPTIMIZE(writer, segments):
    """This policy merges all existing segments."""

    from whoosh.reading import SegmentReader

    for seg in segments:
        reader = SegmentReader(writer.storage, writer.schema, seg)
        writer.add_reader(reader)
        reader.close()
    return []

def CLEAR(writer, segments):
    """This policy DELETES all existing segments and only writes the new
    segment.
    """
    _ = writer

    return []

