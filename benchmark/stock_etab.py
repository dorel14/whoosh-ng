import csv
import os

from benchmark import WhooshLikeSpec
from whoosh import analysis, fields


class StockEtab(WhooshLikeSpec):
    name = "stock_etab"
    main_field = "denomination"
    headline_field = "denomination"
    default_query = "SAINT-NAZAIRE"

    def whoosh_schema(self):
        return fields.Schema(
            siren=fields.ID(stored=True),
            nic=fields.ID(stored=True),
            siret=fields.ID(stored=True, unique=True),
            denomination=fields.TEXT(analyzer=analysis.StandardAnalyzer(), stored=True),
            libelle_commune=fields.TEXT(stored=True),
            libelle_pays=fields.TEXT(stored=True),
            activite_principale=fields.TEXT(stored=True),
            libelle_voie=fields.TEXT(stored=True),
            code_postal=fields.TEXT(stored=True),
            date_creation=fields.TEXT(stored=True),
        )

    def documents(self):
        basedir = os.path.join(self.options.dir, "stock_etab")
        path = os.path.join(basedir, "StockEtablissement_utf8.csv")
        count = 0
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield {
                    "siren": row["siren"],
                    "nic": row["nic"],
                    "siret": row["siret"],
                    "denomination": row["denominationUsuelleEtablissement"] or "",
                    "libelle_commune": row["libelleCommuneEtablissement"] or "",
                    "libelle_pays": row["libellePaysEtrangerEtablissement"] or "",
                    "activite_principale": row["activitePrincipaleEtablissement"] or "",
                    "libelle_voie": row["libelleVoieEtablissement"] or "",
                    "code_postal": row["codePostalEtablissement"] or "",
                    "date_creation": row["dateCreationEtablissement"] or "",
                }
                count += 1
                if self.options.upto and count >= int(self.options.upto):
                    break
