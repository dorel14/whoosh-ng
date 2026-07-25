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
"""Specialized parser plugins."""

import copy

from whoosh import query
from whoosh.qparser import syntax
from whoosh.qparser.common import attach
from whoosh.qparser.taggers import FnTagger, RegexTagger
from whoosh.util.text import rcompile

from whoosh.qparser.plugins._base import Plugin, TaggingPlugin

class BoostPlugin(TaggingPlugin):
    """Adds the ability to boost clauses of the query using the circumflex.

    >>> qp = qparser.QueryParser("content", myschema)
    >>> q = qp.parse("hello there^2")
    """

    expr = "\\^(?P<boost>[0-9]*(\\.[0-9]+)?)($|(?=[ \t\r\n)]))"

    class BoostNode(syntax.SyntaxNode):
        def __init__(self, original, boost):
            self.original = original
            self.boost = boost

        def r(self):
            return f"^ {self.boost}"

    def create(self, parser, match):
        # Override create so we can grab group 0
        original = match.group(0)
        try:
            boost = float(match.group("boost"))
        except ValueError:
            # The text after the ^ wasn't a valid number, so turn it into a
            # word
            node = syntax.WordNode(original)
        else:
            node = self.BoostNode(original, boost)

        return node

    def filters(self, parser):
        return [(self.clean_boost, 0), (self.do_boost, 510)]

    def clean_boost(self, parser, group):
        """This filter finds any BoostNodes in positions where they can't boost
        the previous node (e.g. at the very beginning, after whitespace, or
        after another BoostNode) and turns them into WordNodes.
        """

        bnode = self.BoostNode
        for i, node in enumerate(group):
            if isinstance(node, bnode):
                if not i or not group[i - 1].has_boost:
                    group[i] = syntax.to_word(node)
        return group

    def do_boost(self, parser, group):
        """This filter finds BoostNodes and applies the boost to the previous
        node.
        """

        newgroup = group.empty_copy()
        for node in group:
            if isinstance(node, syntax.GroupNode):
                node = self.do_boost(parser, node)
            elif isinstance(node, self.BoostNode):
                if newgroup and newgroup[-1].has_boost:
                    # Apply the BoostNode's boost to the previous node
                    newgroup[-1].set_boost(node.boost)
                    # Skip adding the BoostNode to the new group
                    continue
                else:
                    node = syntax.to_word(node)
            newgroup.append(node)
        return newgroup

class MultifieldPlugin(Plugin):
    """Converts any unfielded terms into OR clauses that search for the
    term in a specified list of fields.

    >>> qp = qparser.QueryParser(None, myschema)
    >>> qp.add_plugin(qparser.MultifieldPlugin(["a", "b"])
    >>> qp.parse("alfa c:bravo")
    And([Or([Term("a", "alfa"), Term("b", "alfa")]), Term("c", "bravo")])

    This plugin is the basis for the ``MultifieldParser``.
    """

    def __init__(self, fieldnames, fieldboosts=None, group=syntax.OrGroup):
        """
        :param fieldnames: a list of fields to search.
        :param fieldboosts: an optional dictionary mapping field names to
            a boost to use for that field.
        :param group: the group to use to relate the fielded terms to each
            other.
        """

        self.fieldnames = fieldnames
        self.boosts = fieldboosts or {}
        self.group = group

    def filters(self, parser):
        # Run after the fields filter applies explicit fieldnames (at priority
        # 100)
        return [(self.do_multifield, 110)]

    def do_multifield(self, parser, group):
        for i, node in enumerate(group):
            if isinstance(node, syntax.GroupNode):
                # Recurse inside groups
                group[i] = self.do_multifield(parser, node)
            elif node.has_fieldname and node.fieldname is None:
                # For an unfielded node, create a new group containing fielded
                # versions of the node for each configured "multi" field.
                newnodes = []
                for fname in self.fieldnames:
                    newnode = copy.copy(node)
                    newnode.set_fieldname(fname)
                    newnode.set_boost(self.boosts.get(fname, 1.0))
                    newnodes.append(newnode)
                group[i] = self.group(newnodes)
        return group

class FieldAliasPlugin(Plugin):
    """Adds the ability to use "aliases" of fields in the query string.

    This plugin is useful for allowing users of languages that can't be
    represented in ASCII to use field names in their own language, and
    translate them into the "real" field names, which must be valid Python
    identifiers.

    >>> # Allow users to use 'body' or 'text' to refer to the 'content' field
    >>> parser.add_plugin(FieldAliasPlugin({"content": ["body", "text"]}))
    >>> parser.parse("text:hello")
    Term("content", "hello")
    """

    def __init__(self, fieldmap):
        self.fieldmap = fieldmap
        self.reverse = {}
        for key, values in fieldmap.items():
            for value in values:
                self.reverse[value] = key

    def filters(self, parser):
        # Run before fields plugin at 100
        return [(self.do_aliases, 90)]

    def do_aliases(self, parser, group):
        for i, node in enumerate(group):
            if isinstance(node, syntax.GroupNode):
                group[i] = self.do_aliases(parser, node)
            elif node.has_fieldname and node.fieldname is not None:
                fname = node.fieldname
                if fname in self.reverse:
                    node.set_fieldname(self.reverse[fname], override=True)
        return group

