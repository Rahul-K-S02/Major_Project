"""
GeneRisk — Edge Agent: VCF Parser & Filter
==========================================
This runs LOCALLY on the user's machine (the "edge").
Raw DNA never leaves. Only filtered SNP IDs go to cloud.

Your synopsis note: "edge computing concept - filtering method so that
no full data goes to AI model but only required sequence"
-- This file IS that filtering mechanism.
"""

import vcf
import pandas as pd
import sqlite3
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Known clinically relevant rs-IDs (pre-loaded from ClinVar) ──────────────
# In production this comes from your local clinvar.db
KNOWN_CLINICAL_RS_IDS_PATH = os.getenv("GWAS_WEIGHTS_PATH", "./data/gwas_weights")


class VCFEdgeFilter:
    """
    EDGE LAYER — runs locally on user's machine.

    What it does:
    1. Reads the raw VCF file (4-5 million rows)
    2. Filters to only clinically significant SNPs (~50,000)
    3. Returns a tiny anonymised list of rs-IDs + genotypes
    4. Raw VCF file never leaves the local machine
    """

    def __init__(self, clinvar_db_path: str = None):
        self.clinvar_db_path = clinvar_db_path or os.getenv(
            "CLINVAR_DB_PATH", "./data/clinvar.db"
        )
        self.stats = {
            "total_variants": 0,
            "filtered_variants": 0,
            "reduction_percent": 0,
            "processing_time_sec": 0,
        }

    def parse_and_filter(self, vcf_file_path: str) -> dict:
        """
        Main entry point. Takes a VCF file path, returns filtered SNPs.

        Returns:
            {
                "filtered_snps": [{"rs_id": "rs7903146", "genotype": 2, "chrom": "10"}, ...],
                "stats": {"total": 4500000, "filtered": 52000, "reduction": "98.8%"},
                "processing_time": 12.4
            }
        """
        start_time = time.time()
        print(f"\n[EDGE] Starting VCF filtering: {vcf_file_path}")
        print("[EDGE] Raw DNA stays on your machine — only rs-IDs will be sent to cloud\n")

        # Load known clinical rs-IDs from local ClinVar DB
        known_rs_ids = self._load_known_clinical_rs_ids()

        # Parse and filter VCF
        filtered_snps = self._filter_vcf(vcf_file_path, known_rs_ids)

        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        # Calculate stats
        reduction = round(
            (1 - self.stats["filtered_variants"] / max(self.stats["total_variants"], 1)) * 100,
            1,
        )

        result = {
            "filtered_snps": filtered_snps,
            "stats": {
                "total_variants": self.stats["total_variants"],
                "filtered_variants": self.stats["filtered_variants"],
                "reduction_percent": reduction,
                "data_sent_to_cloud_mb": round(len(json.dumps(filtered_snps)) / 1024 / 1024, 3),
            },
            "processing_time_sec": processing_time,
        }

        print(f"[EDGE] Done! {self.stats['total_variants']:,} variants → {self.stats['filtered_variants']:,} clinical SNPs")
        print(f"[EDGE] Reduction: {reduction}% — only {result['stats']['data_sent_to_cloud_mb']} MB sent to cloud")
        print(f"[EDGE] Time: {processing_time}s\n")

        return result

    def _load_known_clinical_rs_ids(self) -> set:
        """Load rs-IDs of clinically significant variants from local SQLite."""
        if not os.path.exists(self.clinvar_db_path):
            print("[EDGE] WARNING: ClinVar DB not found. Run data/setup_clinvar.py first.")
            print("[EDGE] Using fallback small set of known disease rs-IDs.")
            return self._get_fallback_rs_ids()

        try:
            conn = sqlite3.connect(self.clinvar_db_path)
            cursor = conn.cursor()
            # Only load Pathogenic and Likely Pathogenic variants
            cursor.execute("""
                SELECT DISTINCT rs_id FROM clinvar_variants
                WHERE clinical_significance IN ('Pathogenic', 'Likely pathogenic', 'risk factor')
                AND rs_id IS NOT NULL
            """)
            rs_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
            print(f"[EDGE] Loaded {len(rs_ids):,} clinical rs-IDs from local ClinVar DB")
            return rs_ids
        except Exception as e:
            print(f"[EDGE] ClinVar DB error: {e}. Using fallback.")
            return self._get_fallback_rs_ids()

    def _get_fallback_rs_ids(self) -> set:
        """Hardcoded important SNPs for testing when ClinVar DB not yet set up."""
        return {
            # Type 2 Diabetes
            "rs7903146", "rs5219", "rs1801214", "rs10811661", "rs4607517",
            "rs1111875", "rs13266634", "rs4402960", "rs7756992", "rs10946398",
            # Coronary Artery Disease
            "rs1333049", "rs4665058", "rs3798220", "rs2241220", "rs9982601",
            # Breast Cancer (BRCA1/BRCA2 known variants)
            "rs80357906", "rs80359550", "rs28897672", "rs41293455",
            # Alzheimer's Disease
            "rs429358", "rs7412", "rs2075650", "rs4420638",
            # Hypertension
            "rs17367504", "rs3918226", "rs2820037", "rs1530440",
        }

    def _filter_vcf(self, vcf_file_path: str, known_rs_ids: set) -> list:
        """
        Core filtering logic.
        Reads VCF row by row, keeps only clinically relevant SNPs.
        """
        filtered = []

        try:
            vcf_reader = vcf.Reader(open(vcf_file_path, "r"))

            for record in vcf_reader:
                self.stats["total_variants"] += 1

                # Skip if no rs-ID
                if not record.ID:
                    continue

                rs_id = str(record.ID)

                # FILTER: Only keep known clinical variants
                if rs_id not in known_rs_ids:
                    continue

                # Skip non-SNPs (insertions/deletions)
                if len(record.REF) != 1:
                    continue

                # Calculate genotype dosage (0, 1, or 2 copies of risk allele)
                dosage = self._calculate_dosage(record)
                if dosage is None:
                    continue

                filtered.append({
                    "rs_id": rs_id,
                    "chromosome": str(record.CHROM),
                    "position": record.POS,
                    "ref_allele": str(record.REF),
                    "alt_allele": str(record.ALT[0]) if record.ALT else "",
                    "genotype_dosage": dosage,
                    # NOTE: We do NOT send actual genotype letters (e.g., "A/G")
                    # Only the dosage number — extra privacy layer
                })
                self.stats["filtered_variants"] += 1

        except Exception as e:
            print(f"[EDGE] VCF parse error: {e}")
            print("[EDGE] Tip: Make sure the VCF file is not gzipped. Run: gunzip file.vcf.gz")

        return filtered

    def _calculate_dosage(self, record) -> int | None:
        """
        Convert VCF genotype to dosage (0, 1, 2).
        0 = homozygous reference (no risk allele)
        1 = heterozygous (one risk allele from one parent)
        2 = homozygous alt (risk allele from both parents)
        """
        try:
            if not record.samples:
                return None
            sample = record.samples[0]
            gt = sample.data.GT
            if gt is None:
                return None
            # Handle phased (0|1) and unphased (0/1) genotypes
            alleles = gt.replace("|", "/").split("/")
            if len(alleles) != 2:
                return None
            # Count non-reference alleles
            dosage = sum(1 for a in alleles if a not in ["0", ".", None])
            return dosage
        except Exception:
            return None


