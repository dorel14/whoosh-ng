---
title: "Embeddings"
sidebar_position: 70
---

# Embeddings

Whoosh-NG peut embarquer des documents dans des vecteurs denses et les utiliser
pour la recherche sémantique. Cette page couvre la stack embeddings complète :
**LibEmbeddingProvider** (backend CPU par défaut), **FastEmbedProvider**,
**ONNXEmbeddingProvider** (backend CPU avancé), **EmbeddingModelRegistry**,
**EmbeddingModelManager**, le CLI `whoosh-ng-models` et `EmbeddingEngine` pour
l'intégration `ConfigEngine`.

> **Module :** `whoosh_modern.embeddings`
> **Version :** 4.0.0

## Installation

```bash
# Backend CPU par défaut (libembedding-ng)
pip install whoosh-ng[libembedding]

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
from whoosh_modern.embeddings import LibEmbeddingProvider

provider = LibEmbeddingProvider()
vector = provider.embed("hello world")
print(len(vector))  # 384

batch = provider.embed_batch(["hello", "world"])
print(len(batch))   # 2
```

## Providers

### FastEmbedProvider

`FastEmbedProvider` est un backend CPU. Il encapsule
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

### LibEmbeddingProvider (défaut)

`LibEmbeddingProvider` est le nouveau backend CPU par défaut. Il encapsule
`libembedding.TextEmbedding`, qui télécharge et cache les modèles automatiquement.
Il est CPU-only, nécessite zéro PyTorch, et est plus rapide que FastEmbed.

```python
from whoosh_modern.embeddings import LibEmbeddingProvider

provider = LibEmbeddingProvider()
# Ou avec un preset :
provider = LibEmbeddingProvider(model_name="fast")
# Ou avec une quantification explicite :
provider = LibEmbeddingProvider(model_name="balanced", quantization="auto")
```

Prises en charge des presets :
- `"fast"` → modèle le plus rapide auto-sélectionné (dimension 384 préférée, taille minimale, score de vitesse CPU le plus élevé)
- `"balanced"` → vitesse/qualité équilibrée (défaut)
- `"quality"` → modèle de plus haute qualité

Ou utiliser un identifiant de modèle direct (ex: `"BAAI/bge-small-en-v1.5"`).

Arguments du constructeur :
- `model_name`: preset ou identifiant HF (défaut: `"balanced"`)
- `pooling`: `"mean"` ou `"cls"` (défaut: `"mean"`)
- `batch_size`: taille de lot d'inférence optionnelle
- `cache_size`: taille de cache LRU optionnelle (0 = désactivé)
- `quantization`: mode de quantification optionnel (`"none"`, `"static"`, `"dynamic"`, `"fp16"`, `"auto"`)

- Zéro dépendance PyTorch.
- CPU-only.
- Téléchargement automatique et cache des modèles.
- Conforme au protocole `EmbeddingProvider`.

### ONNXEmbeddingProvider (avancé)

`ONNXEmbeddingProvider` encapsule un modèle ONNX et un tokenizer HuggingFace
`tokenizers`. Il gère la tokenization, l'inférence, le pooling et la
normalisation L2 optionnelle.

Les modèles ONNX peuvent être obtenus de deux manières :

**Option A — via EmbeddingModelManager (recommandé pour les modèles enregistrés) :**

L'`EmbeddingModelManager` télécharge et met en cache les modèles ONNX depuis
le Hub HuggingFace dans `~/.whoosh-ng/models/`. Une fois le modèle installé,
vous passez le chemin du répertoire local au provider :

```python
from whoosh_modern.embeddings import EmbeddingModelManager, ONNXEmbeddingProvider

# Télécharger le modèle (une fois ; mis en cache ensuite)
manager = EmbeddingModelManager()
model_dir = manager.download("multilingual-e5-small")

# Résoudre le chemin du fichier .onnx
onnx_path = str(next(model_dir.glob("*.onnx")))

provider = ONNXEmbeddingProvider(
    model_path=onnx_path,
    tokenizer_dir=str(model_dir),
    pooling="mean",
    normalize=True,
)
```

**Option B — via des chemins locaux explicites (modèles personnalisés ou pré-téléchargés) :**

