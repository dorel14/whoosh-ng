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
"""Fragmenters and fragment scorers for highlighting."""

from collections import deque
from heapq import nlargest
from html import escape as htmlescape
from itertools import groupby

from whoosh.analysis import Token

DEFAULT_CHARLIMIT = 2**15


def mkfrag(text, tokens, startchar=None, endchar=None, charsbefore=0, charsafter=0):
    """Returns a :class:`Fragment` object based on the :class:`analysis.Token`
    objects in ``tokens`.
    """

    if startchar is None:
        startchar = tokens[0].startchar if tokens else 0
    if endchar is None:
        endchar = tokens[-1].endchar if tokens else len(text)

    startchar = max(0, startchar - charsbefore)
    endchar = min(len(text), endchar + charsafter)

    return Fragment(text, tokens, startchar, endchar)


class Fragment:
    """Represents a fragment (extract) from a hit document. This object is
    mainly used to keep track of the start and end points of the fragment and
    the "matched" character ranges inside; it does not contain the text of the
    fragment or do much else.

    The useful attributes are:

    ``Fragment.text``
        The entire original text from which this fragment is taken.

    ``Fragment.matches``
        An ordered list of objects representing the matched terms in the
        fragment. These objects have ``startchar`` and ``endchar`` attributes.

    ``Fragment.startchar``
        The index of the first character in the fragment.

    ``Fragment.endchar``
        The index of the last character in the fragment.

    ``Fragment.matched_terms``
        A ``set`` of the ``text`` of the matched terms in the fragment (if
        available).
    """

    def __init__(self, text, matches, startchar=0, endchar=-1):
        """
        :param text: the source text of the fragment.
        :param matches: a list of objects which have ``startchar`` and
            ``endchar`` attributes, and optionally a ``text`` attribute.
        :param startchar: the index into ``text`` at which the fragment starts.
            The default is 0.
        :param endchar: the index into ``text`` at which the fragment ends.
            The default is -1, which is interpreted as the length of ``text``.
        """

        self.text = text
        self.matches = matches

        if endchar == -1:
            endchar = len(text)
        self.startchar = startchar
        self.endchar = endchar

        self.matched_terms = set()
        for t in matches:
            if hasattr(t, "text"):
                self.matched_terms.add(t.text)

    def __repr__(self):
        return "<Fragment %d:%d has %d matches>" % (
            self.startchar,
            self.endchar,
            len(self.matches),
        )

    def __len__(self):
        return self.endchar - self.startchar

    def overlaps(self, fragment):
        sc = self.startchar
        ec = self.endchar
        fsc = fragment.startchar
        fec = fragment.endchar
        return (sc < fsc < ec) or (sc < fec < ec)

    def overlapped_length(self, fragment):
        sc = self.startchar
        ec = self.endchar
        fsc = fragment.startchar
        fec = fragment.endchar
        return max(ec, fec) - min(sc, fsc)

    def __lt__(self, other):
        return self.startchar < other.startchar


def set_matched_filter(tokens, termset):
    """
    Mark tokens to be highlighted as matched.
    Phrase agnostic: highlights all matching tokens individually,
                     even if the terms are part of a phrase

    :param tokens: Result tokens to scan for matched terms to highlight
    :param termset: Query terms
    :return: yield each token with t.matched = True / False, indicating if the
             token should be highlighted
    """
    for t in tokens:
        t.matched = t.text in termset
        yield t


