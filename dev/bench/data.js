window.BENCHMARK_DATA = {
  "lastUpdate": 1783781679838,
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
      }
    ]
  }
}