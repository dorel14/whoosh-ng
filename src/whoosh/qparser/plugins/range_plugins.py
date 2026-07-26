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
"""Range parser plugin."""

import copy

from whoosh import query
from whoosh.qparser import syntax
from whoosh.qparser.common import attach
from whoosh.qparser.taggers import FnTagger, RegexTagger
from whoosh.util.text import rcompile

from whoosh.qparser.plugins._base import Plugin, TaggingPlugin


class RangePlugin(Plugin):
    """Adds the ability to specify term ranges."""

    expr = rcompile(
        r"""
    (?P<open>\{|\[)               # Open paren
    (?P<start>
        ('[^']*?'\s+)             # single-quoted
        |                         # or
        ([^\]}]+?(?=[Tt][Oo]))    # everything until "to"
    )?
    [Tt][Oo]                      # "to"
    (?P<end>
        (\s+'[^']*?')             # single-quoted
        |                         # or
        ([^\]}]+?)                # everything until "]" or "}"
    )?
    (?P<close>}|])                # Close paren
    """,
        verbose=True,
    )

    class RangeTagger(RegexTagger):
        def __init__(self, expr, excl_start, excl_end):
            self.expr = expr
            self.excl_start = excl_start
            self.excl_end = excl_end

        def create(self, parser, match):
            start = match.group("start")
            end = match.group("end")
            if start:
                # Strip the space before the "to"
                start = start.rstrip()
                # Strip single quotes
                if start.startswith("'") and start.endswith("'"):
                    start = start[1:-1]
            if end:
                # Strip the space before the "to"
                end = end.lstrip()
                # Strip single quotes
                if end.startswith("'") and end.endswith("'"):
                    end = end[1:-1]
            # What kind of open and close brackets were used?
            startexcl = match.group("open") == self.excl_start
            endexcl = match.group("close") == self.excl_end

            rn = syntax.RangeNode(start, end, startexcl, endexcl)
            return rn

    def __init__(self, expr=None, excl_start="{", excl_end="}"):
        self.expr = expr or self.expr
        self.excl_start = excl_start
        self.excl_end = excl_end

    def taggers(self, parser):
        tagger = self.RangeTagger(self.expr, self.excl_start, self.excl_end)
        return [(tagger, 1)]