def set_matched_filter_phrases(tokens, text, terms, phrases):
    """
    Mark tokens to be highlighted as matched. Used for Strict Phrase highlighting.
    Phrase-aware: highlights only individual matches for individual query terms
                  and phrase matches for phrase terms.

    :param tokens:  Result tokens
    :param text:    Result text to scan for matched terms to highlight
    :param terms:   Individual query terms
    :param phrases: Query Phrases
    :return: yield each token with t.matched = True / False, indicating if the
             token should be highlighted
    """

    """
    Implementation note: Because the Token object follows a Singleton pattern,
    we can only read each one once. Because phrase matching requires rescanning,
    we require a rendered token list (the text parameter) instead. The function must
    still yield Token objects at the end, so the text list is used as a way to build a list
    of Token indices (the matches set). The yield loop at the end uses this
    to properly set .matched on the yielded Token objects.
    """
    text = text.split()
    matches = set()

    # Match phrases
    for phrase in phrases:
        i = 0
        n_phrase_words = len(phrase.words)
        slop = phrase.slop
        while i < len(text):
            if phrase.words[0] == text[i]:  # If first word matched
                if slop == 1:
                    # Simple substring match
                    if (
                        text[i + 1 : i + n_phrase_words] == phrase.words[1:]
                    ):  # If rest of phrase matches
                        any(
                            map(matches.add, range(i, i + n_phrase_words))
                        )  # Collect matching indices
                        # Advance past match area.
                        # Choosing to ignore possible overlapping matches for efficiency due to low probability.
                        i += n_phrase_words
                    else:
                        i += 1
                else:
                    # Slop match
                    current_word_index = first_slop_match = last_slop_match = i
                    slop_matches = [first_slop_match]
                    for word in phrase.words[1:]:
                        try:
                            """
                            Find the *last* occurrence of word in the slop substring by reversing it and mapping the index back.
                            If multiple tokens match in the substring, picking the first one can overlook valid matches.
                            For example, phrase is: 'one two three'~2
                            Target substring is:    'one two two six three', which is a valid match.
                                                     [0] [1] [2] [3] [4]

                            Looking for the first match will find [0], then [1] then fail since [3] is more than ~2 words away
                            Looking for the last match will find [0], then, given a choice between [1] or [2], will pick [2],
                            making [4] visible from there
                            """
                            text_sub = text[current_word_index + 1 : current_word_index + 1 + slop][
                                ::-1
                            ]  # Substring to scan (reversed)
                            len_sub = len(text_sub)
                            next_word_index = (
                                len_sub - text_sub.index(word) - 1
                            )  # Map index back to unreversed list
                            last_slop_match = current_word_index + next_word_index + 1
                            slop_matches.append(last_slop_match)
                            current_word_index = last_slop_match
                        except ValueError:
                            # word not found in substring
                            i += 1
                            break
                    else:
                        i = last_slop_match
                        any(map(matches.add, slop_matches))  # Collect matching indices
            else:
                i += 1

    # Match individual terms
    for i, word in enumerate(text):
        for term in terms:
            if term.text == word:
                matches.add(i)
                break

    for i, t in enumerate(tokens):
        t.matched = i in matches
        yield t


class Fragmenter:
    def must_retokenize(self):
        """Returns True if this fragmenter requires retokenized text.

        If this method returns True, the fragmenter's ``fragment_tokens``
        method  will be called with an iterator of ALL tokens from the text,
        with the tokens for matched terms having the ``matched`` attribute set
        to True.

        If this method returns False, the fragmenter's ``fragment_matches``
        method will be called with a LIST of matching tokens.
        """

        return True

    def fragment_tokens(self, text, all_tokens):
        """Yields :class:`Fragment` objects based on the tokenized text.

        :param text: the string being highlighted.
        :param all_tokens: an iterator of :class:`analysis.Token`
            objects from the string.
        """

        raise NotImplementedError

    def fragment_matches(self, text, matched_tokens):
        """Yields :class:`Fragment` objects based on the text and the matched
        terms.

        :param text: the string being highlighted.
        :param matched_tokens: a list of :class:`analysis.Token` objects
            representing the term matches in the string.
        """

        raise NotImplementedError


class WholeFragmenter(Fragmenter):
    """Doesn't fragment the token stream. This object just returns the entire
    entire stream as one "fragment". This is useful if you want to highlight
    the entire text.

    Note that even if you use the `WholeFragmenter`, the highlight code will
    return no fragment if no terms matched in the given field. To return the
    whole fragment even in that case, call `highlights()` with `minscore=0`::

        # Query where no terms match in the "text" field
        q = query.Term("tag", "new")

        r = mysearcher.search(q)
        r.fragmenter = highlight.WholeFragmenter()
        r.formatter = highlight.UppercaseFormatter()
        # Since no terms in the "text" field matched, we get no fragments back
        assert r[0].highlights("text") == ""

        # If we lower the minimum score to 0, we get a fragment even though it
        # has no matching terms
        assert r[0].highlights("text", minscore=0) == "This is the text field."

    """

    def __init__(self, charlimit=DEFAULT_CHARLIMIT):
        self.charlimit = charlimit

    def fragment_tokens(self, text, tokens):
        charlimit = self.charlimit
        matches = []
        for t in tokens:
            if charlimit and t.endchar > charlimit:
                break
            if t.matched:
                matches.append(t.copy())
        return [Fragment(text, matches)]


