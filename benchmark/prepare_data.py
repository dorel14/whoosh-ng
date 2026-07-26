"""Prepare benchmark data files.

Usage:
    python benchmark/prepare_data.py

This script downloads and prepares the required benchmark data files into
benchmark/customers-2000000/ and benchmark/stock_etab/. It is intended
to be run before benchmarks in CI or on a fresh checkout.
"""

from __future__ import annotations

import argparse
import csv
import os
import zipfile
from urllib.request import urlretrieve


CUSTOMERS_DST = os.path.join("benchmark", "customers-2000000", "customers-2000000.csv")
CUSTOMERS_ZIP = os.path.join("benchmark", "customers-2000000", "customers-2000000.zip")
STOCK_DST = os.path.join("benchmark", "stock_etab", "StockEtablissement_utf8.csv")
STOCK_ZIP = os.path.join("benchmark", "stock_etab", "StockEtablissement_utf8.zip")


def download(url: str, dst: str, label: str) -> bool:
    if os.path.exists(dst):
        print(f"  {label} already present: {dst}")
        return True
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print(f"  Downloading {label} from {url}")
    try:
        urlretrieve(url, dst)
        print(f"  Downloaded to {dst}")
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def extract_zip(zip_path: str, dst: str) -> bool:
    if os.path.exists(dst):
        print(f"  CSV already present: {dst}")
        return True
    if not os.path.exists(zip_path):
        print(f"  Zip not found: {zip_path}")
        return False
    print(f"  Extracting {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            for name in z.namelist():
                if name.lower().endswith(".csv"):
                    z.extract(name, os.path.dirname(dst))
                    extracted = os.path.join(os.path.dirname(dst), name)
                    if extracted != dst:
                        os.replace(extracted, dst)
                    print(f"  Extracted CSV to {dst}")
                    return True
        print("  No CSV found in zip")
        return False
    except Exception as e:
        print(f"  Extraction failed: {e}")
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare benchmark data files")
    parser.add_argument(
        "--customers-url",
        default=os.environ.get("CUSTOMERS_URL", ""),
        help="URL to download customers-2000000.csv from (env: CUSTOMERS_URL)",
    )
    parser.add_argument(
        "--stock-url",
        default=os.environ.get(
            "STOCK_URL",
            "https://www.data.gouv.fr/api/1/datasets/r/0651fb76-bcf3-4f6a-a38d-bc04fa708576",
        ),
        help="URL to download StockEtablissement_utf8.csv zip from (env: STOCK_URL)",
    )
    parser.add_argument(
        "--customers-max-rows",
        type=int,
        default=0,
        help="If >0, truncate customers CSV to this many rows for lighter CI runs",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    ok = True
    print("Preparing benchmark data...")

    if args.customers_url:
        if not download(args.customers_url, CUSTOMERS_ZIP, "customers ZIP"):
            ok = False
        else:
            if not extract_zip(CUSTOMERS_ZIP, CUSTOMERS_DST):
                ok = False
    else:
        if not os.path.exists(CUSTOMERS_DST):
            print("  customers CSV not provided and not present locally")
            ok = False
        else:
            print(f"  customers CSV present: {CUSTOMERS_DST}")

    if not download(args.stock_url, STOCK_ZIP, "stock_etab ZIP"):
        ok = False
    else:
        if not extract_zip(STOCK_ZIP, STOCK_DST):
            ok = False

    if not ok:
        print(
            "Some benchmark data files are missing. "
            "Provide --customers-url or place files manually."
        )
        return 1

    if args.customers_max_rows > 0 and os.path.exists(CUSTOMERS_DST):
        print(f"Truncating customers CSV to {args.customers_max_rows} rows")
        tmp = CUSTOMERS_DST + ".tmp"
        with (
            open(CUSTOMERS_DST, newline="", encoding="utf-8") as fin,
            open(tmp, "w", newline="", encoding="utf-8") as fout,
        ):
            reader = csv.DictReader(fin)
            writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
            writer.writeheader()
            for i, row in enumerate(reader):
                if i >= args.customers_max_rows:
                    break
                writer.writerow(row)
        os.replace(tmp, CUSTOMERS_DST)
        print(f"  Truncated customers CSV written to {CUSTOMERS_DST}")

    print("Benchmark data ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