class CopyFieldPlugin(Plugin):
    """Looks for basic syntax nodes (terms, prefixes, wildcards, phrases, etc.)
    occurring in a certain field and replaces it with a group (by default OR)
    containing the original token and the token copied to a new field.

    For example, the query::

        hello name:matt

    could be automatically converted by ``CopyFieldPlugin({"name", "author"})``
    to::

        hello (name:matt OR author:matt)

    This is useful where one field was indexed with a differently-analyzed copy
    of another, and you want the query to search both fields.

    You can specify a different group type with the ``group`` keyword. You can
    also specify ``group=None``, in which case the copied node is inserted
    "inline" next to the original, instead of in a new group::

        hello name:matt author:matt
    """

    def __init__(self, map, group=syntax.OrGroup, mirror=False):
        """
        :param map: a dictionary mapping names of fields to copy to the
            names of the destination fields.
        :param group: the type of group to create in place of the original
            token. You can specify ``group=None`` to put the copied node
            "inline" next to the original node instead of in a new group.
        :param two_way: if True, the plugin copies both ways, so if the user
            specifies a query in the 'toname' field, it will be copied to
            the 'fromname' field.
        """

        self.map = map
        self.group = group
        if mirror:
            # Add in reversed mappings
            map.update({v: k for k, v in map.items()})

    def filters(self, parser):
        # Run after the fieldname filter (100) but before multifield (110)
        return [(self.do_copyfield, 109)]

    def do_copyfield(self, parser, group):
        map = self.map
        newgroup = group.empty_copy()
        for node in group:
            if isinstance(node, syntax.GroupNode):
                # Recurse into groups
                node = self.do_copyfield(parser, node)
            elif node.has_fieldname:
                fname = node.fieldname or parser.fieldname
                if fname in map:
                    newnode = copy.copy(node)
                    newnode.set_fieldname(map[fname], override=True)
                    if self.group is None:
                        newgroup.append(node)
                        newgroup.append(newnode)
                    else:
                        newgroup.append(self.group([node, newnode]))
                    continue
            newgroup.append(node)
        return newgroup

class PseudoFieldPlugin(Plugin):
    """This is an advanced plugin that lets you define "pseudo-fields" the user
    can use in their queries. When the parser encounters one of these fields,
    it runs a given function on the following node in the abstract syntax tree.

    Unfortunately writing the transform function(s) requires knowledge of the
    parser's abstract syntax tree classes. A transform function takes a
    :class:`whoosh.qparser.SyntaxNode` and returns a
    :class:`~whoosh.qparser.SyntaxNode` (or None if the node should be removed
    instead of transformed).

    Some things you can do in the transform function::

        from whoosh import qparser

        def my_xform_fn(node):
            # Is this a text node?
            if node.has_text:
                # Change the node's text
                node.text = node.text + "foo"

                # Change the node into a prefix query
                node = qparser.PrefixPlugin.PrefixNode(node.text)

                # Set the field the node should search in
                node.set_fieldname("title")

                return node
            else:
                # If the pseudo-field wasn't applied to a text node (e.g.
                # it preceded a group, as in ``pfield:(a OR b)`` ), remove the
                # node. Alternatively you could just ``return node`` here to
                # leave the non-text node intact.
                return None

    In the following example, if the user types ``regex:foo.bar``, the function
    transforms the text in the pseudo-field "regex" into a regular expression
    query in the "content" field::

        from whoosh import qparser

        def regex_maker(node):
            if node.has_text:
                node = qparser.RegexPlugin.RegexNode(node.text)
                node.set_fieldname("content")
                return node

        qp = qparser.QueryParser("content", myindex.schema)
        qp.add_plugin(qparser.PseudoFieldPlugin({"regex": regex_maker}))
        q = qp.parse("alfa regex:br.vo")

    The name of the "pseudo" field can be the same as an actual field. Imagine
    the schema has a field named ``reverse``, and you want the user to be able
    to type ``reverse:foo`` and transform it to ``reverse:(foo OR oof)``::

        def rev_text(node):
            if node.has_text:
                # Create a word node for the reversed text
                revtext = node.text[::-1]  # Reverse the text
                rnode = qparser.WordNode(revtext)

                # Put the original node and the reversed node in an OrGroup
                group = qparser.OrGroup([node, rnode])

                # Need to set the fieldname here because the PseudoFieldPlugin
                # removes the field name syntax
                group.set_fieldname("reverse")

                return group

        qp = qparser.QueryParser("content", myindex.schema)
        qp.add_plugin(qparser.PseudoFieldPlugin({"reverse": rev_text}))
        q = qp.parse("alfa reverse:bravo")

    Note that transforming the query like this can potentially really confuse
    the spell checker!

    This plugin works as a filter, so it can only operate on the query after it
    has been parsed into an abstract syntax tree. For parsing control (i.e. to
    give a pseudo-field its own special syntax), you would need to write your
    own parsing plugin.
    """

    def __init__(self, xform_map):
        """
        :param xform_map: a dictionary mapping psuedo-field names to transform
            functions. The function should take a
            :class:`whoosh.qparser.SyntaxNode` as an argument, and return a
            :class:`~whoosh.qparser.SyntaxNode`. If the function returns None,
            the node will be removed from the query.
        """

        self.xform_map = xform_map

    def filters(self, parser):
        # Run before the fieldname filter (100)
        return [(self.do_pseudofield, 99)]

    def do_pseudofield(self, parser, group):
        xform_map = self.xform_map

        newgroup = group.empty_copy()
        xform_next = None
        for node in group:
            if isinstance(node, syntax.GroupNode):
                node = self.do_pseudofield(parser, node)
            elif isinstance(node, syntax.FieldnameNode) and node.fieldname in xform_map:
                xform_next = xform_map[node.fieldname]
                continue

            if xform_next:
                newnode = xform_next(node)
                xform_next = None
                if newnode is None:
                    continue
                else:
                    newnode.set_range(node.startchar, node.endchar)
                    node = newnode

            newgroup.append(node)

        return newgroup

