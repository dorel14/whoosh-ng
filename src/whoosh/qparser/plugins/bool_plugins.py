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
"""Boolean/structural parser plugins."""

import copy

from whoosh import query
from whoosh.qparser import syntax
from whoosh.qparser.common import attach
from whoosh.qparser.plugins._base import Plugin, TaggingPlugin
from whoosh.qparser.taggers import FnTagger, RegexTagger
from whoosh.util.text import rcompile


class GroupPlugin(Plugin):
    """Adds the ability to group clauses using parentheses."""

    # Marker nodes for open and close bracket

    class OpenBracket(syntax.SyntaxNode):
        def r(self):
            return "("

    class CloseBracket(syntax.SyntaxNode):
        def r(self):
            return ")"

    def __init__(self, openexpr="[(]", closeexpr="[)]"):
        self.openexpr = openexpr
        self.closeexpr = closeexpr

    def taggers(self, parser):
        return [
            (FnTagger(self.openexpr, self.OpenBracket, "openB"), 0),
            (FnTagger(self.closeexpr, self.CloseBracket, "closeB"), 0),
        ]

    def filters(self, parser):
        return [(self.do_groups, 0)]

    def do_groups(self, parser, group):
        """This filter finds open and close bracket markers in a flat group
        and uses them to organize the nodes into a hierarchy.
        """

        ob, cb = self.OpenBracket, self.CloseBracket
        # Group hierarchy stack
        stack = [parser.group()]
        for node in group:
            if isinstance(node, ob):
                # Open bracket: push a new level of hierarchy on the stack
                stack.append(parser.group())
            elif isinstance(node, cb):
                # Close bracket: pop the current level of hierarchy and append
                # it to the previous level
                if len(stack) > 1:
                    last = stack.pop()
                    stack[-1].append(last)
            else:
                # Anything else: add it to the current level of hierarchy
                stack[-1].append(node)

        top = stack[0]
        # If the parens were unbalanced (more opens than closes), just take
        # whatever levels of hierarchy were left on the stack and tack them on
        # the end of the top-level
        if len(stack) > 1:
            for ls in stack[1:]:
                top.extend(ls)

        if len(top) == 1 and isinstance(top[0], syntax.GroupNode):
            boost = top.boost
            top = top[0]
            top.boost = boost

        return top


class PhrasePlugin(Plugin):
    """Adds the ability to specify phrase queries inside double quotes."""

    # Didn't use TaggingPlugin because I need to add slop parsing at some
    # point

    # Expression used to find words if a schema isn't available
    wordexpr = rcompile(r"\S+")

    class PhraseNode(syntax.TextNode):
        def __init__(self, text, textstartchar, slop=1):
            syntax.TextNode.__init__(self, text)
            self.textstartchar = textstartchar
            self.slop = slop

        def r(self):
            return f"{self.__class__.__name__} {self.text!r}~{self.slop}"

        def apply(self, fn):
            return self.__class__(
                self.type,
                [fn(node) for node in self.nodes],
                slop=self.slop,
                boost=self.boost,
            )

        def query(self, parser):
            text = self.text
            fieldname = self.fieldname or parser.fieldname

            # We want to process the text of the phrase into "words" (tokens),
            # and also record the startchar and endchar of each word

            sc = self.textstartchar
            if parser.schema and fieldname in parser.schema:
                field = parser.schema[fieldname]
                if field.analyzer:
                    # We have a field with an analyzer, so use it to parse
                    # the phrase into tokens
                    tokens = field.tokenize(text, mode="query", chars=True)
                    words = []
                    char_ranges = []
                    for t in tokens:
                        words.append(t.text)
                        char_ranges.append((sc + t.startchar, sc + t.endchar))
                else:
                    # We have a field but it doesn't have a format object,
                    # for some reason (it's self-parsing?), so use process_text
                    # to get the texts (we won't know the start/end chars)
                    words = list(field.process_text(text, mode="query"))
                    char_ranges = [(None, None)] * len(words)
            else:
                # We're parsing without a schema, so just use the default
                # regular expression to break the text into words
                words = []
                char_ranges = []
                for match in PhrasePlugin.wordexpr.finditer(text):
                    words.append(match.group(0))
                    char_ranges.append((sc + match.start(), sc + match.end()))

            qclass = parser.phraseclass
            q = qclass(
                fieldname,
                words,
                slop=self.slop,
                boost=self.boost,
                char_ranges=char_ranges,
            )
            return attach(q, self)

    class PhraseTagger(RegexTagger):
        def create(self, parser, match):
            text = match.group("text")
            textstartchar = match.start("text")
            slopstr = match.group("slop")
            slop = int(slopstr) if slopstr else 1
            return PhrasePlugin.PhraseNode(text, textstartchar, slop)

    def __init__(self, expr='"(?P<text>.*?)"(~(?P<slop>[1-9][0-9]*))?'):
        self.expr = expr

    def taggers(self, parser):
        return [(self.PhraseTagger(self.expr), 0)]


