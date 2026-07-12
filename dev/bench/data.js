window.BENCHMARK_DATA = {
  "lastUpdate": 1783873838022,
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
          "id": "e685c67e902be1914f394145fe00bd87ca8c5803",
          "message": "fix(docs): 📝 Met à jour les liens dans la documentation\n\n* Corrige les liens des sections de documentation pour pointer vers les URL complètes.\n* Assure une navigation correcte pour les utilisateurs en fournissant des liens valides.",
          "timestamp": "2026-07-12T17:46:21+02:00",
          "tree_id": "add2eb49cf4ac6020851a548684433c2456e22a9",
          "url": "https://github.com/dorel14/whoosh-ng/commit/e685c67e902be1914f394145fe00bd87ca8c5803"
        },
        "date": 1783871222877,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1058.431581056396,
            "unit": "iter/sec",
            "range": "stddev: 0.00003352119876153523",
            "extra": "mean: 944.7941821633128 usec\nrounds: 527"
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
          "id": "9aa4cf779e7c69b1fae6735f6804772914d79526",
          "message": ".",
          "timestamp": "2026-07-12T17:46:44+02:00",
          "tree_id": "ff8c866c6aeb2c07a55e9095901a33690bd5236b",
          "url": "https://github.com/dorel14/whoosh-ng/commit/9aa4cf779e7c69b1fae6735f6804772914d79526"
        },
        "date": 1783871261626,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1376.6389058252478,
            "unit": "iter/sec",
            "range": "stddev: 0.00005395727805909633",
            "extra": "mean: 726.4069000000652 usec\nrounds: 550"
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
          "id": "4201fdb851c9460006a66d72376b1f1644a40e0d",
          "message": "Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev",
          "timestamp": "2026-07-12T17:54:51+02:00",
          "tree_id": "cab4894fec98319f536d161103bf66c0f954a7b1",
          "url": "https://github.com/dorel14/whoosh-ng/commit/4201fdb851c9460006a66d72376b1f1644a40e0d"
        },
        "date": 1783871736886,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1089.107371608303,
            "unit": "iter/sec",
            "range": "stddev: 0.0000288439375053202",
            "extra": "mean: 918.1831158880901 usec\nrounds: 535"
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
          "id": "0d8af2e32e492273b15066c184e4409b88e192d4",
          "message": "chore: 🔧 Réorganisation des étapes de déploiement de la documentation\n\n* Suppression des paramètres par défaut inutiles dans le job de déploiement.\n* Ajout de la directive `working-directory` pour la construction du site Jekyll.\n* Correction du chemin de copie des fichiers générés vers la racine du dépôt.",
          "timestamp": "2026-07-12T18:13:29+02:00",
          "tree_id": "a46aec009f326931f124a4cdb58d5cf20e5878f1",
          "url": "https://github.com/dorel14/whoosh-ng/commit/0d8af2e32e492273b15066c184e4409b88e192d4"
        },
        "date": 1783872855095,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1072.5068556505475,
            "unit": "iter/sec",
            "range": "stddev: 0.0000355828631124884",
            "extra": "mean: 932.3949723318391 usec\nrounds: 506"
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
          "id": "035a9827985347fad82a6305efc36b486dcd4cb8",
          "message": "chore: 🗑️ Suppression de la documentation obsolète\n\n* Suppression du fichier `README.md` qui n'est plus nécessaire.\n* Mise à jour de `_config.yml` pour exclure `README.md` du processus de construction.\n* Révision de `index.md` pour améliorer la structure et la clarté de la documentation.",
          "timestamp": "2026-07-12T18:20:49+02:00",
          "tree_id": "3a046c3ee70079ff201476cafd0b2ea3ef97d451",
          "url": "https://github.com/dorel14/whoosh-ng/commit/035a9827985347fad82a6305efc36b486dcd4cb8"
        },
        "date": 1783873292765,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1075.2422870896603,
            "unit": "iter/sec",
            "range": "stddev: 0.0000407853701504595",
            "extra": "mean: 930.0229464623111 usec\nrounds: 523"
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
          "id": "f29f078b2bec383e8316f0b61de6e7b58dbd861d",
          "message": "Merge branch 'dev' of https://github.com/dorel14/whoosh-ng into dev",
          "timestamp": "2026-07-12T18:29:53+02:00",
          "tree_id": "c58dbf8da86ddccb557068df5aa1a692207ecfbe",
          "url": "https://github.com/dorel14/whoosh-ng/commit/f29f078b2bec383e8316f0b61de6e7b58dbd861d"
        },
        "date": 1783873837409,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmark_async.py::test_run_sync_overhead",
            "value": 1065.770168365001,
            "unit": "iter/sec",
            "range": "stddev: 0.00002926184969431114",
            "extra": "mean: 938.2886007534823 usec\nrounds: 531"
          }
        ]
      }
    ]
  }
}