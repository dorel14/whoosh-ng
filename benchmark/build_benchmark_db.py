"""Build SQLite benchmark database from existing benchmark data files."""

from __future__ import annotations

import gzip
import os
import sqlite3
from datetime import datetime


def build_reuters_table(conn: sqlite3.Connection, path: str) -> int:
    """Build reuters_articles table from reuters21578.txt."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reuters_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_date TEXT,
            headline TEXT,
            body TEXT,
            word_count INTEGER
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reuters_date ON reuters_articles(article_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reuters_headline ON reuters_articles(headline)")

    count = 0
    with open(path, encoding="latin-1") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) < 2:
                continue
            article_date = parts[0].strip()
            body = parts[1].strip()
            headline = body[:70].replace("\n", " ")
            word_count = len(body.split())
            cursor.execute(
                "INSERT INTO reuters_articles "
                "(article_date, headline, body, word_count) "
                "VALUES (?, ?, ?, ?)",
                (article_date, headline, body, word_count),
            )
            count += 1
    conn.commit()
    return count


def build_dictionary_table(conn: sqlite3.Connection, path: str) -> int:
    """Build dictionary_entries table from dcvgr10.txt."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dictionary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            head TEXT,
            body TEXT,
            word_count INTEGER
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dict_head ON dictionary_entries(head)")

    head = ""
    body = ""
    count = 0

    with open(path, encoding="latin-1") as f:
        for line in f:
            line = line.rstrip("\n")
            if line and line[0].isalpha():
                if head:
                    cursor.execute(
                        "INSERT INTO dictionary_entries (head, body, word_count) VALUES (?, ?, ?)",
                        (head, body, len(body.split())),
                    )
                    count += 1
                parts = line.split(".", 1)
                head = parts[0].strip()
                body = line + "\n"
            else:
                body += line + "\n"

    if head:
        cursor.execute(
            "INSERT INTO dictionary_entries (head, body, word_count) VALUES (?, ?, ?)",
            (head, body, len(body.split())),
        )
        count += 1

    conn.commit()
    return count


def build_customers_table(conn: sqlite3.Connection, csv_path: str) -> int:
    """Build customers table from customers CSV if available."""
    import csv as csv_mod

    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            company TEXT,
            city TEXT,
            country TEXT,
            email TEXT,
            subscription_date TEXT,
            website TEXT
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country)")

    if not os.path.exists(csv_path):
        return 0

    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        for row in reader:
            cursor.execute(
                "INSERT OR REPLACE INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row.get("Customer Id", ""),
                    row.get("First Name", ""),
                    row.get("Last Name", ""),
                    row.get("Company", ""),
                    row.get("City", ""),
                    row.get("Country", ""),
                    row.get("Email", ""),
                    row.get("Subscription Date", ""),
                    row.get("Website", ""),
                ),
            )
            count += 1
    conn.commit()
    return count


def build_stock_table(conn: sqlite3.Connection, csv_path: str) -> int:
    """Build stock_etablissements table from stock CSV if available."""
    import csv as csv_mod

    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_etablissements (
            siren TEXT,
            siret TEXT,
            nic TEXT,
            statut TEXT,
            date_creation TEXT,
            libelle_activite TEXT,
            libelle_niveau TEXT,
            code_commune TEXT,
            libelle_commune TEXT,
            code_departement TEXT,
            libelle_departement TEXT,
            code_region TEXT,
            libelle_region TEXT
        )
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_stock_commune ON stock_etablissements(libelle_commune)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_stock_departement "
        "ON stock_etablissements(libelle_departement)"
    )

    if not os.path.exists(csv_path):
        return 0

    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        for row in reader:
            cursor.execute(
                """INSERT INTO stock_etablissements "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row.get("siren", ""),
                    row.get("siret", ""),
                    row.get("nic", ""),
                    row.get("statut", ""),
                    row.get("dateCreation", ""),
                    row.get("libelleActivitePrincipale", ""),
                    row.get("libelleNiveau", ""),
                    row.get("codeCommune", ""),
                    row.get("libelleCommune", ""),
                    row.get("codeDepartement", ""),
                    row.get("libelleDepartement", ""),
                    row.get("codeRegion", ""),
                    row.get("libelleRegion", ""),
                ),
            )
            count += 1
    conn.commit()
    return count


def main() -> int:
    benchmark_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(benchmark_dir, "benchmark_data.db")

    if os.path.exists(db_path):
        print(f"Benchmark database already exists: {db_path}")
        return 0

    conn = sqlite3.connect(db_path)
    print(f"Building benchmark database: {db_path}")

    # Reuters articles
    reuters_path = os.path.join(benchmark_dir, "reuters21578.txt")
    if os.path.exists(reuters_path):
        count = build_reuters_table(conn, reuters_path)
        print(f"  reuters_articles: {count} rows")
    else:
        print("  reuters21578.txt not found, skipping")

    # Dictionary entries
    dict_path = os.path.join(benchmark_dir, "dcvgr10.txt")
    if os.path.exists(dict_path):
        count = build_dictionary_table(conn, dict_path)
        print(f"  dictionary_entries: {count} rows")
    else:
        print("  dcvgr10.txt not found, skipping")

    # Customers CSV
    customers_csv = os.path.join(benchmark_dir, "customers-2000000", "customers-2000000.csv")
    count = build_customers_table(conn, customers_csv)
    print(f"  customers: {count} rows")

    # Stock etablissements CSV
    stock_csv = os.path.join(benchmark_dir, "stock_etab", "StockEtablissement_utf8.csv")
    count = build_stock_table(conn, stock_csv)
    print(f"  stock_etablissements: {count} rows")

    conn.close()
    print("Benchmark database ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