class SequencePlugin(Plugin):
    """Adds the ability to group arbitrary queries inside double quotes to
    produce a query matching the individual sub-queries in sequence.

    To enable this plugin, first remove the default PhrasePlugin, then add
    this plugin::

        qp = qparser.QueryParser("field", my_schema)
        qp.remove_plugin_class(qparser.PhrasePlugin)
        qp.add_plugin(qparser.SequencePlugin())

    This enables parsing "phrases" such as::

        "(jon OR john OR jonathan~1) smith*"
    """

    def __init__(self, expr='["](~(?P<slop>[1-9][0-9]*))?'):
        """
        :param expr: a regular expression for the marker at the start and end
            of a phrase. The default is the double-quotes character.
        """

        self.expr = expr

    class SequenceNode(syntax.GroupNode):
        qclass = query.Sequence

    class QuoteNode(syntax.MarkerNode):
        def __init__(self, slop=None):
            self.slop = int(slop) if slop else 1

    def taggers(self, parser):
        return [(FnTagger(self.expr, self.QuoteNode, "quote"), 0)]

    def filters(self, parser):
        return [(self.do_quotes, 550)]

    def do_quotes(self, parser, group):
        # New group to copy nodes into
        newgroup = group.empty_copy()
        # Buffer for sequence nodes; when it's None, it means we're not in
        # a sequence
        seq = None

        # Start copying nodes from group to newgroup. When we find a quote
        # node, start copying nodes into the buffer instead. When we find
        # the next (end) quote, put the buffered nodes into a SequenceNode
        # and add it to newgroup.
        for node in group:
            if isinstance(node, syntax.GroupNode):
                # Recurse
                node = self.do_quotes(parser, node)

            if isinstance(node, self.QuoteNode):
                if seq is None:
                    # Start a new sequence
                    seq = []
                else:
                    # End the current sequence
                    sn = self.SequenceNode(seq, slop=node.slop)
                    newgroup.append(sn)
                    seq = None
            elif seq is None:
                # Not in a sequence, add directly
                newgroup.append(node)
            else:
                # In a sequence, add it to the buffer
                seq.append(node)

        # We can end up with buffered nodes if there was an unbalanced quote;
        # just add the buffered nodes directly to newgroup
        if seq is not None:
            newgroup.extend(seq)

        return newgroup


