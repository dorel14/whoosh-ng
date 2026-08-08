---
title: 'Automata API'
sidebar_position: 0
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Automata API

Module for constructing and manipulating finite state automata (FSAs),
including NFAs, DFAs, finite state transducers (FSTs), Levenshtein
automata, and regular expression automata. Used internally for spelling
correction, fuzzy term queries, and term dictionary operations.

The automata module is a refactored package with submodules. All classes
and functions are importable directly from `whoosh.automata`.

## Module Functions

### `parse_glob`

```python
whoosh.automata.parse_glob(pattern, _glob_multi="*", _glob_single="?", _glob_range1="[", _glob_range2="]") -> NFA
```

Parses a glob-style pattern string and returns an NFA that matches strings
matching the pattern.

**Parameters:**
- `pattern`: Glob pattern string (`*` matches any sequence, `?` matches any
  single character).
- `_glob_multi`, `_glob_single`: Override the wildcard characters.
- `_glob_range1`, `_glob_range2`: Override the range syntax brackets.

### `glob_automaton`

```python
whoosh.automata.glob_automaton(pattern) -> NFA
```

Convenience function that parses a glob pattern and returns an NFA.

## FSA (Finite State Automaton) Classes

### `FSA`

```python
class whoosh.automata.FSA(initial)
```

Base class for finite state automata.

**Constructor:**
- `initial`: The initial state.

**Attributes:**
- `initial`: Initial state.
- `transitions`: Dict mapping source states to dicts mapping labels to
  target states.
- `final_states`: Set of accepting (final) states.

**Methods:**
- `__eq__(other)`: Compares initial state, final states, and transitions.
- `all_states()`: Returns a set of all states reachable in the automaton.
- `all_labels()`: Returns a set of all transition labels.
- `get_labels(src)`: Yields all labels leaving state `src`.
- `generate_all(state=None, sofar="")`: Yields all strings accepted by the
  automaton.
- `move(state, label)`: Returns the state reached by following `label` from
  `state`, or `None`.
- `moves(state, labels)`: Yields `(label, next_state)` pairs.
- `next(state)`: Yields target states reachable from `state` via any label.
- `is_final(state)`: Returns `True` if `state` is a final state.
- `start()`: Returns the initial state.
- `has_path_to(target)`: Returns `True` if there is a path to `target`.

### `Marker`

```python
class whoosh.automata.Marker(name)
```

Marker object used as a special transition label in NFAs (e.g., `ANY`,
`EPSILON`).

### `EPSILON`

```python
whoosh.automata.EPSILON = Marker("EPSILON")
```

Special marker representing an epsilon transition (no input consumed).

### `ANY`

```python
whoosh.automata.ANY = Marker("ANY")
```

Special marker representing a transition that matches any input character.

### `NFA`

```python
class whoosh.automata.NFA(initial)
```

Nondeterministic Finite Automaton. Extends `FSA` with epsilon transitions
and NFA-specific construction methods.

**Methods:**
- `add_transition(src, label, dst)`: Adds a transition from `src` to `dst`
  consuming `label`.
- `add_final_state(state, final=True)`: Marks `state` as a final/accepting
  state.
- `epsilon_closure(state)`: Returns the set of states reachable from `state`
  via epsilon transitions.
- `to_dfa()`: Converts this NFA to an equivalent DFA and returns it.

### `DFA`

```python
class whoosh.automata.DFA(initial)
```

Deterministic Finite Automaton. Extends `FSA` with DFA-specific operations.

**Methods:**
- `next_valid_string(string)`: Finds the lexicographically smallest string
  accepted by the DFA that is greater than or equal to `string`.
- `to_dfa()`: Returns self (already a DFA).

### `renumber_dfa`

```python
whoosh.automata.renumber_dfa(dfa, base=0) -> DFA
```

Renumerates the states of a DFA to integers starting at `base`.

### `u_to_utf8`

```python
whoosh.automata.u_to_utf8(dfa, base=0) -> DFA
```

Converts a Unicode DFA to a UTF-8 DFA.

### `find_all_matches`

```python
whoosh.automata.find_all_matches(dfa, lookup_func, first=unull)
```

Yields all strings accepted by the DFA, using `lookup_func` to determine
which strings exist in the dictionary.

**Parameters:**
- `dfa`: A deterministic finite automaton.
- `lookup_func`: Function called with each candidate string; returns the
  string if found in the dictionary.
- `first`: First string to start matching from (default `chr(0)`).

### `reverse_nfa`

```python
whoosh.automata.reverse_nfa(n) -> NFA
```

Returns the reverse of an NFA (reversed transitions, swapped initial
and final states).

### `product`

```python
whoosh.automata.product(dfa1, op, dfa2) -> DFA
```

Computes the product of two DFAs using a binary operation.

**Parameters:**
- `dfa1`, `dfa2`: Input DFAs.
- `op`: A function `(set1, set2) -> set` computing the output final states
  from the two input final state sets.

### `intersection`

```python
whoosh.automata.intersection(dfa1, dfa2) -> DFA
```

Returns the intersection of two DFAs.

### `union`

```python
whoosh.automata.union(dfa1, dfa2) -> DFA
```

Returns the union of two DFAs.

### `epsilon_nfa`

```python
whoosh.automata.epsilon_nfa() -> NFA
```

Returns an NFA that accepts only the empty string.

### `dot_nfa`

```python
whoosh.automata.dot_nfa() -> NFA
```

Returns an NFA that accepts any single character.

### `basic_nfa`

```python
whoosh.automata.basic_nfa(label) -> NFA
```

Returns an NFA that accepts exactly the string `label`.

### `charset_nfa`

```python
whoosh.automata.charset_nfa(labels) -> NFA
```

