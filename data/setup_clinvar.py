"""
GeneRisk — ClinVar SQLite Setup
================================
Run this ONCE to download ClinVar and load into SQLite.
This creates the local database for offline SNP lookups.

Usage: python data/setup_clinvar.py
Time: ~5-10 minutes (downloads ~100MB compressed file)
"""

import os
import sqlite3
import gzip
import csv
import requests
import time

CLINVAR_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"
DB_PATH = "./data/clinvar.db"
GZ_PATH = "./data/variant_summary.txt.gz"
TXT_PATH = "./data/variant_summary.txt"


def download_clinvar():
    """Download ClinVar variant summary file."""
    os.makedirs("./data", exist_ok=True)

    if os.path.exists(TXT_PATH):
        print(f"[SETUP] ClinVar file already exists at {TXT_PATH}")
        return

    print("[SETUP] Downloading ClinVar variant summary (~100MB)...")
    print("[SETUP] This takes 3-5 minutes depending on your internet speed...")

    response = requests.get(CLINVAR_URL, stream=True)
    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(GZ_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = int(downloaded / total * 100)
                print(f"\r[SETUP] Downloading: {pct}%", end="", flush=True)

    print("\n[SETUP] Download complete. Extracting...")
    with gzip.open(GZ_PATH, "rb") as gz:
        with open(TXT_PATH, "wb") as txt:
            txt.write(gz.read())

    os.remove(GZ_PATH)
    print("[SETUP] Extraction complete.")


def load_into_sqlite():
    """Load ClinVar TSV into SQLite database."""
    print(f"\n[SETUP] Loading ClinVar into SQLite: {DB_PATH}")
    print("[SETUP] This takes 2-3 minutes...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute("DROP TABLE IF EXISTS clinvar_variants")
    cursor.execute("""
        CREATE TABLE clinvar_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rs_id TEXT,
            gene_name TEXT,
            clinical_significance TEXT,
            condition_name TEXT,
            chromosome TEXT,
            start_pos INTEGER,
            ref_allele TEXT,
            alt_allele TEXT,
            review_status TEXT,
            origin TEXT
        )
    """)

    # Create index for fast rs-ID lookups
    cursor.execute("CREATE INDEX idx_rs_id ON clinvar_variants (rs_id)")

    # Load data
    count = 0
    skip = 0

    with open(TXT_PATH, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            rs_id = row.get("RS# (dbSNP)", "").strip()

            # Only load rows with valid rs-IDs
            if not rs_id or rs_id == "-1" or rs_id == "":
                skip += 1
                continue

            rs_id = f"rs{rs_id}"

            cursor.execute("""
                INSERT INTO clinvar_variants 
                (rs_id, gene_name, clinical_significance, condition_name,
                 chromosome, start_pos, ref_allele, alt_allele, review_status, origin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rs_id,
                row.get("GeneSymbol", ""),
                row.get("ClinicalSignificance", ""),
                row.get("PhenotypeList", ""),
                row.get("Chromosome", ""),
                int(row.get("Start", 0) or 0),
                row.get("ReferenceAllele", ""),
                row.get("AlternateAllele", ""),
                row.get("ReviewStatus", ""),
                row.get("Origin", ""),
            ))

            count += 1
            if count % 50000 == 0:
                conn.commit()
                print(f"\r[SETUP] Loaded {count:,} variants...", end="", flush=True)

    conn.commit()
    conn.close()

    print(f"\n[SETUP] Done! Loaded {count:,} variants into {DB_PATH}")
    print(f"[SETUP] Skipped {skip:,} variants without rs-IDs")

    size_mb = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"[SETUP] Database size: {size_mb:.1f} MB")


def test_database():
    """Quick test to verify the database works."""
    print("\n[SETUP] Testing database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Test known rs-ID
    cursor.execute(
        "SELECT rs_id, gene_name, clinical_significance, condition_name FROM clinvar_variants WHERE rs_id = ?",
        ("rs7903146",)
    )
    row = cursor.fetchone()
    if row:
        print(f"[SETUP] Test query OK: {row}")
    else:
        print("[SETUP] rs7903146 not found — database may need reloading")

    cursor.execute("SELECT COUNT(*) FROM clinvar_variants")
    count = cursor.fetchone()[0]
    print(f"[SETUP] Total variants in DB: {count:,}")
    conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("GeneRisk — ClinVar Database Setup")
    print("=" * 50)
    download_clinvar()
    load_into_sqlite()
    test_database()
    print("\n[SETUP] ClinVar setup complete! You can now run the main project.")
