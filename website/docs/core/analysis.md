---
title: "About Analyzers"
sidebar_position: 6
Module: whoosh.analysis
Version: 2.7.4
---

:::info
Following the rename of `whoosh-reloaded` to `whoosh-ng`, new Whoosh-NG specific modules are typically found under `whoosh_modern`.
Core Whoosh components (like `whoosh.analysis`, `whoosh.index`) remain accessible directly under the `whoosh` namespace for backward compatibility.
:::

# About analyzers

## Overview

An analyzer is a function or callable class (a class with a `__call__` method)
that takes a unicode string and returns a generator of tokens. Usually a
"token" is a word, for example the string "Mary had a little lamb" might yield
the tokens "Mary", "had", "a", "little", and "lamb". However, tokens do not
necessarily correspond to words. For example, you might tokenize Chinese text
into individual characters or bi-grams. Tokens are the units of indexing, that
is, they are what you are able to look up in the index.

An analyzer is basically just a wrapper for a tokenizer and zero or more
filters. The analyzer's `__call__` method will pass its parameters to a
tokenizer, and the tokenizer will usually be wrapped in a few filters.

A tokenizer is a callable that takes a unicode string and yields a series of
`analysis.Token` objects.

For example, the provided `whoosh.analysis.RegexTokenizer` class implements a
customizable, regular-expression-based tokenizer that extracts words and
ignores whitespace and punctuation:

```python
from whoosh.analysis import RegexTokenizer

tokenizer = RegexTokenizer()
for token in tokenizer("Hello there my friend!"):
    print(repr(token.text))
# u'Hello'
# u'there'
# u'my'
# u'friend'
```

A filter is a callable that takes a generator of Tokens (either a tokenizer or
another filter) and in turn yields a series of Tokens.

For example, the provided `whoosh.analysis.LowercaseFilter()` filters tokens by
converting their text to lowercase. The implementation is very simple:

```python
def LowercaseFilter(tokens):
    """Uses lower() to lowercase token text."""
    for t in tokens:
        t.text = t.text.lower()
        yield t
```

You can wrap the filter around a tokenizer to see it in operation:

```python
from whoosh.analysis import LowercaseFilter, RegexTokenizer

tokenizer = RegexTokenizer()
for token in LowercaseFilter(tokenizer("These ARE the things I want!")):
    print(repr(token.text))
# u'these'
# u'are'
# u'the'
# u'things'
# u'i'
# u'want'
```

An analyzer is just a means of combining a tokenizer and some filters into a
single package.

You can implement an analyzer as a custom class or function, or compose
tokenizers and filters together using the `|` character:

```python
my_analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()
```

The first item must be a tokenizer and the rest must be filters (you can't put
a filter first or a tokenizer after the first item). Note that this only works
if at least the tokenizer is a subclass of `whoosh.analysis.Composable`, as all
the tokenizers and filters that ship with Whoosh are.

## Using analyzers

When you create a field in a schema, you can specify your analyzer as a keyword
argument to the field object:

```python
schema = Schema(content=TEXT(analyzer=StemmingAnalyzer()))
```

## Advanced analysis

### Token objects

The `Token` class has no methods. It is merely a place to record certain
attributes. A `Token` object actually has two kinds of attributes: *settings*
that record what kind of information the `Token` object does or should contain,
and *information* about the current token.

#### Token setting attributes

A `Token` object should always have the following attributes. A tokenizer or
filter can check these attributes to see what kind of information is available
and/or what kind of information they should be setting on the `Token` object.
Filters **should not** change the values of these attributes.

| Type | Attribute name | Description | Default |
|------|----------------|-------------|---------|
| str | mode | The mode in which the analyzer is being called, e.g. `'index'` during indexing or `'query'` during query parsing | `''` |
| bool | positions | Whether term positions are recorded in the token | `False` |
| bool | chars | Whether term start and end character indices are recorded in the token | `False` |
| bool | boosts | Whether per-term boosts are recorded in the token | `False` |
| bool | removestops | Whether stop-words should be removed from the token stream | `True` |

#### Token information attributes

A `Token` object may have any of the following attributes. The `text` attribute
should always be present. The `original` attribute may be set by a tokenizer.
All other attributes should only be accessed or set based on the values of the
"settings" attributes above.

