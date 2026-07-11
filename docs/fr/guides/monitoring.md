---
title: "Monitoring"
nav_order: 31
parent: "Guides"
lang: fr
---

# Monitoring

Whoosh-NG inclut des hooks d'observabilité intégrés et un plugin Prometheus pour le monitoring en production.

## Métriques intégrées

### MetricsMiddleware

```python
from whoosh.middleware import MetricsMiddleware, MiddlewareChain
from whoosh.middleware.integration import apply_middleware_to_writer, apply_middleware_to_searcher

chain = MiddlewareChain([MetricsMiddleware()])

writer = apply_middleware_to_writer(ix.writer(), chain.middlewares)
searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)

# Obtenir les métriques
metrics = chain.get_metrics()
```

## Plugin Prometheus

### Installation

```bash
pip install whoosh-ng[metrics]
```

### Métriques exposées

| Métrique | Type | Description |
|----------|------|-------------|
| `whoosh_documents_indexed_total` | Counter | Total documents indexés |
| `whoosh_searches_executed_total` | Counter | Total recherches exécutées |
| `whoosh_indexing_duration_seconds` | Histogram | Temps d'indexation |
| `whoosh_search_duration_seconds` | Histogram | Temps de recherche |
| `whoosh_index_size_bytes` | Gauge | Taille actuelle de l'index |
| `whoosh_cache_hits_total` | Counter | Cache hits |
| `whoosh_cache_misses_total` | Counter | Cache misses |

## Event Bus pour monitoring

```python
from whoosh.event_bus import EventBus, DocumentIndexed, SearchExecuted

bus = EventBus()

@bus.subscribe
def on_indexed(event: DocumentIndexed):
    stats.increment("documents.indexed")

@bus.subscribe
def on_searched(event: SearchExecuted):
    stats.timing("search.duration", event.duration)
```

## Bonnes pratiques

1. **Ajoutez MetricsMiddleware tôt**: Incluez-le dans votre chaîne de base
2. **Exportez via Prometheus**: En production, exposez l'endpoint `/metrics`
3. **Endpoint health**: Utilisez `/health` pour les health checks load balancer
4. **Logging structuré**: Corrélez les événements search/index avec des request IDs
5. **Alerting**: Définissez des alertes sur les taux d'erreur et les latences
