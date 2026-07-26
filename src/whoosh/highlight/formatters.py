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
"""Formatters for highlighting."""

from collections import deque
from heapq import nlargest
from html import escape as htmlescape
from itertools import groupby
from whoosh.analysis import Token
from whoosh.highlight.fragmenters import Fragment, get_text, mkfrag


class Formatter:
    """Base class for formatters.

    For highlighters that return strings, it is usually only necessary to
    override :meth:`Formatter.format_token`.

    Use the :func:`get_text` function as a convenience to get the token text::

        class MyFormatter(Formatter):
            def format_token(text, token, replace=False):
                ttext = get_text(text, token, replace)
                return "[%s]" % ttext
    """

    between = "..."

    def _text(self, text):
        return text

    def format_token(self, text, token, replace=False):
        """Returns a formatted version of the given "token" object, which
        should have at least ``startchar`` and ``endchar`` attributes, and
        a ``text`` attribute if ``replace`` is True.

        :param text: the original fragment text being highlighted.
        :param token: an object having ``startchar`` and ``endchar`` attributes
            and optionally a ``text`` attribute (if ``replace`` is True).
        :param replace: if True, the original text between the token's
            ``startchar`` and ``endchar`` indices will be replaced with the
            value of the token's ``text`` attribute.
        """

        raise NotImplementedError

    def format_fragment(self, fragment, replace=False):
        """Returns a formatted version of the given text, using the "token"
        objects in the given :class:`Fragment`.

        :param fragment: a :class:`Fragment` object representing a list of
            matches in the text.
        :param replace: if True, the original text corresponding to each
            match will be replaced with the value of the token object's
            ``text`` attribute.
        """

        output = []
        index = fragment.startchar
        text = fragment.text

        # For overlapping tokens (such as in Chinese), sort by position,
        # then by inverse of length.
        # Because the formatter is sequential, it will only pick the first
        # token for a given position to highlight. This makes sure it picks
        # the longest overlapping token.
        for t in sorted(
            fragment.matches,
            key=lambda token: (token.startchar, -(token.endchar - token.startchar)),
        ):
            if t.startchar is None:
                continue
            if t.startchar < index:
                continue
            if t.startchar > index:
                output.append(self._text(text[index : t.startchar]))
            output.append(self.format_token(text, t, replace))
            index = t.endchar
        output.append(self._text(text[index : fragment.endchar]))

        out_string = "".join(output)
        return out_string

    def format(self, fragments, replace=False):
        """Returns a formatted version of the given text, using a list of
        :class:`Fragment` objects.
        """

        formatted = [self.format_fragment(f, replace=replace) for f in fragments]
        return self.between.join(formatted)

    def __call__(self, text, fragments):
        # For backwards compatibility
        return self.format(fragments)


class NullFormatter(Formatter):
    """Formatter that does not modify the string."""

    def format_token(self, text, token, replace=False):
        return get_text(text, token, replace)


class UppercaseFormatter(Formatter):
    """Returns a string in which the matched terms are in UPPERCASE."""

    def __init__(self, between="..."):
        """
        :param between: the text to add between fragments.
        """

        self.between = between

    def format_token(self, text, token, replace=False):
        ttxt = get_text(text, token, replace)
        return ttxt.upper()


