"""Prebuilt synonym dictionaries for FR/EN/DE/ES/IT.

These are minimal starter dictionaries for demonstration and testing.
Production deployments should load from compact-dictionaries or curated sources.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

LANG_SYNONYMS: dict[str, dict[str, list[str]]] = {
    "fr": {
        "voiture": ["automobile", "véhicule"],
        "ordinateur": ["pc", "machine"],
        "maison": ["domicile", "résidence"],
        "livre": ["ouvrage", "bouquin"],
        "travail": ["emploi", "job"],
    },
    "en": {
        "car": ["automobile", "vehicle"],
        "house": ["home", "residence"],
        "computer": ["pc", "machine"],
        "book": ["publication", "work"],
        "job": ["employment", "work"],
    },
    "de": {
        "auto": ["wagen", "fahrzeug"],
        "haus": ["wohnung", "gebäude"],
        "buch": ["werk", "publikation"],
        "arbeit": ["job", "beruf"],
    },
    "es": {
        "coche": ["automóvil", "vehículo"],
        "casa": ["hogar", "residencia"],
        "libro": ["obra", "publicación"],
        "trabajo": ["empleo", "ocupación"],
    },
    "it": {
        "auto": ["automobile", "veicolo"],
        "casa": ["abitazione", "residenza"],
        "libro": ["opera", "pubblicazione"],
        "lavoro": ["impiego", "occupazione"],
    },
}

__all__ = ["LANG_SYNONYMS"]
