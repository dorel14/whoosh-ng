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
"""Base parser plugins."""

import copy

from whoosh import query
from whoosh.qparser import syntax
from whoosh.qparser.common import attach
from whoosh.qparser.taggers import FnTagger, RegexTagger
from whoosh.util.text import rcompile


class Plugin:
    """Base class for parser plugins."""

    def taggers(self, parser):
        """Should return a list of ``(Tagger, priority)`` tuples to add to the
        syntax the parser understands. Lower priorities run first.
        """

        return ()

    def filters(self, parser):
        """Should return a list of ``(filter_function, priority)`` tuples to
        add to parser. Lower priority numbers run first.

        Filter functions will be called with ``(parser, groupnode)`` and should
        return a group node.
        """

        return ()


class TaggingPlugin(RegexTagger):
    """A plugin that also acts as a Tagger, to avoid having an extra Tagger
    class for simple cases.

    A TaggingPlugin object should have a ``priority`` attribute and either a
    ``nodetype`` attribute or a ``create()`` method. If the subclass doesn't
    override ``create()``, the base class will call ``self.nodetype`` with the
    Match object's named groups as keyword arguments.
    """

    priority = 0

    def __init__(self, expr=None):
        self.expr = rcompile(expr or self.expr)

    def taggers(self, parser):
        return [(self, self.priority)]

    def filters(self, parser):
        return ()

    def create(self, parser, match):
        kwargs = {str(k): v for k, v in match.groupdict().items()}
        return self.nodetype(**kwargs)


class WhitespacePlugin(TaggingPlugin):
    """Tags whitespace and removes it at priority 500. Depending on whether
    your plugin's filter wants to see where whitespace was in the original
    query, it should run with priority lower than 500 (before removal of
    whitespace) or higher than 500 (after removal of whitespace).
    """

    nodetype = syntax.Whitespace
    priority = 100

    def __init__(self, expr=r"\s+"):
        TaggingPlugin.__init__(self, expr)

    def filters(self, parser):
        return [(self.remove_whitespace, 500)]

    def remove_whitespace(self, parser, group):
        newgroup = group.empty_copy()
        for node in group:
            if isinstance(node, syntax.GroupNode):
                newgroup.append(self.remove_whitespace(parser, node))
            elif not node.is_ws():
                newgroup.append(node)
        return newgroup


class SingleQuotePlugin(TaggingPlugin):
    """Adds the ability to specify single "terms" containing spaces by
    enclosing them in single quotes.
    """

    expr = r"(^|(?<=\W))'(?P<text>.*?)'(?=\s|\]|[)}]|$)"
    nodetype = syntax.WordNode


class FunctionPlugin(TaggingPlugin):
    """Adds an abitrary "function call" syntax to the query parser to allow
    advanced and extensible query functionality.

    This is unfinished and experimental.
    """

    expr = rcompile(
        """
    [#](?P<name>[A-Za-z_][A-Za-z0-9._]*)  # function name
    (                                     # optional args
        \\[                               # inside square brackets
        (?P<args>.*?)
        \\]
    )?
    """,
        verbose=True,
    )

    class FunctionNode(syntax.SyntaxNode):
        has_fieldname = False
        has_boost = True
        merging = False

        def __init__(self, name, fn, args, kwargs):
            self.name = name
            self.fn = fn
            self.args = args
            self.kwargs = kwargs
            self.nodes = []
            self.boost = None

        def __repr__(self):
            return f"#{self.name}<{self.args!r}>({self.nodes!r})"

        def query(self, parser):
            qs = [n.query(parser) for n in self.nodes]
            kwargs = self.kwargs
            if "boost" not in kwargs and self.boost is not None:
                kwargs["boost"] = self.boost
            # TODO: If this call raises an exception, return an error query
            return self.fn(qs, *self.args, **self.kwargs)

    def __init__(self, fns):
        """
        :param fns: a dictionary mapping names to functions that return a
            query.
        """

        self.fns = fns

    def create(self, parser, match):
        name = match.group("name")
        if name in self.fns:
            fn = self.fns[name]
            argstring = match.group("args")
            if argstring:
                args, kwargs = self._parse_args(argstring)
            else:
                args = ()
                kwargs = {}
            return self.FunctionNode(name, fn, args, kwargs)

    def _parse_args(self, argstring):
        args = []
        kwargs = {}

        parts = argstring.split(",")
        for part in parts:
            if "=" in part:
                name, value = part.split("=", 1)
                name = name.strip()
            else:
                name = None
                value = part

            value = value.strip()
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            if name:
                kwargs[name] = value
            else:
                args.append(value)

        return args, kwargs

    def filters(self, parser):
        return [(self.do_functions, 600)]

    def do_functions(self, parser, group):
        newgroup = group.empty_copy()
        i = 0
        while i < len(group):
            node = group[i]
            if (
                isinstance(node, self.FunctionNode)
                and i < len(group) - 1
                and isinstance(group[i + 1], syntax.GroupNode)
            ):
                nextnode = group[i + 1]
                node.nodes = list(self.do_functions(parser, nextnode))

                if nextnode.boost != 1:
                    node.set_boost(nextnode.boost)

                i += 1
            elif isinstance(node, syntax.GroupNode):
                node = self.do_functions(parser, node)

            newgroup.append(node)
            i += 1
        return newgroup