Returns an NFA that accepts any single character in `labels`.

### `string_nfa`

```python
whoosh.automata.string_nfa(string) -> NFA
```

Returns an NFA that accepts exactly `string`.

### `choice_nfa`

```python
whoosh.automata.choice_nfa(n1, n2) -> NFA
```

Returns an NFA that accepts strings accepted by either `n1` or `n2`.

### `concat_nfa`

```python
whoosh.automata.concat_nfa(n1, n2) -> NFA
```

Returns an NFA that accepts the concatenation of `n1` and `n2`.

### `star_nfa`

```python
whoosh.automata.star_nfa(n) -> NFA
```

Returns an NFA that accepts zero or more repetitions of `n`.

### `plus_nfa`

```python
whoosh.automata.plus_nfa(n) -> NFA
```

Returns an NFA that accepts one or more repetitions of `n`.

### `optional_nfa`

```python
whoosh.automata.optional_nfa(n) -> NFA
```

Returns an NFA that accepts zero or one occurrence of `n`.

### `strings_dfa`

```python
whoosh.automata.strings_dfa(strings) -> DFA
```

Constructs a minimal DFA that accepts exactly the given strings.

### `add_suffix`

```python
whoosh.automata.add_suffix(dfa, nodes, last, downto, seen)
```

Internal function for adding suffixes to a trie during DFA construction.

## Levenshtein Automata

### `levenshtein_automaton`

```python
whoosh.automata.levenshtein_automaton(term, k, prefix=0) -> NFA
```

Constructs an NFA that matches all strings within edit distance `k` of
`term`. This is the core function for fuzzy term queries and spelling
suggestions.

**Parameters:**
- `term`: The reference string to compute edit distance from.
- `k`: Maximum edit distance (number of insertions, deletions, or
  substitutions).
- `prefix`: If positive, require matched strings to share this length of
  prefix with `term` (speeds up matching significantly).

**Returns:** An NFA that can be converted to a DFA via `.to_dfa()`.

```python
from whoosh.automata import levenshtein_automaton

nfa = levenshtein_automaton("hello", k=1, prefix=0)
dfa = nfa.to_dfa()
```

## RegEx

### `parse`

```python
whoosh.automata.parse(pattern) -> NFA
```

Parses a regular expression pattern string and returns an NFA.

**Parameters:**
- `pattern`: A regex pattern string (Python `re`-style syntax).

### `RegexBuilder`

```python
class whoosh.automata.RegexBuilder(pattern)
```

Helper class for building NFAs from regex patterns.

## FST (Finite State Transducer) Classes

### `Values`

```python
class whoosh.automata.Values
```

Abstract base class for value types stored in FST arcs.

### `IntValues`

```python
class whoosh.automata.IntValues
```

Stores integer values in FST arcs.

### `SequenceValues`

```python
class whoosh.automata.SequenceValues
```

Base class for value types that store sequences of values.

### `BytesValues`

```python
class whoosh.automata.BytesValues
```

Stores byte string values in FST arcs.

### `ArrayValues`

```python
class whoosh.automata.ArrayValues
```

Stores arrays of values in FST arcs.

### `IntListValues`

```python
class whoosh.automata.IntListValues
```

Stores lists of integers in FST arcs.

### `Node`

```python
class whoosh.automata.Node
```

Base class for nodes in an FST.

### `ComboNode`

```python
class whoosh.automata.ComboNode
```

Base class for nodes that combine multiple sub-nodes (intersection, union).

### `UnionNode`

```python
class whoosh.automata.UnionNode
```

A node that represents the union of multiple sub-nodes.

### `IntersectionNode`

```python
class whoosh.automata.IntersectionNode
```

A node that represents the intersection of multiple sub-nodes.

### `BaseCursor`

```python
class whoosh.automata.BaseCursor
```

Base class for cursors that iterate over FST contents.

### `Cursor`

```python
class whoosh.automata.Cursor
```

Concrete cursor for iterating over an FST, supporting `next()`, `find()`,
`text()`, and other navigation methods.

### `UncompiledNode`

```python
class whoosh.automata.UncompiledNode
```

Represents an FST node that has not yet been compiled into a binary
representation. Used during FST construction.

### `Arc`

```python
class whoosh.automata.Arc
```

Represents a single arc in an FST, with a label, target node, and associated
value.

### `GraphWriter`

```python
class whoosh.automata.GraphWriter
```

Writes an FST to a binary file on disk or to an in-memory buffer.

### `BaseGraphReader`

```python
class whoosh.automata.BaseGraphReader
```

Base class for reading FSTs from disk.

### `GraphReader`

```python
class whoosh.automata.GraphReader
```

Concrete reader for FSTs stored on disk. Supports `find()`, `next()`, and
`text()` for navigating the graph.

### `to_labels`

```python
whoosh.automata.to_labels(key)
```

Converts a key (string, int, etc.) into a list of FST arc labels.

### `within`

```python
whoosh.automata.within(graph, text, k=1, prefix=0, address=None)
```

Uses a pre-built FST and a Levenshtein automaton to find all keys in the
graph within edit distance `k` of `text`.

**Parameters:**
- `graph`: A `GraphReader` instance.
- `text`: The search term.
- `k`: Maximum edit distance.
- `prefix`: Required shared prefix length.
- `address`: Optional starting address in the graph.

### `dump_graph`

```python
whoosh.automata.dump_graph(graph, address=None, tab=0, out=None)
```

Debug utility that prints the structure of an FST to stdout or a file.

### `FileVersionError`

```python
class whoosh.automata.FileVersionError
```

Raised when reading an FST file with an incompatible version.

### `InactiveCursor`

```python
class whoosh.automata.InactiveCursor
```

Raised when operating on a cursor that is not at a valid position.
