---
title: "Introduction to Whoosh"
sidebar_position: 2
Module: whoosh
Version: 2.7.4
---
> **Note de traduction** : Cette page n'est pas encore traduite en francais.
> Le contenu anglais est affiche ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Introduction to Whoosh

## About Whoosh

Whoosh was created by Matt Chaput. It started as a quick and dirty search
server for the online documentation of the Houdini 3D animation software
package. Side Effects Software generously allowed Matt to open source the code
in case it might be useful to anyone else who needs a very flexible or
pure-Python search engine (or both!).

- Whoosh is fast, but uses only pure Python, so it will run anywhere Python
  runs, without requiring a compiler.
- By default, Whoosh uses the [Okapi BM25F](https://en.wikipedia.org/wiki/Okapi_BM25)
  ranking function, but like most things the ranking function can be easily
  customized.
- Whoosh creates fairly small indexes compared to many other search libraries.
- All indexed text in Whoosh must be **unicode**.
- Whoosh lets you store arbitrary Python objects with indexed documents.

## What is Whoosh?

Whoosh is a fast, pure Python search engine library.

The primary design impetus of Whoosh is that it is pure Python. You should be
able to use Whoosh anywhere you can use Python, no compiler or Java required.

Like one of its ancestors, Lucene, Whoosh is not really a search engine, it's a
programmer library for creating a search engine.

Practically no important behavior of Whoosh is hard-coded. Indexing of text, the
level of information stored for each term in each field, parsing of search
queries, the types of queries allowed, scoring algorithms, etc. are all
customizable, replaceable, and extensible.

## What can Whoosh do for you?

Whoosh lets you index free-form or structured text and then quickly find
matching documents based on simple or complex search criteria.

## Whoosh-NG

Whoosh-NG is the maintained evolution of Whoosh. It preserves the pure-Python
core described above while adding optional, opt-in extensions (vector search,
a plugin system, a middleware pipeline, linguistics, and pluggable storage).
Classic features documented in this section remain backwards-compatible with
Whoosh 1.x/2.x.

## Getting help with Whoosh

You can view outstanding issues on the
[Whoosh-NG GitHub page](https://github.com/dorel14/whoosh-ng) and get help by
opening an issue or discussion there.