NullFragmeter = WholeFragmenter


class SentenceFragmenter(Fragmenter):
    """Breaks the text up on sentence end punctuation characters
    (".", "!", or "?"). This object works by looking in the original text for a
    sentence end as the next character after each token's 'endchar'.

    When highlighting with this fragmenter, you should use an analyzer that
    does NOT remove stop words, for example::

        sa = StandardAnalyzer(stoplist=None)
    """

    def __init__(self, maxchars=200, sentencechars=".!?", charlimit=DEFAULT_CHARLIMIT):
        """
        :param maxchars: The maximum number of characters allowed in a
            fragment.
        """

        self.maxchars = maxchars
        self.sentencechars = frozenset(sentencechars)
        self.charlimit = charlimit

    def fragment_tokens(self, text, tokens):
        maxchars = self.maxchars
        sentencechars = self.sentencechars
        charlimit = self.charlimit

        textlen = len(text)
        # startchar of first token in the current sentence
        first = None
        # Buffer for matched tokens in the current sentence
        tks = []
        endchar = None
        # Number of chars in the current sentence
        currentlen = 0

        for t in tokens:
            startchar = t.startchar
            endchar = t.endchar
            if charlimit and endchar > charlimit:
                break

            if first is None:
                # Remember the startchar of the first token in a sentence
                first = startchar
                currentlen = 0

            tlength = endchar - startchar
            currentlen += tlength

            if t.matched:
                tks.append(t.copy())

            # If the character after the current token is end-of-sentence
            # punctuation, finish the sentence and reset
            if endchar < textlen and text[endchar] in sentencechars:
                # Don't break for two periods in a row (e.g. ignore "...")
                if endchar + 1 < textlen and text[endchar + 1] in sentencechars:
                    continue

                # If the sentence had matches and it's not too long, yield it
                # as a token
                if tks and currentlen <= maxchars:
                    yield mkfrag(text, tks, startchar=first, endchar=endchar)
                # Reset the counts
                tks = []
                first = None
                currentlen = 0

        # If we get to the end of the text and there's still a sentence
        # in the buffer, yield it
        if tks:
            yield mkfrag(text, tks, startchar=first, endchar=endchar)


class ContextFragmenter(Fragmenter):
    """Looks for matched terms and aggregates them with their surrounding
    context.
    """

    def __init__(self, maxchars=200, surround=20, charlimit=DEFAULT_CHARLIMIT):
        """
        :param maxchars: The maximum number of characters allowed in a
            fragment.
        :param surround: The number of extra characters of context to add both
            before the first matched term and after the last matched term.
        """

        self.maxchars = maxchars
        self.surround = surround
        self.charlimit = charlimit

    def fragment_tokens(self, text, tokens):
        maxchars = self.maxchars
        surround = self.surround
        charlimit = self.charlimit

        # startchar of the first token in the fragment
        first = None
        # Stack of startchars
        firsts = deque()
        # Each time we see a matched token, we reset the countdown to finishing
        # the fragment. This also indicates whether we're currently inside a
        # fragment (< 0 not in fragment, >= 0 in fragment)
        countdown = -1
        # Tokens in current fragment
        tks = []
        endchar = None
        # Number of chars in the current fragment
        currentlen = 0

        for t in tokens:
            startchar = t.startchar
            endchar = t.endchar
            tlength = endchar - startchar
            if charlimit and endchar > charlimit:
                break

            if countdown < 0 and not t.matched:
                # We're not in a fragment currently, so just maintain the
                # "charsbefore" buffer
                firsts.append(startchar)
                while firsts and endchar - firsts[0] > surround:
                    firsts.popleft()
            elif currentlen + tlength > maxchars:
                # We're in a fragment, but adding this token would put us past
                # the maximum size. Zero the countdown so the code below will
                # cause the fragment to be emitted
                countdown = 0
            elif t.matched:
                # Start/restart the countdown
                countdown = surround
                # Remember the first char of this fragment
                if first is None:
                    if firsts:
                        first = firsts[0]
                    else:
                        first = startchar
                        # Add on unused front context
                        countdown += surround
                tks.append(t.copy())

            # If we're in a fragment...
            if countdown >= 0:
                # Update the counts
                currentlen += tlength
                countdown -= tlength

                # If the countdown is expired
                if countdown <= 0:
                    # Finish the fragment
                    yield mkfrag(text, tks, startchar=first, endchar=endchar)
                    # Reset the counts
                    tks = []
                    firsts = deque()
                    first = None
                    currentlen = 0

        # If there's a fragment left over at the end, yield it
        if tks:
            yield mkfrag(text, tks, startchar=first, endchar=endchar)