```python
from whoosh_modern.embeddings import ONNXEmbeddingProvider

provider = ONNXEmbeddingProvider(
    model_path="models/multilingual-e5-small/model.onnx",
    tokenizer_dir="models/multilingual-e5-small",
    pooling="mean",
    normalize=True,
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

## Identifiants de modèles : FastEmbed vs ONNX

Les deux providers interprètent les identifiants de modèles différemment.
Comprendre cette distinction évite la confusion avec des noms existant dans
les deux registres :

| Aspect | FastEmbedProvider | ONNXEmbeddingProvider |
|--------|-------------------|-----------------------|
| Type d'identifiant | Nom de modèle HuggingFace (ex. `BAAI/bge-small-en-v1.5`) | Nom de modèle enregistré (ex. `bge-small-en-v1.5`) **ou** chemin de fichier local |
| Mécanisme de téléchargement | `fastembed` télécharge automatiquement à la première utilisation | `EmbeddingModelManager.download()` télécharge depuis le Hub |
| Emplacement du cache | Cache propre de FastEmbed (`~/.cache/fastembed`) | `~/.whoosh-ng/models/` |
| Registre | Aucun (FastEmbed gère sa propre liste de modèles) | `EmbeddingModelRegistry` (`get_default_registry()`) |
| Exemple | `FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")` | `ONNXEmbeddingProvider(model_path=str(model_dir / "model.onnx"))` |

> **Note d'ambiguïté :** Le nom `bge-small-en-v1.5` existe à la fois comme
> modèle FastEmbed (identifiant de repo HuggingFace sans espace de noms) et
> comme entrée de registre ONNX. Ils produisent des embeddings similaires mais
> **ne sont pas interchangeables** — FastEmbed gère son propre téléchargement,
> tandis que le registre ONNX mappe vers `onnx-community/bge-small-en-v1.5-ONNX`
> via `EmbeddingModelManager`.

## ProviderPool (embedding parallèle)

`ProviderPool` distribue les appels `embed_batch()` across plusieurs instances
de provider pour maximiser le throughput CPU et éviter la contention GIL.

```python
from whoosh_modern.embeddings.provider_pool import ProviderPool
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

pool = ProviderPool(
    provider_factory=lambda: FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5"),
    pool_size=4,
)

vectors = pool.embed_batch(["texte 1", "texte 2", "texte 3", "texte 4"])
print(len(vectors))  # 4
```

Amélioration attendue : throughput parallèle vs provider unique (à mesurer sur votre matériel).

## Réglage du runtime ONNX

`ONNXEmbeddingProvider` expose les options de session ONNX Runtime pour le réglage CPU/GPU :

```python
from whoosh_modern.embeddings.onnx_provider import ONNXEmbeddingProvider

provider = ONNXEmbeddingProvider(
    model_path="models/bge-small-en-v1.5.onnx",
    tokenizer_dir="models/tokenizer",
    use_cuda=True,                    # auto-détecte CUDA, fallback CPU
    intra_op_num_threads=2,           # parallélisme intra-op
    inter_op_num_threads=2,           # parallélisme inter-op
    graph_optimization_level="all",   # active toutes les optimisations
)
```

## EmbeddingBatchWriter v4.0

`EmbeddingBatchWriter` supporte maintenant le provider pooling, la gestion
d'erreurs stricte, le cache LRU thread-safe et les métriques de performance :

```python
from whoosh_modern.indexing import EmbeddingBatchWriter
from whoosh_modern.embeddings.provider_pool import ProviderPool
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

pool = ProviderPool(
    provider_factory=lambda: FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5"),
    pool_size=4,
)

writer = EmbeddingBatchWriter(
    index,
    embedding_provider=pool,
    text_field="body",
    vector_field="body_vector",
    batch_size=500,
    embedding_batch_size=32,
    cache_size=8192,
    strict_errors=True,
)

for batch in source.stream_batches(batch_size=500):
    writer.add_batch(batch)

writer.close()

stats = writer.get_stats()
print(f"Taux de hit cache: {stats['cache']['hit_rate_percent']}%")
print(f"Throughput: {stats['docs_per_second']} docs/sec")
```

## EmbeddingMiddleware v4.0

`EmbeddingMiddleware` accumule maintenant les documents et appelle
`embed_batch()` pour +33% de throughput. Utilisez `batch_size=1` pour le mode
par document (comportement legacy).

```python
from whoosh_modern.middleware.embedding import EmbeddingMiddleware

middleware = EmbeddingMiddleware(
    embedding_provider=provider,
    source_field="content",
    target_field="embedding",
    batch_size=32,          # accumule 32 docs, puis embed_batch()
    strict=True,            # raise on embedding failures
)
```

## Préchargement de modèles

Préchargez les modèles de manière asynchrone au démarrage pour éviter la latence
de première requête :