| Type | Name | Description |
|------|------|-------------|
| unicode | text | The text of the token (this should always be present) |
| unicode | original | The original (pre-filtered) text of the token |
| int | pos | The position of the token in the stream, starting at 0 (only set if positions is True) |
| int | startchar | The character index of the start of the token in the original string (only set if chars is True) |
| int | endchar | The character index of the end of the token in the original string (only set if chars is True) |
| float | boost | The boost for this token (only set if boosts is True) |
| bool | stopped | Whether this token is a "stop" word (only set if removestops is False) |

### Performing different analysis for indexing and query parsing

Whoosh sets the `mode` setting attribute to indicate whether the analyzer is
being called by the indexer (`mode='index'`) or the query parser
(`mode='query'`). This is useful if there's a transformation that you only want
to apply at indexing or query parsing:

```python
class MyFilter(Filter):
    def __call__(self, tokens):
        for t in tokens:
            if t.mode == 'query':
                ...
            else:
                ...
```

The `whoosh.analysis.MultiFilter` filter class lets you specify different
filters to use based on the mode setting:

```python
intraword = MultiFilter(
    index=IntraWordFilter(mergewords=True, mergenums=True),
    query=IntraWordFilter(mergewords=False, mergenums=False),
)
```

### Stop words

"Stop" words are words that are so common it's often counter-productive to
index them, such as "and", "or", "if", etc. The provided `analysis.StopFilter`
lets you filter out stop words, and includes a default list of common stop
words.

```python
from whoosh.analysis import StopFilter

stopper = StopFilter()
for token in stopper(LowercaseFilter(tokenizer("These ARE the things I want!"))):
    print(repr(token.text))
# u'these'
# u'things'
# u'want'
```

#### Renumbering term positions

Remember that analyzers are sometimes asked to record the position of each
token in the token stream. So what happens to the `pos` attribute of the
tokens if `StopFilter` removes the words `had` and `a` from the stream? Should
it renumber the positions to pretend the "stopped" words never existed? Or
should it preserve the original positions of the words?

It turns out that different situations call for different solutions, so the
provided `StopFilter` class supports both of the above behaviors. Renumbering
is the default, since that is usually the most useful and is necessary to
support phrase searching. However, you can set a parameter in StopFilter's
constructor to tell it not to renumber positions:

```python
stopper = StopFilter(renumber=False)
```

#### Removing or leaving stop words

The point of using `StopFilter` is to remove stop words, right? Well, there are
actually some situations where you might want to mark tokens as "stopped" but
not remove them from the token stream.

The `removestops` parameter passed to the analyzer's `__call__` method (and
copied to the `Token` object as an attribute) specifies whether stop words
should be removed from the stream or left in.

```python
from whoosh.analysis import StandardAnalyzer

analyzer = StandardAnalyzer()
print([(t.text, t.stopped) for t in analyzer("This is a test")])
# [(u'test', False)]

print([(t.text, t.stopped) for t in analyzer("This is a test", removestops=False)])
# [(u'this', True), (u'is', True), (u'a', True), (u'test', False)]
```

The `analysis.unstopped()` filter function takes a token generator and yields
only the tokens whose `stopped` attribute is `False`.

> Even if you leave stopped words in the stream in an analyzer you use for
> indexing, the indexer will ignore any tokens where the `stopped` attribute is
> `True`.

### Implementation notes

Because object creation is slow in Python, the stock tokenizers do not create a
new `analysis.Token` object for each token. Instead, they create one `Token`
object and yield it over and over. This is a nice performance shortcut but can
lead to strange behavior if your code tries to remember tokens between loops of
the generator.

```python
# WRONG: the generator reuses the same Token object
print(list(tokenizer("Hello there my friend")))
# [Token(u"friend"), Token(u"friend"), Token(u"friend"), Token(u"friend")]

# RIGHT: save the attributes, not the token object
print([t.text for t in tokenizer("Hello there my friend")])
# [u'Hello', u'there', u'my', u'friend']
```

If you implement your own tokenizer, filter, or analyzer as a class, you should
implement an `__eq__` method. This is important to allow comparison of `Schema`
objects.

## See also

- [Stemming & Stop Words](/core/stemming) — Practical stemming and stop-word guides
- [N-grams](/core/ngrams) — Substring and prefix matching with N-gram analyzers
- [API: analysis](../api/analysis) — Full reference for analyzers, tokenizers, and filters
