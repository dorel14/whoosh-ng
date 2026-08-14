---
title: "Embeddings"
sidebar_position: 70
---

# Embeddings

Whoosh-NG peut embarquer des documents dans des vecteurs denses et les utiliser
pour la recherche sémantique. Cette page couvre la stack embeddings complète :
**FastEmbedProvider** (backend CPU par défaut), **ONNXEmbeddingProvider**
(backend CPU avancé), **EmbeddingModelRegistry**, **EmbeddingModelManager**,
le CLI `whoosh-ng-models` et `EmbeddingEngine` pour l'intégration
`ConfigEngine`.

> **Module :** `whoosh_modern.embeddings`
> **Version :** 3.0.0

## Installation

```bash
# Backend CPU par défaut (FastEmbed)
pip install whoosh-ng[embeddings]

# Backend CPU avancé (ONNX Runtime)
pip install whoosh-ng[embeddings-onnx]

# Backend sentence-transformers
pip install whoosh-ng[embeddings-sentence-transformers]

# Stack complète avec recherche vectorielle
pip install whoosh-ng[embeddings,vector]
```

## Démarrage rapide

```python
from whoosh_modern.embeddings import FastEmbedProvider

provider = FastEmbedProvider()
vector = provider.embed("bonjour le monde")
print(len(vector))  # 384

batch = provider.embed_batch(["bonjour", "le monde"])
print(len(batch))   # 2
```

## Providers

### FastEmbedProvider (défaut)

`FastEmbedProvider` est le backend CPU par défaut. Il encapsule
`fastembed.TextEmbedding`, qui télécharge et cache les modèles
automatiquement.

```python
from whoosh_modern.embeddings import FastEmbedProvider

provider = FastEmbedProvider()
# Ou avec un modèle personnalisé :
provider = FastEmbedProvider(model_name="BAAI/bge-base-en-v1.5")
```

- Zéro dépendance PyTorch.
- CPU-only.
- Téléchargement automatique et cache des modèles.
- Conforme au protocole `EmbeddingProvider`.

### ONNXEmbeddingProvider (avancé)

`ONNXEmbeddingProvider` encapsule un modèle ONNX et un tokenizer HuggingFace
`tokenizers`. Il gère la tokenization, l'inférence, le pooling et la
normalisation L2 optionnelle.

```python
from whoosh_modern.embeddings import ONNXEmbeddingProvider

provider = ONNXEmbeddingProvider(
    model_path="models/multilingual-e5-small/model.onnx",
    tokenizer_dir="models/multilingual-e5-small",
)
```

#### Arguments du constructeur

| Argument | Type | Défaut | Description |
|----------|------|---------|-------------|
| `model_path` | `str` | requis | Chemin vers le fichier `.onnx` |
| `tokenizer_dir` | `str \| None` | parent de `model_path` | Répertoire contenant `tokenizer.json` |
| `pooling` | `str` | `"mean"` | Au choix `"mean"`, `"cls"`, `"max"` |
| `normalize` | `bool` | `True` | Normalisation L2 des vecteurs de sortie |
| `dimension` | `int \| None` | `None` | Dimension attendue des embeddings (inférée depuis le modèle si omise) |
| `enable_prefix` | `bool` | `True` | Ajoute le préfixe de tâche E5 `"passage: "` / `"query: "` |

#### Stratégies de pooling

| Stratégie | Description |
|-----------|-------------|
| `mean` | Moyenne des embeddings de tous les tokens réels (aware masque) |
| `cls` | Embedding du premier token |
| `max` | Maximum élément par élément sur les tokens réels |

#### Préfixes de tâche E5

Quand `enable_prefix=True`, `embed()` préfixe par `"passage: "` et
`embed_batch(..., is_query=True)` préfixe par `"query: "`. Mettez
`enable_prefix=False` quand le modèle n'attend pas de préfixe.

## Model manager et registry

### EmbeddingModelRegistry

`EmbeddingModelRegistry` stocke les métadonnées `ModelInfo` des modèles ONNX
connus.

```python
from whoosh_modern.embeddings import get_default_registry

registry = get_default_registry()
info = registry.resolve("multilingual-e5-small")
print(info.dimension)   # 384
print(info.pooling)     # mean
print(info.normalize)   # True
```

Modèles pré-enregistrés :

| Nom | Dimension | Pooling | Description |
|-----|-----------|---------|-------------|
| `bge-small-en-v1.5` | 384 | mean | BGE-small anglais |
| `multilingual-e5-small` | 384 | mean | E5-small multilingue |
| `mini-lm-en-ONNX` | 384 | cls | MiniLM anglais |
| `bge-small-en-v1.5-int8` | 384 | mean | BGE-small quantifié INT8 |

