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
"""Term-based parser plugins."""

import copy

from whoosh import query
from whoosh.qparser import syntax
from whoosh.qparser.common import attach
from whoosh.qparser.plugins._base import Plugin, TaggingPlugin
from whoosh.qparser.taggers import FnTagger, RegexTagger
from whoosh.util.text import rcompile


class PrefixPlugin(TaggingPlugin):
    """Adds the ability to specify prefix queries by ending a term with an
    asterisk.

    This plugin is useful if you want the user to be able to create prefix but
    not wildcard queries (for performance reasons). If you are including the
    wildcard plugin, you should not include this plugin as well.

    >>> qp = qparser.QueryParser("content", myschema)
    >>> qp.remove_plugin_class(qparser.WildcardPlugin)
    >>> qp.add_plugin(qparser.PrefixPlugin())
    >>> q = qp.parse("pre*")
    """

    class PrefixNode(syntax.TextNode):
        qclass = query.Prefix

        def r(self):
            return f"{self.text!r}*"

    expr = "(?P<text>[^ \t\r\n*]+)[*](?= |$|\\))"
    nodetype = PrefixNode


class WildcardPlugin(TaggingPlugin):
    # \u055E = Armenian question mark
    # \u061F = Arabic question mark
    # \u1367 = Ethiopic question mark
    qmarks = "?\u055e\u061f\u1367"
    expr = f"(?P<text>[*{qmarks}])"

    def filters(self, parser):
        # Run early, but definitely before multifield plugin
        return [(self.do_wildcards, 50)]

    def do_wildcards(self, parser, group):
        i = 0
        while i < len(group):
            node = group[i]
            if isinstance(node, self.WildcardNode):
                if i < len(group) - 1 and group[i + 1].is_text():
                    nextnode = group.pop(i + 1)
                    node.text += nextnode.text
                if i > 0 and group[i - 1].is_text():
                    prevnode = group.pop(i - 1)
                    node.text = prevnode.text + node.text
                else:
                    i += 1
            else:
                if isinstance(node, syntax.GroupNode):
                    self.do_wildcards(parser, node)
                i += 1

        for i in range(len(group)):
            node = group[i]
            if isinstance(node, self.WildcardNode):
                text = node.text
                if len(text) > 1 and not any(qm in text for qm in self.qmarks):
                    if text.find("*") == len(text) - 1:
                        newnode = PrefixPlugin.PrefixNode(text[:-1])
                        newnode.startchar = node.startchar
                        newnode.endchar = node.endchar
                        group[i] = newnode
        return group

    class WildcardNode(syntax.TextNode):
        # Note that this node inherits tokenize = False from TextNode,
        # so the text in this node will not be analyzed... just passed
        # straight to the query

        qclass = query.Wildcard

        def r(self):
            return f"Wild {self.text!r}"

    nodetype = WildcardNode


class RegexPlugin(TaggingPlugin):
    """Adds the ability to specify regular expression term queries.

    The default syntax for a regular expression term is ``r"termexpr"``.

    >>> qp = qparser.QueryParser("content", myschema)
    >>> qp.add_plugin(qparser.RegexPlugin())
    >>> q = qp.parse('foo title:r"bar+"')
    """

    class RegexNode(syntax.TextNode):
        qclass = query.Regex

        def r(self):
            return f"Regex {self.text!r}"

    expr = 'r"(?P<text>[^"]*)"'
    nodetype = RegexNode