class HtmlFormatter(Formatter):
    """Returns a string containing HTML formatting around the matched terms.

    This formatter wraps matched terms in an HTML element with two class names.
    The first class name (set with the constructor argument ``classname``) is
    the same for each match. The second class name (set with the constructor
    argument ``termclass`` is different depending on which term matched. This
    allows you to give different formatting (for example, different background
    colors) to the different terms in the excerpt.

    >>> hf = HtmlFormatter(tagname="span", classname="match", termclass="term")
    >>> hf(mytext, myfragments)
    "The <span class="match term0">template</span> <span class="match term1">geometry</span> is..."

    This object maintains a dictionary mapping terms to HTML class names (e.g.
    ``term0`` and ``term1`` above), so that multiple excerpts will use the same
    class for the same term. If you want to re-use the same HtmlFormatter
    object with different searches, you should call HtmlFormatter.clear()
    between searches to clear the mapping.
    """

    template = "<%(tag)s class=%(q)s%(cls)s%(tn)s%(q)s>%(t)s</%(tag)s>"

    def __init__(
        self,
        tagname="strong",
        between="...",
        classname="match",
        termclass="term",
        maxclasses=5,
        attrquote='"',
    ):
        """
        :param tagname: the tag to wrap around matching terms.
        :param between: the text to add between fragments.
        :param classname: the class name to add to the elements wrapped around
            matching terms.
        :param termclass: the class name prefix for the second class which is
            different for each matched term.
        :param maxclasses: the maximum number of term classes to produce. This
            limits the number of classes you have to define in CSS by recycling
            term class names. For example, if you set maxclasses to 3 and have
            5 terms, the 5 terms will use the CSS classes ``term0``, ``term1``,
            ``term2``, ``term0``, ``term1``.
        """

        self.between = between
        self.tagname = tagname
        self.classname = classname
        self.termclass = termclass
        self.attrquote = attrquote
        self.maxclasses = maxclasses
        self.seen = {}
        self.htmlclass = " ".join((self.classname, self.termclass))

    def _text(self, text):
        return htmlescape(text, quote=False)

    def format_token(self, text, token, replace=False):
        seen = self.seen
        ttext = self._text(get_text(text, token, replace))
        if ttext in seen:
            termnum = seen[ttext]
        else:
            termnum = len(seen) % self.maxclasses
            seen[ttext] = termnum

        return self.template % {
            "tag": self.tagname,
            "q": self.attrquote,
            "cls": self.htmlclass,
            "t": ttext,
            "tn": termnum,
        }

    def clean(self):
        """Clears the dictionary mapping terms to HTML classnames."""
        self.seen = {}


class GenshiFormatter(Formatter):
    """Returns a Genshi event stream containing HTML formatting around the
    matched terms.
    """

    def __init__(self, qname="strong", between="..."):
        """
        :param qname: the QName for the tag to wrap around matched terms.
        :param between: the text to add between fragments.
        """

        self.qname = qname
        self.between = between

        from genshi.core import (  # type: ignore  # type: ignore
            END,
            START,
            TEXT,
            Attrs,
            Stream,
        )

        self.START, self.END, self.TEXT = START, END, TEXT
        self.Attrs, self.Stream = Attrs, Stream

    def _add_text(self, text, output):
        if output and output[-1][0] == self.TEXT:
            output[-1] = (self.TEXT, output[-1][1] + text, output[-1][2])
        else:
            output.append((self.TEXT, text, (None, -1, -1)))

    def format_token(self, text, token, replace=False):
        qn = self.qname
        txt = get_text(text, token, replace)
        return self.Stream(
            [
                (self.START, (qn, self.Attrs()), (None, -1, -1)),
                (self.TEXT, txt, (None, -1, -1)),
                (self.END, qn, (None, -1, -1)),
            ]
        )

    def format_fragment(self, fragment, replace=False):
        output = []
        index = fragment.startchar
        text = fragment.text

        for t in fragment.matches:
            if t.startchar > index:
                self._add_text(text[index : t.startchar], output)
            output.append((text, t, replace))
            index = t.endchar
        if index < len(text):
            self._add_text(text[index:], output)
        return self.Stream(output)

    def format(self, fragments, replace=False):
        output = []
        first = True
        for fragment in fragments:
            if not first:
                self._add_text(self.between, output)
            output += self.format_fragment(fragment, replace=replace)
            first = False
        return self.Stream(output)


def top_fragments(fragments, count, scorer, order, minscore=1):
    scored_fragments = ((scorer(f), f) for f in fragments)
    scored_fragments = nlargest(count, scored_fragments)
    best_fragments = [sf for score, sf in scored_fragments if score >= minscore]
    best_fragments.sort(key=order)
    return best_fragments
