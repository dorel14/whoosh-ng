---
title: 'Auto-Indexing'
sidebar_position: 27
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Auto-Indexing

Whoosh-NG provides utilities for automatic schema discovery and data-source driven indexing.

## Schema Discovery

The `SchemaDiscovery` utility inspects a data source and auto-generates a Whoosh schema:

```python
from whoosh_modern.discovery import SchemaDiscovery

discovery = SchemaDiscovery(source=data_source)
schema = discovery.discover()
```

See [SearchView](/examples/search-view) and [Data Sources](/examples/data-sources) for usage examples.
