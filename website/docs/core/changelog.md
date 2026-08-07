---
title: "Changelog"
sidebar_position: 80
---

# Changelog

Release notes for Whoosh-NG, auto-generated from GitHub releases and commit messages.

## v4.1.0 (2026-08-07)
**Tag**: `v4.1.0`

## v4.1.0 (2026-08-07)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- **ci**: Fix broken workflows and Docusaurus build errors after migration ([`0e86e6c`](https://github.com/dorel14/whoosh-ng/commit/0e86e6c51e3d41fec984f0f79a4457e9d5d0b1ef))

- **ci**: Fix sync_version.py NameError and missing imports ([`f809f56`](https://github.com/dorel14/whoosh-ng/commit/f809f563851b102c7220cec0371c560191bdb217))

### Features

- **docs**: Migrate Jekyll/Just the Docs to Docusaurus v3 ([`7e70791`](https://github.com/dorel14/whoosh-ng/commit/7e70791d23fb0f3097e3603ba0ff3fa5c8d822c2))

---

**Detailed Changes**: [v4.0.1...v4.1.0](https://github.com/dorel14/whoosh-ng/compare/v4.0.1...v4.1.0)

### Commits

### Chores

- synchronize version from pyproject.toml [skip ci]
- v4.1.0 [skip ci]

### Features

- migrate Jekyll/Just the Docs to Docusaurus v3

### Bug Fixes

- fix broken workflows and Docusaurus build errors after migration
- fix sync_version.py NameError and missing imports


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v4.1.0)

## v4.0.1 (2026-08-07)
**Tag**: `v4.0.1`

## v4.0.1 (2026-08-07)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- **pages**: Pointer Bundler sur docs/Gemfile via BUNDLE_GEMFILE ([`0f3a8f1`](https://github.com/dorel14/whoosh-ng/commit/0f3a8f11087c5df910d1762f31ae1cee4017ed31))

---

**Detailed Changes**: [v4.0.0...v4.0.1](https://github.com/dorel14/whoosh-ng/compare/v4.0.0...v4.0.1)

### Commits

### Chores

- synchronize version from pyproject.toml [skip ci]
- v4.0.1 [skip ci]

### Bug Fixes

- pointer Bundler sur docs/Gemfile via BUNDLE_GEMFILE


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v4.0.1)

## v4.0.0 (2026-08-07)
**Tag**: `v4.0.0`

## v4.0.0 (2026-08-07)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- **ci**: Corriger les erreurs de lint, mypy et pyright ([`4283355`](https://github.com/dorel14/whoosh-ng/commit/428335590e641870f6bc399b241b453745e4b9a3))

---

**Detailed Changes**: [v3.0.0...v4.0.0](https://github.com/dorel14/whoosh-ng/compare/v3.0.0...v4.0.0)

### Commits

### Features

- restructurer le système de middleware et étendre PluginManager
- ajouter le module linguistics avec analyseurs multilingues
- add asearch/awriter bridges and AsyncFileStorage
- enhance FastAPI models and Admin Studio modules
- add SearchApplication and FileStorage exports
- add S3Storage, HybridStorage, AsyncHybridStorage
- add SnapshotStorage, CachedObjectStorage alias, and Phase 3 roadmap
- publier la version 3.0.0 et ajouter la documentation LLM

### Documentation

- ajouter les guides Whoosh-NG 2.0 et ajuster la configuration de release
- add Gemfile.lock for reproducible Jekyll build and fix French index permalinks
- add S3 storage benchmarks and documentation
- auto-update llms context files

### Chores

- restructurer les workflows CI/CD et nettoyer le code
- apply pre-commit fixes
- v4.0.0 [skip ci]

### Other

- Merge branch 'master' into dev
- Merge pull request #14 from dorel14/dev

### Bug Fixes

- corriger les erreurs de lint, mypy et pyright


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v4.0.0)

## v3.0.0 (2026-08-06)
**Tag**: `v3.0.0`

## v3.0.0 (2026-08-06)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- Ajouter reportAssignmentType en warning dans pyrightconfig.json ([`3259c76`](https://github.com/dorel14/whoosh-ng/commit/3259c76660a4f99135a8cda1ac26baa3f642a873))

- Corriger docstring PathTokenizer et restaurer Literal pour engine ([`b90222e`](https://github.com/dorel14/whoosh-ng/commit/b90222e5962671dfb20f496d396f546f33c95747))

- Mapper engine pyarrow vers auto pour pandas et exclure tests/ de mypy ([`dadeb91`](https://github.com/dorel14/whoosh-ng/commit/dadeb91cffd9462d0c5c2aff77fd36f4cbac8f4a))

- Ne pas yield de token vide dans RegexTokenizer gaps=True ([`6385a24`](https://github.com/dorel14/whoosh-ng/commit/6385a24cb048777aef9cc5d2bad46f2e5d2e5dfa))

- Remove unreachable dead code after build() return in parallel_builder ([`c2e03c9`](https://github.com/dorel14/whoosh-ng/commit/c2e03c97bda6ac61d78c38c6ac3ad37df4f9345a))

- Rendre test_buffered_threads deterministe en couverture des valeurs ([`77a66f6`](https://github.com/dorel14/whoosh-ng/commit/77a66f6320f9ff7bfe8a1c787c52d1bb0e3cf0d6))

- Resolve mypy errors in CI (parquet, tortoise, hnswlib) ([`514f1f6`](https://github.com/dorel14/whoosh-ng/commit/514f1f62d55edd92633654e0096caf920a9ff3a6))

- Réintégrer assert segment_reader is not None après merge distant ([`c42b065`](https://github.com/dorel14/whoosh-ng/commit/c42b065355bb0004094223748a7c9b6eca810405))

- Résoudre les erreurs pyright dans pre-commit (Token typing, reportAttributeAccessIssue) ([`eff5adf`](https://github.com/dorel14/whoosh-ng/commit/eff5adf55cbbae6169bf2efacc76fddacc1891dd))

- Résoudre les erreurs pyright reportOptionalMemberAccess et reportAssignmentType ([`572529e`](https://github.com/dorel14/whoosh-ng/commit/572529e1fb7f0828f3729ed7920e219a71df139c))

- Supprimer cast redondant et ajouter reportAssignmentType en warning ([`0834923`](https://github.com/dorel14/whoosh-ng/commit/0834923f185a4fb62ded3e5020ea6d36b90bfc42))

- **analysis**: Corriger l'indentation du RegexTokenizer et ajuster les annotations de type ([`69e9ad8`](https://github.com/dorel14/whoosh-ng/commit/69e9ad815192ed9113acea4075e21eaf9e514f8d))

- **deps**: Retirer les modules obsolètes des exclusions mypy ([`f53e157`](https://github.com/dorel14/whoosh-ng/commit/f53e15729647ac7473066f193a33fcbfb2a3dce0))

- **indexing**: Close segment_ix in ParallelIndexBuilder to prevent fd leak ([`bad2928`](https://github.com/dorel14/whoosh-ng/commit/bad2928155d424e19de24e5b00822831695e7449))

- **indexing**: Corriger les fuites de handles et erreurs de nettoyage sous Windows ([`3cb85c7`](https://github.com/dorel14/whoosh-ng/commit/3cb85c7d9f80eccdbb5d2225d270d9f4c15b79bd))

- **indexing**: Merge parallel worker segments into main index ([`6f18248`](https://github.com/dorel14/whoosh-ng/commit/6f182488b18aedaceaf4c886b1b0d87eadc02a99))

- **indexing**: Merge worker segments into main index in ParallelIndexBuilder ([`27b0541`](https://github.com/dorel14/whoosh-ng/commit/27b054140d1a99228a804b75a1d4efd3e4f300ce))

- **mypy**: Restore ignore_missing_imports for pytest, peewee, httpx, re2, psutil ([`699ee4f`](https://github.com/dorel14/whoosh-ng/commit/699ee4f2fb3007012913d5970376f97fc99a0296))

- **profiling**: Add segment_write() and sibling step context managers to CommitProfilerV2 ([`599b650`](https://github.com/dorel14/whoosh-ng/commit/599b6507149332b3e0522b753e547bae718b468e))

- **profiling**: Implement SegmentProfiler to resolve NameError in benchmark.py ([`1b03b3a`](https://github.com/dorel14/whoosh-ng/commit/1b03b3ae7fbc3d03c7223ab4f7759eb500c9c8bf))

### Documentation

- Auto-update llms context files ([`5cca243`](https://github.com/dorel14/whoosh-ng/commit/5cca243cba55d49836e89793af3ac126815b862c))

- Auto-update llms context files ([`55825c1`](https://github.com/dorel14/whoosh-ng/commit/55825c15502f0b15041aec9ac15d7f9c4bc23e6c))

- Auto-update llms context files ([`c0d74a4`](https://github.com/dorel14/whoosh-ng/commit/c0d74a4cda58a44898a0b3f67fdc009fefa565fe))

- Restructurer la documentation et ajouter les pages API et guides ([`4e9b1e2`](https://github.com/dorel14/whoosh-ng/commit/4e9b1e2ce8a494c66f1725cec3b03e5025643e8d))

- **guides**: Ajouter le guide d'indexation moderne et mettre à jour les index de documentation ([`9fbc4ff`](https://github.com/dorel14/whoosh-ng/commit/9fbc4ff41dafc184219f0b4f1da3ee4f3e0ecb71))

### Features

- Ajouter FastCSVSource, indexation par lots, infrastructure de profiling et optimisations du cœur ([`fc63f9c`](https://github.com/dorel14/whoosh-ng/commit/fc63f9c890155fa9ce0b25c03e9db733eb7f0139))

- **analysis**: Ajouter le système de stemmers, FastCSVSource et l'infrastructure de profiling des performances ([`a077319`](https://github.com/dorel14/whoosh-ng/commit/a077319a8fc7435ef283b5c2b5402538c6550819))

- **core**: Ajouter CacheMiddleware et ObservableDataSource ([`508589a`](https://github.com/dorel14/whoosh-ng/commit/508589a8c86c7d1eadeb6ffd044a340fe84363be))

- **data-sources**: Ajouter les sources de données et le pooling de connexions ([`51805d4`](https://github.com/dorel14/whoosh-ng/commit/51805d4c08109b78704f6938deb4c135f57b0674))

- **data-sources**: Améliorer la robustesse et la validation des sources de données ([`35281b5`](https://github.com/dorel14/whoosh-ng/commit/35281b534865111e30d0d1195c492d72b8769e75))

- **profiling**: Ajouter les groupes d'options profiling et fast-stemming, stream_batches et restructurer les chemins d'import des sources de données ([`152e9c4`](https://github.com/dorel14/whoosh-ng/commit/152e9c44b68380a9d238489a29ebfd52e28f97a9))

---

**Detailed Changes**: [v2.0.0...v3.0.0](https://github.com/dorel14/whoosh-ng/compare/v2.0.0...v3.0.0)

### Commits

### Other

- Remove workflows permission from test.yml
- Revise README for version 2.0.0 updates
- Merge pull request #12 from dorel14/master
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Potential fix for pull request finding 'CodeQL / Workflow does not contain permissions'
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- .
- Update src/whoosh_modern/indexing/parallel_builder.py
- codec/base: restore missing out-of-order term check in add_postings
- Update src/whoosh_modern/profiling/segment_profiler.py
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge c42b065355bb0004094223748a7c9b6eca810405 into 9988770df03a2d255a21b74843772776dbbf998a
- Merge pull request #13 from dorel14/dev
- Update commit_parser_options in pyproject.toml
- Add files via upload

### Build System

- automatiser la synchronisation de la version entre les fichiers du projet

### Chores

- apply pre-commit fixes
- simplifier la configuration type-checking et retirer les dépendances inutilisées
- apply pre-commit fixes
- apply pre-commit fixes
- trigger pre-commit workflow
- v3.0.0 [skip ci]

### Features

- ajouter CacheMiddleware et ObservableDataSource
- ajouter les sources de données et le pooling de connexions
- ajouter FastCSVSource, indexation par lots, infrastructure de profiling et optimisations du cœur
- ajouter le système de stemmers, FastCSVSource et l'infrastructure de profiling des performances
- ajouter les groupes d'options profiling et fast-stemming, stream_batches et restructurer les chemins d'import des sources de données
- améliorer la robustesse et la validation des sources de données

### Code Refactoring

- simplifier les expressions multi-lignes et optimiser Token avec __slots__
- nettoyer les annotations de type et supprimer les dépendances inutilisées

### Documentation

- auto-update llms context files
- restructurer la documentation et ajouter les pages API et guides
- auto-update llms context files
- ajouter le guide d'indexation moderne et mettre à jour les index de documentation
- auto-update llms context files

### Bug Fixes

- corriger l'indentation du RegexTokenizer et ajuster les annotations de type
- resolve mypy errors in CI (parquet, tortoise, hnswlib)
- ne pas yield de token vide dans RegexTokenizer gaps=True
- résoudre les erreurs pyright dans pre-commit (Token typing, reportAttributeAccessIssue)
- supprimer cast redondant et ajouter reportAssignmentType en warning
- ajouter reportAssignmentType en warning dans pyrightconfig.json
- corriger docstring PathTokenizer et restaurer Literal pour engine
- mapper engine pyarrow vers auto pour pandas et exclure tests/ de mypy
- remove unreachable dead code after build() return in parallel_builder
- add segment_write() and sibling step context managers to CommitProfilerV2
- implement SegmentProfiler to resolve NameError in benchmark.py
- merge parallel worker segments into main index
- merge worker segments into main index in ParallelIndexBuilder
- rendre test_buffered_threads deterministe en couverture des valeurs
- retirer les modules obsolètes des exclusions mypy
- close segment_ix in ParallelIndexBuilder to prevent fd leak
- résoudre les erreurs pyright reportOptionalMemberAccess et reportAssignmentType
- réintégrer assert segment_reader is not None après merge distant
- restore ignore_missing_imports for pytest, peewee, httpx, re2, psutil
- corriger les fuites de handles et erreurs de nettoyage sous Windows


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v3.0.0)

## v2.0.0 (2026-07-31)
**Tag**: `v2.0.0`

## v2.0.0 (2026-07-31)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- Address review findings in CI/CD workflows and documentation ([`b1e0b89`](https://github.com/dorel14/whoosh-ng/commit/b1e0b89f10ad182ad0120d6d19bcac2f8a04470a))

### Documentation

- Auto-update llms context files ([`10e6c90`](https://github.com/dorel14/whoosh-ng/commit/10e6c90fb6e7ffd9ec9f1b3fa7f4e398a933077b))

- Auto-update llms context files ([`992e4d7`](https://github.com/dorel14/whoosh-ng/commit/992e4d780fd7829bd804d68b215e06f255e9cacf))

- Auto-update llms context files ([`5dfe9dc`](https://github.com/dorel14/whoosh-ng/commit/5dfe9dcfdd725d1ca12f3bba0c09a2f7d163aa88))

- Auto-update llms context files ([`aadce99`](https://github.com/dorel14/whoosh-ng/commit/aadce99460c30cd5950e44c927c07eb6fa5ffde8))

### Features

- **deps**: Add sqlalchemy and sqlmodel to models extra and configure mypy overrides ([`4486b5f`](https://github.com/dorel14/whoosh-ng/commit/4486b5feef2700fd8720a0dec1419985f9479951))

- **models**: Ajouter AutoIndexer et améliorer la génération de schémas ([`919131c`](https://github.com/dorel14/whoosh-ng/commit/919131ce7f475b8584e74d98d9cf41e04891b7c7))

- **models**: ✨ Introduce ModelIndex and SearchField for auto-mapping ([`6c202bc`](https://github.com/dorel14/whoosh-ng/commit/6c202bc6c4e20ad9dba7e4cd81deadfdaf3dcf2a))

- **whoosh_modern**: Add modern API with data sources, schema discovery, facets, validation, middleware, and SearchView ([`36bfbae`](https://github.com/dorel14/whoosh-ng/commit/36bfbaebd6acc18cda06aba83bebade7154c9972))

---

**Detailed Changes**: [v1.3.3...v2.0.0](https://github.com/dorel14/whoosh-ng/compare/v1.3.3...v2.0.0)

### Commits

### Documentation

- merge duplicate FastAPI example into fastapi-search.md
- auto-update llms context files
- auto-update llms context files
- auto-update llms context files
- auto-update llms context files

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng
- ..
- Merge pull request #10 from dorel14/master
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- style(benchmark): ajouter un saut de ligne final manquant dans reuters_modern.py
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Potential fix for pull request finding 'CodeQL / Workflow does not contain permissions'
- Potential fix for pull request finding 'CodeQL / Workflow does not contain permissions'
- Potential fix for pull request finding 'CodeQL / Workflow does not contain permissions'
- .
- .
- .
- Merge pull request #11 from dorel14/dev

### Features

- ✨ Introduce ModelIndex and SearchField for auto-mapping
- ajouter AutoIndexer et améliorer la génération de schémas
- add modern API with data sources, schema discovery, facets, validation, middleware, and SearchView
- add sqlalchemy and sqlmodel to models extra and configure mypy overrides

### Bug Fixes

- address review findings in CI/CD workflows and documentation

### Code Refactoring

- moderniser les annotations de type avec la syntaxe union PEP 604
- moderniser les annotations de type avec Coroutine et ajouter des ignores pyright
- ajouter des annotations de retour aux méthodes replace des matchers
- moderniser la vérification isinstance avec la syntaxe union PEP 604

### CI/CD

- ajouter des extras d'installation et simplifier la couverture

### Chores

- v2.0.0 [skip ci]


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v2.0.0)

## v1.3.3 (2026-07-26)
**Tag**: `v1.3.3`

## v1.3.3 (2026-07-26)

_This release is published under the BSD-2-Clause License._

---

**Detailed Changes**: [v1.3.2...v1.3.3](https://github.com/dorel14/whoosh-ng/compare/v1.3.2...v1.3.3)

### Commits

### Bug Fixes

- reorganize nav_order for coherent navigation (Guides 1-90, API 100-190, Examples 200-270)

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng

### Chores

- v1.3.3 [skip ci]


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.3.3)

## v1.3.2 (2026-07-26)
**Tag**: `v1.3.2`

## v1.3.2 (2026-07-26)

_This release is published under the BSD-2-Clause License._

---

**Detailed Changes**: [v1.3.1...v1.3.2](https://github.com/dorel14/whoosh-ng/compare/v1.3.1...v1.3.2)

### Commits

### Bug Fixes

- remove color_scheme from individual pages, use global config

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng

### Chores

- v1.3.2 [skip ci]


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.3.2)

## v1.3.1 (2026-07-26)
**Tag**: `v1.3.1`

## v1.3.1 (2026-07-26)

_This release is published under the BSD-2-Clause License._

---

**Detailed Changes**: [v1.3.0...v1.3.1](https://github.com/dorel14/whoosh-ng/compare/v1.3.0...v1.3.1)

### Commits

### Bug Fixes

- align _config.yml with taskiq-flow and clean README front matter

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng

### Chores

- v1.3.1 [skip ci]


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.3.1)

## v1.3.0 (2026-07-26)
**Tag**: `v1.3.0`

## v1.3.0 (2026-07-26)

_This release is published under the BSD-2-Clause License._

---

**Detailed Changes**: [v1.2.4...v1.3.0](https://github.com/dorel14/whoosh-ng/compare/v1.2.4...v1.3.0)

### Commits

### Features

- éviter les exécutions inutiles du workflow lors des commits de release

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng

### Chores

- v1.3.0 [skip ci]


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.3.0)

## v1.2.4 (2026-07-26)
**Tag**: `v1.2.4`

## v1.2.4 (2026-07-26)

_This release is published under the BSD-2-Clause License._

---

**Detailed Changes**: [v1.2.3...v1.2.4](https://github.com/dorel14/whoosh-ng/compare/v1.2.3...v1.2.4)

### Commits

### Bug Fixes

- remove invalid parent fields and align config with taskiq-flow

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng

### Chores

- v1.2.4


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.2.4)

## v1.2.3 (2026-07-26)
**Tag**: `v1.2.3`

## v1.2.3 (2026-07-26)

_This release is published under the BSD-2-Clause License._

---

**Detailed Changes**: [v1.2.2...v1.2.3](https://github.com/dorel14/whoosh-ng/compare/v1.2.2...v1.2.3)

### Commits

### Bug Fixes

- remove invalid parent fields from all pages

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng

### Chores

- v1.2.3


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.2.3)

## v1.2.2 (2026-07-26)
**Tag**: `v1.2.2`

## v1.2.2 (2026-07-26)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- **docs**: Align _config.yml with taskiq-flow pattern ([`2124be0`](https://github.com/dorel14/whoosh-ng/commit/2124be0cf1fd4669c9ebdaa4ad485eabae22c279))

---

**Detailed Changes**: [v1.2.1...v1.2.2](https://github.com/dorel14/whoosh-ng/compare/v1.2.1...v1.2.2)

### Commits

### Code Refactoring

- supprimer la navigation statique codée en dur

### Other

- Merge branch 'master' of https://github.com/dorel14/whoosh-ng

### Bug Fixes

- align _config.yml with taskiq-flow pattern

### Chores

- v1.2.2


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.2.2)

## v1.2.1 (2026-07-26)
**Tag**: `v1.2.1`

## v1.2.1 (2026-07-26)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- **docs**: Restore front matter and add explicit nav config ([`74dc151`](https://github.com/dorel14/whoosh-ng/commit/74dc151104a7a89ffd1459a60e0e28488bf110ff))

### Documentation

- Fix Jekyll links with relative_url and clean deploy workflow ([`2f9afc2`](https://github.com/dorel14/whoosh-ng/commit/2f9afc20f5e41022117a636b0d223f92c660df3d))

---

**Detailed Changes**: [v1.2.0...v1.2.1](https://github.com/dorel14/whoosh-ng/compare/v1.2.0...v1.2.1)

### Commits

### Documentation

- fix Jekyll links with relative_url and clean deploy workflow

### Bug Fixes

- restore front matter and add explicit nav config

### Chores

- v1.2.1


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.2.1)

## v1.2.0 (2026-07-26)
**Tag**: `v1.2.0`

## v1.2.0 (2026-07-26)

_This release is published under the BSD-2-Clause License._

### Documentation

- Ajouter la documentation complète bilingue et le déploiement GitHub Pages ([`a091ced`](https://github.com/dorel14/whoosh-ng/commit/a091cede82bb5d722e5db0ff233c1dcbcecd35ea))

- Auto-update llms context files ([`96e4f2c`](https://github.com/dorel14/whoosh-ng/commit/96e4f2c251ccdde5e9fd7e9cb0ce6b2650ab64d9))

- Auto-update llms context files ([`6abefe4`](https://github.com/dorel14/whoosh-ng/commit/6abefe4b84d99e29c1d6ccb471dd7bf27ea4f31d))

### Features

- **docs**: Ajouter le support multilingue dans la configuration ([`967ed12`](https://github.com/dorel14/whoosh-ng/commit/967ed125e5fcd167e237e1c32b7feeb3ab6f9c4f))

---

**Detailed Changes**: [v1.1.0...v1.2.0](https://github.com/dorel14/whoosh-ng/compare/v1.1.0...v1.2.0)

### Commits

### CI/CD

- restructurer le workflow de release sémantique

### Other

- Merge pull request #7 from dorel14/dev
- revert: supprimer la documentation complète bilingue et restaurer l'état précédent
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge pull request #8 from dorel14/dev
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge pull request #9 from dorel14/dev

### Documentation

- ajouter la documentation complète bilingue et le déploiement GitHub Pages
- auto-update llms context files
- auto-update llms context files

### Features

- ajouter le support multilingue dans la configuration

### Chores

- v1.2.0


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.2.0)

## v1.1.0 (2026-07-26)
**Tag**: `v1.1.0`

## v1.1.0 (2026-07-26)

_This release is published under the BSD-2-Clause License._

### Bug Fixes

- **bench**: 🐛 add type ignores for method overrides in `XappyModule` ([`822e957`](https://github.com/dorel14/whoosh-ng/commit/822e957c986f603e9fd1c2de2799fb60d3c122a9))

- **schema**: 🐛 corriger l'initialisation de l'objet dans `__new__` ([`5a764a7`](https://github.com/dorel14/whoosh-ng/commit/5a764a78751a6a2bb94118340784da074fdcf2c8))

- **stress**: 🐛 ensure correct handling of string encoding in `test_bigtable` ([`822e957`](https://github.com/dorel14/whoosh-ng/commit/822e957c986f603e9fd1c2de2799fb60d3c122a9))

### Build System

- **deps**: Supprimer les dépendances obsolètes de la section models ([`227a59f`](https://github.com/dorel14/whoosh-ng/commit/227a59fc195799aca02289c2cb5f3d60135ea063))

### Features

- **benchmark**: Refonte du système de benchmarks avec nouvelles spécifications ([`417efd1`](https://github.com/dorel14/whoosh-ng/commit/417efd1be034fe8be4377ad2716e7b15028ad929))

- **matching**: ✨ add type hints for `supports_block_quality` methods ([`822e957`](https://github.com/dorel14/whoosh-ng/commit/822e957c986f603e9fd1c2de2799fb60d3c122a9))

- **support**: ✨ add compatibility for Python 3 unicode handling ([`822e957`](https://github.com/dorel14/whoosh-ng/commit/822e957c986f603e9fd1c2de2799fb60d3c122a9))

- **writing**: ✨ Implement segment writing and merging policies ([`ae5fc62`](https://github.com/dorel14/whoosh-ng/commit/ae5fc62d2185ac349b56cbbf006bbb7fd4f92c80))

---

**Detailed Changes**: [v1.0.0...v1.1.0](https://github.com/dorel14/whoosh-ng/compare/v1.0.0...v1.1.0)

### Commits

### Chores

- ✏️ Mise à jour de la version dans le README
- prepare whoosh-ng 1.0.0
- bump version to 1.0.1
- 🔄 Update project dependencies
- apply pre-commit fixes
- apply pre-commit fixes
- v1.1.0

### Other

- Potential fix for code scanning alert no. 1: Workflow does not contain permissions
- Potential fix for code scanning alert no. 1: Workflow does not contain permissions
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge pull request #5 from dorel14/alert-autofix-1
- Merge branch 'master' into dev
- Potential fix for pull request finding 'CodeQL / Workflow does not contain permissions'
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge 3d0187143ec5a2a4e19f62d26a622d2c53efc2c7 into 68e67aaefb0d48f136d53576e00f10d68f77f15a
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge 4473223d510f0cde2d30ca638d284f23dc467b14 into 68e67aaefb0d48f136d53576e00f10d68f77f15a
- Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev
- Merge pull request #6 from dorel14/dev

### Features

- ✨ Ajout de la validation de l'intégrité des segments
- ✨ Ajout d'un wrapper Asyncio pour la gestion asynchrone des écritures
- ✨ Isolation des espaces de stockage temporaires pour les écrivains concurrents
- ✨ Ajout de la normalisation des boosts pour les sous-requêtes
- ✨ Ajout d'un module de reporting pour les résultats de benchmark
- ✨ Ajout d'un backend LMDB et d'un support d'autocomplétion
- ✨ Implement segment writing and merging policies
- refonte du système de benchmarks avec nouvelles spécifications
- ✨ add type hints for `supports_block_quality` methods

### Bug Fixes

- 🐛 Ajout d'un type d'ignore pour l'appel de la requête
- 🐛 Amélioration des benchmarks avec un échauffement et ajustement des seuils d'alerte
- 🐛 corriger l'initialisation de l'objet dans `__new__`

### Code Refactoring

- improve _posting_size estimation, fix benchmark CLI, update mypy target to 3.12

### Build System

- supprimer les dépendances obsolètes de la section models


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.1.0)

## v1.0.0 (2026-07-12)
**Tag**: `v1.0.0`

## v1.0.0 (2026-07-12)

_This release is published under the BSD-2-Clause License._

- Initial Release


[View on GitHub](https://github.com/dorel14/whoosh-ng/releases/tag/v1.0.0)