class PinpointFragmenter(Fragmenter):
    """This is a NON-RETOKENIZING fragmenter. It builds fragments from the
    positions of the matched terms.
    """

    def __init__(self, maxchars=200, surround=20, autotrim=False, charlimit=DEFAULT_CHARLIMIT):
        """
        :param maxchars: The maximum number of characters allowed in a
            fragment.
        :param surround: The number of extra characters of context to add both
            before the first matched term and after the last matched term.
        :param autotrim: automatically trims text before the first space and
            after the last space in the fragments, to try to avoid truncated
            words at the start and end. For short fragments or fragments with
            long runs between spaces this may give strange results.
        """

        self.maxchars = maxchars
        self.surround = surround
        self.autotrim = autotrim
        self.charlimit = charlimit

    def must_retokenize(self):
        return False

    def fragment_tokens(self, text, tokens):
        matched = [t for t in tokens if t.matched]
        return self.fragment_matches(text, matched)

    @staticmethod
    def _autotrim(fragment):
        text = fragment.text
        startchar = fragment.startchar
        endchar = fragment.endchar

        firstspace = text.find(" ", startchar, endchar)
        if firstspace > 0:
            startchar = firstspace + 1
        lastspace = text.rfind(" ", startchar, endchar)
        if lastspace > 0:
            endchar = lastspace

        if fragment.matches:
            startchar = min(startchar, fragment.matches[0].startchar)
            endchar = max(endchar, fragment.matches[-1].endchar)

        fragment.startchar = startchar
        fragment.endchar = endchar

    def fragment_matches(self, text, tokens):
        maxchars = self.maxchars
        surround = self.surround
        autotrim = self.autotrim
        charlimit = self.charlimit

        j = -1

        for i, t in enumerate(tokens):
            if j >= i:
                continue
            j = i
            left = t.startchar
            right = t.endchar
            if charlimit and right > charlimit:
                break

            currentlen = right - left
            while j < len(tokens) - 1 and currentlen < maxchars:
                next = tokens[j + 1]
                ec = next.endchar
                if ec - right <= surround and ec - left <= maxchars:
                    j += 1
                    right = ec
                    currentlen += ec - next.startchar
                else:
                    break

            left = max(0, left - surround)
            right = min(len(text), right + surround)
            fragment = Fragment(text, tokens[i : j + 1], left, right)
            if autotrim:
                self._autotrim(fragment)
            yield fragment


class FragmentScorer:
    pass


class BasicFragmentScorer(FragmentScorer):
    def __call__(self, f):
        # Add up the boosts for the matched terms in this passage
        score = sum(t.boost for t in f.matches)

        # Favor diversity: multiply score by the number of separate
        # terms matched
        score *= (len(f.matched_terms) * 100) or 1

        return score


def SCORE(fragment):
    "Sorts higher scored passages first."
    return 1


def FIRST(fragment):
    "Sorts passages from earlier in the document first."
    return fragment.startchar


def LONGER(fragment):
    "Sorts longer passages first."
    return 0 - len(fragment)


def SHORTER(fragment):
    "Sort shorter passages first."
    return len(fragment)


def get_text(original, token, replace):
    """Convenience function for getting the text to use for a match when
    formatting.

    If ``replace`` is False, returns the part of ``original`` between
    ``token.startchar`` and ``token.endchar``. If ``replace`` is True, returns
    ``token.text``.
    """

    if replace:
        return token.text
    else:
        return original[token.startchar : token.endchar]