### EmbeddingModelManager

`EmbeddingModelManager` télécharge et met en cache les modèles ONNX localement
sous `~/.whoosh-ng/models/` (remplacer par `WHOOSH_NG_MODELS_DIR`).

```python
from whoosh_modern.embeddings import EmbeddingModelManager

manager = EmbeddingModelManager()

# Télécharger un modèle depuis HuggingFace
model_dir = manager.download("multilingual-e5-small")

# Vérifier la présence
print(manager.is_installed("multilingual-e5-small"))  # True

# Lister les modèles installés
print(manager.list_installed())

# Vérifier le checksum
print(manager.verify_checksum("multilingual-e5-small", "hexsha256..."))

# Supprimer
manager.remove("multilingual-e5-small")
```

## CLI

Un script console `whoosh-ng-models` est installé avec l'extra
`embeddings-onnx` :

```bash
whoosh-ng-models list
whoosh-ng-models list --all
whoosh-ng-models info multilingual-e5-small
whoosh-ng-models install multilingual-e5-small
whoosh-ng-models verify multilingual-e5-small --expected-sha256 <hex>
whoosh-ng-models remove multilingual-e5-small
whoosh-ng-models update multilingual-e5-small
```

Utilisez `--models-dir` pour remplacer le répertoire de modèles par défaut.

Utilisez `--hf-token` pour vous authentifier auprès du Hub HuggingFace. Il se
rabat sur les variables d'environnement `HF_TOKEN` /
`HUGGING_FACE_HUB_TOKEN`. Les modèles publics fonctionnent sans token, mais
les requêtes authentifiées bénéficient de limites de débit plus élevées et de
téléchargements plus rapides.

## Intégration ConfigEngine

`EmbeddingEngine` (`whoosh_modern.config.engines.embedding.EmbeddingEngine`) lit le bloc
`embedding` depuis `WhooshNGConfig` et instancie le provider correspondant.

```yaml
# whoosh-ng.yml
embedding:
  provider: fastembed
  model: BAAI/bge-small-en-v1.5
```

```yaml
# Ou avec ONNX
embedding:
  provider: onnx
  model: multilingual-e5-small
  model_path: models/multilingual-e5-small/model.onnx
  tokenizer_dir: models/multilingual-e5-small
  pooling: mean
  normalize: true
```

```yaml
# Ou avec sentence-transformers
embedding:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2
```

```yaml
# Vectorisation multi-champs
embedding:
  provider: fastembed
  model: BAAI/bge-small-en-v1.5
  source_field: body
  target_field: body_vector
  embedding_fields:
    - source_field: title
      target_field: title_vector
    - source_field: body
      target_field: body_vector
```

Providers supportés : `fastembed`, `onnx`, `sentence-transformers`.

Lorsque `embedding_fields` est fourni, les valeurs par défaut `source_field` / `target_field` sont ignorées et chaque mapping est traité indépendamment. `SearchView` injecte automatiquement les champs cibles en tant que champs `VECTOR` dans le schéma Whoosh généré s'ils ne sont pas déjà déclarés.

**Note sur la configuration ONNX :**
Lorsque vous utilisez `provider: onnx`, vous pouvez spécifier un modèle enregistré via `model` ou fournir des chemins de fichiers explicites via `model_path` et `tokenizer_dir`.
Si `model` est spécifié, l'`EmbeddingModelManager` tentera de télécharger et gérer le modèle, dérivant automatiquement `model_path` et `tokenizer_dir` depuis le cache local.
Si `model_path` et/ou `tokenizer_dir` sont fournis explicitement, ils prendront le pas sur les chemins dérivés du nom du `model`.
Il est recommandé d'utiliser soit `model` pour les modèles gérés par le manager, soit `model_path` / `tokenizer_dir` pour des chemins locaux personnalisés, afin d'éviter toute ambiguïté.

## Protocole

Tout objet implémentant `embed(text: str) -> Sequence[float]` satisfait le
protocole `EmbeddingProvider` (`whoosh_modern.embeddings.protocol`).

```python
from whoosh_modern.embeddings.protocol import EmbeddingProvider

class MonProvider:
    def embed(self, text: str) -> list[float]: ...
```

## Exemples

- [Embeddings avec FastEmbed](/examples/embeddings-fastembed) — Exemple FastEmbed exécutable
- [Embeddings avec ONNX](/examples/embeddings-onnx) — Exemple ONNX exécutable

## Voir aussi

- [Recherche vectorielle](/modern/vector) — Utiliser les embeddings pour la recherche sémantique
- [Fournisseurs de stockage](/modern/storage-providers) — Persister les index vectoriels
- [Moteur de configuration](/modern/configuration-engine) — Surface de configuration typée
