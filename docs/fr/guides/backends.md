---
title: "Backends"
nav_order: 28
parent: "Guides"
lang: fr
---

# Backends

Whoosh-NG supporte des backends de stockage pluggables via l'architecture Provider. Le backend par défaut stocke les données comme fichiers sur disque, mais vous pouvez utiliser SQLite, PostgreSQL, S3, et plus encore.

## Backends intégrés

| Backend | Description |
|---------|-------------|
| Fichier (défaut) | Stocke l'index comme fichiers sur disque |
| SQLite | Stocke l'index dans une base SQLite |
| Mémoire | Backend en mémoire (tests uniquement) |

## Backend Fichier (défaut)

```python
from whoosh.index import create_in

# Utilise FileBackend par défaut
ix = create_in("indexdir", schema)
```

## Backend SQLite

```python
from whoosh.backends.sqlite import SQLiteBackend
from whoosh.store.sqlite import SQLiteStorage

storage = SQLiteStorage("index.db")
backend = SQLiteBackend(storage=storage)
```

### Avantages

- Index en un seul fichier
- Meilleur pour les charges transactionnelles
- Sauvegardes plus faciles
- Supporte les lectures concurrentes

## Backend Mémoire

```python
from whoosh.backends.memory import MemoryBackend

backend = MemoryBackend()  # Utile pour les tests
```

## Bonnes pratiques

1. **File backend pour production**: Le plus éprouvé
2. **SQLite pour déploiement mono-fichier**: Plus facile à déployer
3. **Mémoire pour les tests**: Rapide, pas de nettoyage nécessaire
4. **Fichiers composés**: Activez pour réduire le nombre de fichiers
5. **Stratégie de sauvegarde**: File = copier le répertoire; SQLite = copier le fichier