```python
import asyncio
from whoosh_modern.embeddings.model_preload import preload_embedding_model_async

async def startup():
    await preload_embedding_model_async(
        model_name="BAAI/bge-small-en-v1.5",
        provider_type="fastembed",
    )

asyncio.run(startup())
```

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
| `bge-small-en-v1.5` | 384 | mean | BGE-small anglais (ONNX) |
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
# ONNX avec un nom de modèle enregistré
# EmbeddingModelManager télécharge et met en cache le modèle automatiquement,
# dérivant model_path et tokenizer_dir depuis le cache local.
embedding:
  provider: onnx
  model: multilingual-e5-small
  pooling: mean
  normalize: true
```

```yaml
# ONNX avec des chemins locaux explicites (modèles personnalisés ou pré-téléchargés)
embedding:
  provider: onnx
  model_path: models/multilingual-e5-small/model.onnx
  tokenizer_dir: models/multilingual-e5-small
  pooling: mean
  normalize: true
```

```yaml
# sentence-transformers
embedding:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2
```

```yaml
# Vectorisation multi-champs
# Quand embedding_fields est utilisé, omettez source_field/target_field au
# niveau racine — ils sont ignorés quand embedding_fields est présent.
embedding:
  provider: fastembed
  model: BAAI/bge-small-en-v1.5
  embedding_fields:
    - source_field: title
      target_field: title_vector
    - source_field: body
      target_field: body_vector
```

Providers supportés : `fastembed`, `onnx`, `sentence-transformers`.

> **Précédence des champs multi-champs :** Quand `embedding_fields` est fourni,
> les valeurs par défaut racine `source_field` / `target_field` sont **ignorées**
> — chaque entrée dans `embedding_fields` est traitée indépendamment.
> `SearchView` injecte automatiquement les champs cibles en tant que champs
> `VECTOR` dans le schéma Whoosh généré s'ils ne sont pas déjà déclarés.
> Pour éviter la confusion, omettez `source_field` et `target_field` du niveau
> racine lorsque vous utilisez `embedding_fields`.

### Configuration ONNX

Lorsque vous utilisez `provider: onnx`, vous pouvez spécifier un modèle enregistré
via `model` ou fournir des chemins de fichiers explicites via `model_path` et
`tokenizer_dir`.

- Si `model` est spécifié, `EmbeddingModelManager` téléchargera et gérera le
  modèle, dérivant automatiquement `model_path` et `tokenizer_dir` depuis le
  cache local.
- Si `model_path` et/ou `tokenizer_dir` sont fournis explicitement, ils prennent
  le pas sur les chemins dérivés du nom du `model`.

Il est recommandé d'utiliser soit `model` pour les modèles gérés par le manager,
soit `model_path` / `tokenizer_dir` pour des chemins locaux personnalisés, afin
d'éviter toute ambiguïité.

## Gestion des erreurs d'embedding {#error-handling}

> **Décision de conception :** Les erreurs du fournisseur sont **ignorées**
> (journalisées en tant qu'avertissements) pour éviter d'interrompre le pipeline
> d'indexation. Cela s'applique à tous les providers d'embeddings (FastEmbed,
> ONNX, Sentence Transformers).

Lorsqu'un provider d'embedding lève une exception pendant `embed()` ou
`embed_batch()`, le `EmbeddingMiddleware` attrape l'exception, journalise un
avertissement, et continue l'indexation. Le document concerné sera indexé
**sans** son champ vectoriel, ce qui signifie qu'il ne sera pas recherchable
via la recherche sémantique (similarité) mais restera recherchable via la
recherche par mot-clé (BM25).

Les noms de loggers Python pertinents sont :

| Logger | Module source |
|--------|---------------|
| `whoosh_modern.middleware.embedding` | `EmbeddingMiddleware.before_index()` |
| `whoosh_modern.config.engines.embedding` | `EmbeddingEngine.build()` |

Configurez la journalisation pour contrôler la verbosité et la destination :

```python
import logging

# Journaliser les avertissements d'embedding vers un fichier dédié
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="embedding_warnings.log",
)

# Ou élever les avertissements au niveau ERROR pour les faire remonter en développement
logging.getLogger("whoosh_modern.middleware.embedding").setLevel(logging.ERROR)
```

### Gestion des erreurs dans le benchmark

Le script de benchmark `benchmark/stock_parquet_embedding.py` suit le même
modèle : les exceptions du provider sont attrapées, un avertissement est
imprimé sur `stderr`, et le document est ignoré. Les échecs sont suivis dans
la sortie du benchmark sous la clé `failures`.

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