class OperatorsPlugin(Plugin):
    """By default, adds the AND, OR, ANDNOT, ANDMAYBE, and NOT operators to
    the parser syntax. This plugin scans the token stream for subclasses of
    :class:`Operator` and calls their :meth:`Operator.make_group` methods
    to allow them to manipulate the stream.

    There are two levels of configuration available.

    The first level is to change the regular expressions of the default
    operators, using the ``And``, ``Or``, ``AndNot``, ``AndMaybe``, and/or
    ``Not`` keyword arguments. The keyword value can be a pattern string or
    a compiled expression, or None to remove the operator::

        qp = qparser.QueryParser("content", schema)
        cp = qparser.OperatorsPlugin(And="&", Or="\\|", AndNot="&!",
                                     AndMaybe="&~", Not=None)
        qp.replace_plugin(cp)

    You can also specify a list of ``(OpTagger, priority)`` pairs as the first
    argument to the initializer to use custom operators. See :ref:`custom-op`
    for more information on this.
    """

    class OpTagger(RegexTagger):
        def __init__(self, expr, grouptype, optype=syntax.InfixOperator, leftassoc=True, memo=""):
            RegexTagger.__init__(self, expr)
            self.grouptype = grouptype
            self.optype = optype
            self.leftassoc = leftassoc
            self.memo = memo

        def __repr__(self):
            return f"<{self.__class__.__name__} {self.expr.pattern!r} ({self.memo})>"

        def create(self, parser, match):
            return self.optype(match.group(0), self.grouptype, self.leftassoc)

    def __init__(
        self,
        ops=None,
        clean=False,
        And=r"(?<=\s)AND(?=\s)",
        Or=r"(?<=\s)OR(?=\s)",
        AndNot=r"(?<=\s)ANDNOT(?=\s)",
        AndMaybe=r"(?<=\s)ANDMAYBE(?=\s)",
        Not=r"(^|(?<=(\s|[()])))NOT(?=\s)",
        Require=r"(^|(?<=\s))REQUIRE(?=\s)",
    ):
        if ops:
            ops = list(ops)
        else:
            ops = []

        if not clean:
            ot = self.OpTagger
            if Not:
                ops.append((ot(Not, syntax.NotGroup, syntax.PrefixOperator, memo="not"), 0))
            if And:
                ops.append((ot(And, syntax.AndGroup, memo="and"), 0))
            if Or:
                ops.append((ot(Or, syntax.OrGroup, memo="or"), 0))
            if AndNot:
                ops.append((ot(AndNot, syntax.AndNotGroup, memo="anot"), -5))
            if AndMaybe:
                ops.append((ot(AndMaybe, syntax.AndMaybeGroup, memo="amaybe"), -5))
            if Require:
                ops.append((ot(Require, syntax.RequireGroup, memo="req"), 0))

        self.ops = ops

    def taggers(self, parser):
        return self.ops

    def filters(self, parser):
        return [(self.do_operators, 600)]

    def do_operators(self, parser, group):
        """This filter finds PrefixOperator, PostfixOperator, and InfixOperator
        nodes in the tree and calls their logic to rearrange the nodes.
        """

        for tagger, _ in self.ops:
            # Get the operators created by the configured taggers
            optype = tagger.optype
            gtype = tagger.grouptype

            # Left-associative infix operators are replaced left-to-right, and
            # right-associative infix operators are replaced right-to-left.
            # Most of the work is done in the different implementations of
            # Operator.replace_self().
            if tagger.leftassoc:
                i = 0
                while i < len(group):
                    t = group[i]
                    if isinstance(t, optype) and t.grouptype is gtype:
                        i = t.replace_self(parser, group, i)
                    else:
                        i += 1
            else:
                i = len(group) - 1
                while i >= 0:
                    t = group[i]
                    if isinstance(t, optype):
                        i = t.replace_self(parser, group, i)
                    i -= 1

        # Descend into the groups and recursively call do_operators
        for i, t in enumerate(group):
            if isinstance(t, syntax.GroupNode):
                group[i] = self.do_operators(parser, t)

        return group