class FuzzyTermPlugin(TaggingPlugin):
    """Adds syntax to the query parser to create "fuzzy" term queries, which
    match any term within a certain "edit distance" (number of inserted,
    deleted, or transposed characters) by appending a tilde (``~``) and an
    optional maximum edit distance to a term. If you don't specify an explicit
    maximum edit distance, the default is 1.

    >>> qp = qparser.QueryParser("content", myschema)
    >>> qp.add_plugin(qparser.FuzzyTermPlugin())
    >>> q = qp.parse("Stephen~2 Colbert")

    For example, the following query creates a :class:`whoosh.query.FuzzyTerm`
    query with a maximum edit distance of 1::

        bob~

    The following creates a fuzzy term query with a maximum edit distance of
    2::

        bob~2

    The maximum edit distance can only be a single digit. Note that edit
    distances greater than 2 can take an extremely long time and are generally
    not useful.

    You can specify a prefix length using ``~n/m``. For example, to allow a
    maximum edit distance of 2 and require a prefix match of 3 characters::

        johannson~2/3

    To specify a prefix with the default edit distance::

        johannson~/3
    """

    expr = rcompile(
        """
    (?<=\\S)                          # Only match right after non-space
    ~                                 # Initial tilde
    (?P<maxdist>[0-9])?               # Optional maxdist
    (/                                # Optional prefix slash
        (?P<prefix>[1-9][0-9]*)       # prefix
    )?                                # (end prefix group)
    """,
        verbose=True,
    )

    class FuzzinessNode(syntax.SyntaxNode):
        def __init__(self, maxdist, prefixlength, original):
            self.maxdist = maxdist
            self.prefixlength = prefixlength
            self.original = original

        def __repr__(self):
            return "<~%d/%d>" % (self.maxdist, self.prefixlength)

    class FuzzyTermNode(syntax.TextNode):
        qclass = query.FuzzyTerm

        def __init__(self, wordnode, maxdist, prefixlength):
            self.fieldname = wordnode.fieldname
            self.text = wordnode.text
            self.boost = wordnode.boost
            self.startchar = wordnode.startchar
            self.endchar = wordnode.endchar
            self.maxdist = maxdist
            self.prefixlength = prefixlength

        def r(self):
            return "%r ~%d/%d" % (self.text, self.maxdist, self.prefixlength)

        def query(self, parser):
            # Use the superclass's query() method to create a FuzzyTerm query
            # (it looks at self.qclass), just because it takes care of some
            # extra checks and attributes
            q = syntax.TextNode.query(self, parser)
            # Set FuzzyTerm-specific attributes
            q.maxdist = self.maxdist
            q.prefixlength = self.prefixlength
            return q

    def create(self, parser, match):
        mdstr = match.group("maxdist")
        maxdist = int(mdstr) if mdstr else 1

        pstr = match.group("prefix")
        prefixlength = int(pstr) if pstr else 0

        return self.FuzzinessNode(maxdist, prefixlength, match.group(0))

    def filters(self, parser):
        return [(self.do_fuzzyterms, 0)]

    def do_fuzzyterms(self, parser, group):
        newgroup = group.empty_copy()
        i = 0
        while i < len(group):
            node = group[i]
            if i < len(group) - 1 and isinstance(node, syntax.WordNode):
                nextnode = group[i + 1]
                if isinstance(nextnode, self.FuzzinessNode):
                    node = self.FuzzyTermNode(node, nextnode.maxdist, nextnode.prefixlength)
                    i += 1
            if isinstance(node, self.FuzzinessNode):
                node = syntax.to_word(node)
            if isinstance(node, syntax.GroupNode):
                node = self.do_fuzzyterms(parser, node)

            newgroup.append(node)
            i += 1
        return newgroup


class EveryPlugin(TaggingPlugin):
    expr = "[*]:[*]"
    priority = -1

    def create(self, parser, match):
        return self.EveryNode()

    class EveryNode(syntax.SyntaxNode):
        def r(self):
            return "*:*"

        def query(self, parser):
            return query.Every()


class FieldsPlugin(TaggingPlugin):
    """Adds the ability to specify the field of a clause."""

    class FieldnameTagger(RegexTagger):
        def create(self, parser, match):
            return syntax.FieldnameNode(match.group("text"), match.group(0))

    def __init__(self, expr=r"(?P<text>\w+|[*]):", remove_unknown=True):
        """
        :param expr: the regular expression to use for tagging fields.
        :param remove_unknown: if True, converts field specifications for
            fields that aren't in the schema into regular text.
        """

        self.expr = expr
        self.removeunknown = remove_unknown

    def taggers(self, parser):
        return [(self.FieldnameTagger(self.expr), 0)]

    def filters(self, parser):
        return [(self.do_fieldnames, 100)]

    def do_fieldnames(self, parser, group):
        """This filter finds FieldnameNodes in the tree and applies their
        fieldname to the next node.
        """

        fnclass = syntax.FieldnameNode

        if self.removeunknown and parser.schema:
            # Look for field nodes that aren't in the schema and convert them
            # to text
            schema = parser.schema
            newgroup = group.empty_copy()
            prev_field_node = None

            for node in group:
                if isinstance(node, fnclass) and node.fieldname not in schema:
                    prev_field_node = node
                    continue
                elif prev_field_node:
                    # If prev_field_node is not None, it contains a field node
                    # that appeared before this node but isn't in the schema,
                    # so we'll convert it to text here
                    if node.has_text:
                        node.text = prev_field_node.original + node.text
                    else:
                        newgroup.append(syntax.to_word(prev_field_node))
                    prev_field_node = None
                newgroup.append(node)
            if prev_field_node:
                newgroup.append(syntax.to_word(prev_field_node))
            group = newgroup

        newgroup = group.empty_copy()
        # Iterate backwards through the stream, looking for field-able objects
        # with field nodes in front of them
        i = len(group)
        while i > 0:
            i -= 1
            node = group[i]
            if isinstance(node, fnclass):
                # If we see a fieldname node, it must not have been in front
                # of something fieldable, since we would have already removed
                # it (since we're iterating backwards), so convert it to text
                node = syntax.to_word(node)
            elif isinstance(node, syntax.GroupNode):
                node = self.do_fieldnames(parser, node)

            if i > 0 and not node.is_ws() and isinstance(group[i - 1], fnclass):
                node.set_fieldname(group[i - 1].fieldname, override=False)
                i -= 1

            newgroup.append(node)
        newgroup.reverse()
        return newgroup

