---
color_scheme: dark
title: "API Events"
nav_order: 8
parent: "Référence API"
lang: fr
---

# API Events

Système d'événements pour un couplage lâche entre les composants.

## EventBus

```python
class whoosh.event_bus.EventBus
```

Registre central des événements et subscribers.

### Méthodes

| Méthode | Description |
|---------|-------------|
| `bus.publish(event)` | Publie un événement |
| `bus.subscribe(fn)` | Abonne un handler |
| `bus.unsubscribe(fn)` | Désabonne un handler |
| `bus.clear()` | Supprime tous les abonnés |

**Exemple:**
```python
from whoosh.event_bus import EventBus

bus = EventBus()

@bus.subscribe
def on_index(event: DocumentIndexed):
    print(f"Indexé: {event.docnum}")

# Publier
bus.publish(DocumentIndexed(docnum=42))
```

## Événements intégrés

### DocumentIndexed

```python
class DocumentIndexed
    docnum: int           # Numéro de document
    schema: Schema        # Schéma utilisé
    timestamp: datetime   # Horodatage
    metadata: dict        # Métadonnées
```

### SearchExecuted

```python
class SearchExecuted
    query: str            # Requête originale
    result_count: int     # Nombre de résultats
    duration_ms: float    # Durée en ms
    user: str | None      # Utilisateur (si auth)
```

### IndexOptimized

```python
class IndexOptimized
    segments_before: int
    segments_after: int
    size_bytes: int
```

## Utilisation avec FastAPI

```python
from fastapi import FastAPI
from whoosh.event_bus import EventBus, DocumentIndexed

app = FastAPI()
bus = EventBus()

@app.on_event("startup")
def startup():
    bus.subscribe(on_index)

@app.post("/documents")
def add_document(doc: dict):
    # Indexation...
    bus.publish(DocumentIndexed(docnum=doc["id"]))
```

## Gestion d'erreurs

```python
@bus.subscribe
def on_error(event: SearchExecuted):
    if event.result_count == 0:
        logger.warning(f"Recherche vide: {event.query}")
```