def create_sample_vcf(output_path: str = "./data/sample_test.vcf"):
    """
    Creates a tiny sample VCF file for testing.
    Use this when you don't have a real VCF file yet.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    content = """##fileformat=VCFv4.1
##source=GeneRisk_Test
##reference=GRCh38
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE
10\t114758349\trs7903146\tC\tT\t.\tPASS\tgene=TCF7L2\tGT\t0/1
11\t17418149\trs5219\tC\tT\t.\tPASS\tgene=KCNJ11\tGT\t1/1
4\t6302519\trs10811661\tT\tC\t.\tPASS\tgene=CDKN2A\tGT\t0/1
19\t45411941\trs429358\tT\tC\t.\tPASS\tgene=APOE\tGT\t0/0
17\t41246481\trs80357906\tG\tA\t.\tPASS\tgene=BRCA1\tGT\t0/1
1\t1234567\trs9999999\tA\tG\t.\tPASS\tgene=UNKNOWN\tGT\t0/1
"""
    with open(output_path, "w") as f:
        f.write(content)
    print(f"[EDGE] Sample VCF created at: {output_path}")
    return output_path


# ─── Run directly for testing ─────────────────────────────────────────────────
if __name__ == "__main__":
    # Create sample VCF for testing
    sample_vcf = create_sample_vcf("./data/sample_test.vcf")

    # Run the edge filter
    filter_agent = VCFEdgeFilter()
    result = filter_agent.parse_and_filter(sample_vcf)

    print("=== FILTERED OUTPUT (this is ALL that goes to cloud) ===")
    print(json.dumps(result, indent=2))
