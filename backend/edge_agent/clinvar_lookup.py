"""
GeneRisk — ClinVar Local Lookup
================================
Queries the local SQLite ClinVar database for SNP annotations.
Runs on edge (user's machine) — no internet required.
"""
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()

CLINVAR_DB = os.getenv("CLINVAR_DB_PATH", "./data/clinvar.db")

# Hardcoded fallback for when DB not downloaded yet
FALLBACK_ANNOTATIONS = {
    "rs7903146":  {"gene": "TCF7L2",  "significance": "risk factor",      "condition": "Type 2 Diabetes",          "review": "reviewed by expert panel"},
    "rs5219":     {"gene": "KCNJ11",  "significance": "risk factor",      "condition": "Type 2 Diabetes",          "review": "criteria provided"},
    "rs10811661": {"gene": "CDKN2A",  "significance": "risk factor",      "condition": "Type 2 Diabetes",          "review": "criteria provided"},
    "rs4607517":  {"gene": "GCK",     "significance": "risk factor",      "condition": "Type 2 Diabetes",          "review": "criteria provided"},
    "rs1333049":  {"gene": "CDKN2B",  "significance": "risk factor",      "condition": "Coronary artery disease",  "review": "criteria provided"},
    "rs80357906": {"gene": "BRCA1",   "significance": "Pathogenic",       "condition": "Hereditary breast cancer", "review": "reviewed by expert panel"},
    "rs80359550": {"gene": "BRCA2",   "significance": "Pathogenic",       "condition": "Hereditary breast cancer", "review": "reviewed by expert panel"},
    "rs429358":   {"gene": "APOE",    "significance": "risk factor",      "condition": "Alzheimer disease",        "review": "reviewed by expert panel"},
    "rs17367504": {"gene": "MTHFR",   "significance": "risk factor",      "condition": "Hypertension",             "review": "criteria provided"},
}


class ClinVarLookup:
    """Query local ClinVar SQLite for SNP clinical significance."""

    def __init__(self):
        self.db_path = CLINVAR_DB
        self.db_available = os.path.exists(self.db_path)
        if not self.db_available:
            print("[ClinVar] Local DB not found — using built-in fallback annotations.")
            print("[ClinVar] Run: python data/setup_clinvar.py   to download full database.")

    def lookup(self, rs_id: str) -> dict:
        """Return ClinVar annotation for a single rs-ID."""
        if self.db_available:
            return self._query_db(rs_id)
        return FALLBACK_ANNOTATIONS.get(rs_id, {
            "gene": "Unknown", "significance": "Uncertain significance",
            "condition": "Not specified", "review": "no assertion"
        })

    def lookup_batch(self, rs_ids: list) -> dict:
        """Return annotations for a list of rs-IDs. Returns {rs_id: annotation}."""
        results = {}
        if self.db_available:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                placeholders = ",".join("?" * len(rs_ids))
                cursor.execute(f"""
                    SELECT rs_id, gene_name, clinical_significance, condition_name, review_status
                    FROM clinvar_variants WHERE rs_id IN ({placeholders})
                """, rs_ids)
                for row in cursor.fetchall():
                    results[row[0]] = {
                        "gene": row[1], "significance": row[2],
                        "condition": row[3], "review": row[4]
                    }
                conn.close()
                return results
            except Exception as e:
                print(f"[ClinVar] DB query error: {e}")

        # fallback
        for rs_id in rs_ids:
            results[rs_id] = FALLBACK_ANNOTATIONS.get(rs_id, {
                "gene": "Unknown", "significance": "Uncertain significance",
                "condition": "Not specified", "review": "no assertion"
            })
        return results

    def _query_db(self, rs_id: str) -> dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT gene_name, clinical_significance, condition_name, review_status
                FROM clinvar_variants WHERE rs_id = ? LIMIT 1
            """, (rs_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"gene": row[0], "significance": row[1], "condition": row[2], "review": row[3]}
        except Exception as e:
            print(f"[ClinVar] Lookup error for {rs_id}: {e}")
        return FALLBACK_ANNOTATIONS.get(rs_id, {"gene": "Unknown", "significance": "Unknown", "condition": "Unknown", "review": "none"})


if __name__ == "__main__":
    cl = ClinVarLookup()
    test_ids = ["rs7903146", "rs429358", "rs80357906"]
    results = cl.lookup_batch(test_ids)
    for rs_id, info in results.items():
        print(f"{rs_id}: {info['gene']} — {info['significance']} — {info['condition']}")
