---
title: "Field Caches"
sidebar_position: 16
Module: whoosh.filedb.fieldcache
Version: 2.7.4
---
> **Note de traduction** : Cette page n'est pas encore traduite en francais.
> Le contenu anglais est affiche ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Field caches

The default (`filedb`) backend uses *field caches* in certain circumstances.
The field cache basically pre-computes the order of documents in the index to
speed up sorting and faceting.

Generating field caches can take time the first time you sort/facet on a large
index. The field cache is kept in memory (and by default written to disk when
it is generated) so subsequent sorted/faceted searches should be faster.

The default caching policy never expires field caches, so reused searchers
and/or sorting a lot of different fields could use up quite a bit of memory
with large indexes.

## Customizing cache behaviour

(By default, Whoosh saves field caches to disk. To prevent a reader or
searcher from writing out field caches, do this before you start using it:)

```python
searcher.set_caching_policy(save=False)
```

By default, if caches are written to disk they are saved in the index
directory. To tell a reader or searcher to save cache files to a different
location, create a storage object and pass it to the `storage` keyword
argument:

```python
from whoosh.filedb.filestore import FileStorage

mystorage = FileStorage("path/to/cachedir")
reader.set_caching_policy(storage=mystorage)
```

## Creating a custom caching policy

Expert users who want to implement a custom caching policy (for example, to add
cache expiration) should subclass `whoosh.filedb.fieldcache.FieldCachingPolicy`.
Then you can pass an instance of your policy object to the `set_caching_policy`
method:

```python
searcher.set_caching_policy(MyPolicy())
```

## See also

- [Sorting](/core/sorting) â€” Facets and sort keys
- [API: sorting](../api/sorting) â€” Sorting and faceting reference