class PlusMinusPlugin(Plugin):
    """Adds the ability to use + and - in a flat OR query to specify required
    and prohibited terms.

    This is the basis for the parser configuration returned by
    ``SimpleParser()``.
    """

    # Marker nodes for + and -

    class Plus(syntax.MarkerNode):
        pass

    class Minus(syntax.MarkerNode):
        pass

    def __init__(self, plusexpr="\\+", minusexpr="-"):
        self.plusexpr = plusexpr
        self.minusexpr = minusexpr

    def taggers(self, parser):
        return [
            (FnTagger(self.plusexpr, self.Plus, "plus"), 0),
            (FnTagger(self.minusexpr, self.Minus, "minus"), 0),
        ]

    def filters(self, parser):
        return [(self.do_plusminus, 510)]

    def do_plusminus(self, parser, group):
        """This filter sorts nodes in a flat group into "required", "optional",
        and "banned" subgroups based on the presence of plus and minus nodes.
        """

        required = syntax.AndGroup()
        optional = syntax.OrGroup()
        banned = syntax.OrGroup()

        # If the top-level group is an AndGroup we make everything "required" by default
        if isinstance(group, syntax.AndGroup):
            optional = syntax.AndGroup()

        # Which group to put the next node we see into
        next = optional
        for node in group:
            if isinstance(node, self.Plus):
                # +: put the next node in the required group
                next = required
            elif isinstance(node, self.Minus):
                # -: put the next node in the banned group
                next = banned
            else:
                # Anything else: put it in the appropriate group
                next.append(node)
                # Reset to putting things in the optional group by default
                next = optional

        group = optional
        if required:
            group = syntax.AndMaybeGroup([required, group])
        if banned:
            group = syntax.AndNotGroup([group, banned])
        return group


class GtLtPlugin(TaggingPlugin):
    """Allows the user to use greater than/less than symbols to create range
    queries::

        a:>100 b:<=z c:>=-1.4 d:<mz

    This is the equivalent of::

        a:{100 to] b:[to z] c:[-1.4 to] d:[to mz}

    The plugin recognizes ``>``, ``<``, ``>=``, ``<=``, ``=>``, and ``=<``
    after a field specifier. The field specifier is required. You cannot do the
    following::

        >100

    This plugin requires the FieldsPlugin and RangePlugin to work.
    """

    class GtLtNode(syntax.SyntaxNode):
        def __init__(self, rel):
            self.rel = rel

        def __repr__(self):
            return f"({self.rel})"

    expr = r"(?P<rel>(<=|>=|<|>|=<|=>))"
    nodetype = GtLtNode

    def filters(self, parser):
        # Run before the fields filter removes FilenameNodes at priority 100.
        return [(self.do_gtlt, 99)]

    def do_gtlt(self, parser, group):
        """This filter translate FieldnameNode/GtLtNode pairs into RangeNodes."""

        fname = syntax.FieldnameNode
        newgroup = group.empty_copy()
        i = 0
        lasti = len(group) - 1
        while i < len(group):
            node = group[i]
            # If this is a GtLtNode...
            if isinstance(node, self.GtLtNode):
                # If it's not the last node in the group...
                if i < lasti:
                    prevnode = newgroup[-1]
                    nextnode = group[i + 1]
                    # If previous was a fieldname and next node has text
                    if isinstance(prevnode, fname) and nextnode.has_text:
                        # Make the next node into a range based on the symbol
                        newgroup.append(self.make_range(nextnode, node.rel))
                        # Skip the next node
                        i += 1
            elif isinstance(node, syntax.GroupNode):
                newgroup.append(self.do_gtlt(parser, node))
            else:
                # If it's not a GtLtNode, add it to the filtered group
                newgroup.append(node)
            i += 1

        return newgroup

    def make_range(self, node, rel):
        text = node.text
        if rel == "<":
            n = syntax.RangeNode(None, text, False, True)
        elif rel == ">":
            n = syntax.RangeNode(text, None, True, False)
        elif rel == "<=" or rel == "=<":
            n = syntax.RangeNode(None, text, False, False)
        elif rel == ">=" or rel == "=>":
            n = syntax.RangeNode(text, None, False, False)
        return n.set_range(node.startchar, node.endchar)

