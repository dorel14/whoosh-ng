window.BENCHMARK_DATA = {
  "lastUpdate": 1783870566504,
  "repoUrl": "https://github.com/dorel14/whoosh-ng",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "1ee6599ac17ad9719d8f6771b46fc0768c3e1a1b",
          "message": "chore(workflows): 🔄 Ajoute la permission `workflows: write` pour permettre les modifications des workflows\n\n* Cette modification est nécessaire pour permettre le déploiement des changements dans les workflows.",
          "timestamp": "2026-07-11T16:49:14+02:00",
          "tree_id": "f950a42e37e04850702f79742af69bafcfb876d5",
          "url": "https://github.com/dorel14/whoosh-ng/commit/1ee6599ac17ad9719d8f6771b46fc0768c3e1a1b"
        },
        "date": 1783781402170,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1130.6109018266484,
            "unit": "iter/sec",
            "range": "stddev: 0.00004312342106325787",
            "extra": "mean: 884.4775849802708 usec\nrounds: 506"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "f97247662ff6442048795a599dbdc4fdc4119968",
          "message": "chore(workflows): 🔄 Mise à jour des permissions pour les actions de workflow\n\n* Remplace `workflows: write` par `actions: write` dans les permissions des jobs.\n* Cette modification est nécessaire pour permettre les modifications des workflows.",
          "timestamp": "2026-07-11T16:53:51+02:00",
          "tree_id": "be3e5545b7557c7b4662283adc3b0047ab35e4db",
          "url": "https://github.com/dorel14/whoosh-ng/commit/f97247662ff6442048795a599dbdc4fdc4119968"
        },
        "date": 1783781679229,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1058.0919195633383,
            "unit": "iter/sec",
            "range": "stddev: 0.000027245399659380556",
            "extra": "mean: 945.0974735849868 usec\nrounds: 530"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "cbf58e243070d119f977bb4997005321ce91940c",
          "message": "fix(workflows): 🐛 Remplace l'utilisation de `actions/delete-artifact` par un script personnalisé pour supprimer les artefacts obsolètes\n\n* Améliore la gestion des artefacts en utilisant `actions/github-script` pour supprimer les artefacts nommés `github-pages`.\n* Permet une meilleure flexibilité et contrôle sur la suppression des artefacts.",
          "timestamp": "2026-07-11T16:55:29+02:00",
          "tree_id": "5344a3891fbdd6d0d093f11d778c012c6358cdff",
          "url": "https://github.com/dorel14/whoosh-ng/commit/cbf58e243070d119f977bb4997005321ce91940c"
        },
        "date": 1783781776108,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1046.0299343372835,
            "unit": "iter/sec",
            "range": "stddev: 0.00003723217718661146",
            "extra": "mean: 955.9955859519011 usec\nrounds: 541"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "304cbd95fe3764241cd1205951ebc7531c6a9648",
          "message": "chore(docs): ✏️ Mise à jour de la documentation et suppression de fichiers obsolètes\n\n* Suppression de fichiers inutilisés tels que `Makefile`, `make.bat`, et `requirements.txt`.\n* Réorganisation de la documentation en ajoutant des fichiers de démarrage rapide en français.\n* Correction du chemin de journalisation dans le fichier de workflow `test.yml`.\n* Mise à jour de la configuration de documentation pour une meilleure gestion des langues.",
          "timestamp": "2026-07-11T19:28:39+02:00",
          "tree_id": "3c299724fd2f1e67bc44c49fd46dd14b0b6c1a78",
          "url": "https://github.com/dorel14/whoosh-ng/commit/304cbd95fe3764241cd1205951ebc7531c6a9648"
        },
        "date": 1783790967486,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1056.7173729343435,
            "unit": "iter/sec",
            "range": "stddev: 0.00005530793452225306",
            "extra": "mean: 946.3268283582318 usec\nrounds: 536"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "b3db23c70c5eb75356e3fbe3709fbe91a779963f",
          "message": "Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev",
          "timestamp": "2026-07-12T16:40:57+02:00",
          "tree_id": "cf1d8d7ae6f66578659a2a66e3e48a5fecc7732e",
          "url": "https://github.com/dorel14/whoosh-ng/commit/b3db23c70c5eb75356e3fbe3709fbe91a779963f"
        },
        "date": 1783867302405,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1130.2267269702722,
            "unit": "iter/sec",
            "range": "stddev: 0.00007100171229066114",
            "extra": "mean: 884.7782273567686 usec\nrounds: 541"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "071013cc8709817e96de883b3e4e7f13df319e1c",
          "message": "fix(docs): 🐛 Correction du titre de la documentation Whoosh-ng\n\n* Mise à jour du titre pour respecter la casse correcte.",
          "timestamp": "2026-07-12T16:41:26+02:00",
          "tree_id": "ee30cb7b1d9cc9d4282bd58ac980021196c16671",
          "url": "https://github.com/dorel14/whoosh-ng/commit/071013cc8709817e96de883b3e4e7f13df319e1c"
        },
        "date": 1783867335114,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1056.8507063035097,
            "unit": "iter/sec",
            "range": "stddev: 0.000030418265639086156",
            "extra": "mean: 946.2074387948763 usec\nrounds: 531"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "4ee9b4c595d5c5351a8b1635293d5a83e99057a4",
          "message": "feat(examples): ✨ Add multiple examples for Whoosh‑NG integration\n\n- Introduced `autocomplete.md` demonstrating autocomplete functionality using `whoosh_modern.autocomplete`.\n- Added `fastapi-search.md` showcasing FastAPI integration with Whoosh‑NG for document search.\n- Created `movie-search.md` illustrating a movie search application with faceted search and filtering.\n- Implemented `vector-search.md` for semantic/vector search using document embeddings.\n- Translated examples into French for broader accessibility.",
          "timestamp": "2026-07-12T17:20:26+02:00",
          "tree_id": "e23e8b9ccbfef9b58c657e265f998ae08a943b64",
          "url": "https://github.com/dorel14/whoosh-ng/commit/4ee9b4c595d5c5351a8b1635293d5a83e99057a4"
        },
        "date": 1783869669650,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1155.9771082244388,
            "unit": "iter/sec",
            "range": "stddev: 0.00003601147526841071",
            "extra": "mean: 865.0690337077549 usec\nrounds: 534"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "ee29ecdc8350cbbb9c16b353bfaf8727ed262bec",
          "message": "Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev",
          "timestamp": "2026-07-12T17:33:13+02:00",
          "tree_id": "c790bac344ff537ee45635f154f97e5136217d08",
          "url": "https://github.com/dorel14/whoosh-ng/commit/ee29ecdc8350cbbb9c16b353bfaf8727ed262bec"
        },
        "date": 1783870436449,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1056.1562818559119,
            "unit": "iter/sec",
            "range": "stddev: 0.000029025865268900303",
            "extra": "mean: 946.8295717019906 usec\nrounds: 523"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "committer": {
            "email": "david.orel@sfr.fr",
            "name": "David Orel"
          },
          "distinct": true,
          "id": "5e5f3c4679c588c4e5bd6c4736d6322b65d5a9a0",
          "message": "Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev",
          "timestamp": "2026-07-12T17:35:24+02:00",
          "tree_id": "d764d13613edb05353d25a2a91940d2419f01064",
          "url": "https://github.com/dorel14/whoosh-ng/commit/5e5f3c4679c588c4e5bd6c4736d6322b65d5a9a0"
        },
        "date": 1783870566184,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1161.654265032218,
            "unit": "iter/sec",
            "range": "stddev: 0.00005345359315839586",
            "extra": "mean: 860.8413278388517 usec\nrounds: 546"
          }
        ]
      }
    ]
  }
}