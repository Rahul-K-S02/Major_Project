"""
GeneRisk — ChromaDB Setup
==========================
Indexes medical knowledge into ChromaDB for RAG retrieval.
Run this ONCE before starting the cloud worker.

Usage: python data/setup_chromadb.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CHROMADB_PATH = "./data/chromadb"

# Curated medical knowledge for RAG
# In production: pull from OMIM API + PubMed Entrez API
MEDICAL_KNOWLEDGE = [
    {
        "id": "t2d_tcf7l2",
        "content": """TCF7L2 gene and Type 2 Diabetes: The rs7903146 variant in TCF7L2 is the 
strongest common genetic risk factor for Type 2 Diabetes in multiple populations. 
Each T allele increases risk by approximately 1.4-fold. The gene encodes transcription 
factor 7-like 2, which plays a critical role in the Wnt signalling pathway and affects 
pancreatic beta-cell function and insulin secretion. South Asian populations show 
particularly high risk due to TCF7L2 variants combined with lifestyle factors.""",
        "source": "ClinVar + GWAS Catalog",
        "disease": "type2_diabetes",
    },
    {
        "id": "t2d_prevention",
        "content": """Type 2 Diabetes Prevention: The Diabetes Prevention Program (DPP) showed 
that lifestyle intervention reduced diabetes incidence by 58% in high-risk individuals. 
Physical activity (150 min/week of moderate exercise) and 5-7% weight loss are key targets. 
Low glycemic index diet, Mediterranean diet, and DASH diet show protective effects. 
Metformin reduces risk by 31% in high-risk individuals. Annual HbA1c and fasting glucose 
screening recommended for those with elevated genetic risk.""",
        "source": "NEJM 2002, DPP Study",
        "disease": "type2_diabetes",
    },
    {
        "id": "cad_genetics",
        "content": """Coronary Artery Disease Genetics: The 9p21 locus (rs1333049, CDKN2B) 
increases CAD risk by 1.25-1.5x per allele, independently of traditional risk factors. 
LPA gene variants affecting Lipoprotein(a) levels are causal for CAD. South Asian 
populations have 3-4x higher CAD mortality than Europeans at the same age, partly due 
to genetic factors and partly due to metabolic syndrome. Statin therapy reduces CAD 
events by 25-35% regardless of baseline LDL cholesterol.""",
        "source": "Nature Genetics, Lancet",
        "disease": "coronary_artery_disease",
    },
    {
        "id": "brca_cancer",
        "content": """BRCA1 and BRCA2 Pathogenic Variants: BRCA1 mutations confer 50-72% 
lifetime breast cancer risk and 44% ovarian cancer risk. BRCA2 mutations confer 45-69% 
breast cancer risk. Annual MRI screening from age 25 recommended. Risk-reducing 
salpingo-oophorectomy reduces ovarian cancer risk by >96% and breast cancer risk by 
~50%. Prophylactic mastectomy reduces breast cancer risk by 90-95%. Tamoxifen or 
raloxifene chemoprevention may be considered. Genetic counselling mandatory.""",
        "source": "NCCN Guidelines 2025",
        "disease": "breast_cancer",
    },
    {
        "id": "apoe_alzheimers",
        "content": """APOE and Alzheimer's Disease: APOE e4 allele (rs429358) is the strongest 
genetic risk factor for late-onset Alzheimer's. One copy increases risk 3-4x; two copies 
increase risk 8-12x compared to APOE e3/e3. Risk varies by age and sex: women with 
APOE e4 have higher lifetime risk than men. Mediterranean diet, physical exercise, 
cognitive engagement, and sleep hygiene reduce risk. New anti-amyloid therapies 
(lecanemab, donanemab) show promise in APOE e4 carriers.""",
        "source": "JAMA Neurology 2024",
        "disease": "alzheimers",
    },
    {
        "id": "hypertension_genetics",
        "content": """Hypertension Genetics: Blood pressure is highly polygenic. Key genes 
include AGT, ACE, MTHFR, and NOS3. MTHFR C677T variant affects homocysteine metabolism 
and vascular function. Lifestyle interventions: DASH diet reduces BP by 8-14 mmHg, 
sodium restriction by 2-8 mmHg, aerobic exercise by 4-9 mmHg, weight loss by 5-20 mmHg 
per 10kg. First-line medications: ACE inhibitors, ARBs, thiazide diuretics. Target 
<130/80 mmHg for high-risk individuals.""",
        "source": "AHA Guidelines 2023",
        "disease": "hypertension",
    },
    {
        "id": "indian_genomics",
        "content": """Indian Population Genomic Considerations: South Asian populations 
(Indian, Pakistani, Sri Lankan) show distinct allele frequencies compared to European 
GWAS reference populations. T2D risk is 3-5x higher in South Asians. GWAS effect 
sizes estimated in Europeans may underestimate or overestimate risk in Indians. 
Indian Genome Variation Consortium (IGVC) provides South Asian reference data. 
Thalassemia, G6PD deficiency, and sickle cell trait are prevalent in specific 
Indian sub-populations. Population-stratified PRS models improve accuracy.""",
        "source": "Indian Genome Variation Consortium",
        "disease": "general",
    },
]


def setup_chromadb():
    """Create and populate ChromaDB vector store."""
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain.schema import Document
    except ImportError:
        print("[SETUP] LangChain not installed. Run: pip install langchain langchain-community")
        return

    print("[SETUP] Loading embedding model (all-MiniLM-L6-v2)...")
    print("[SETUP] First run downloads ~90MB model — this is normal...")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Convert to LangChain documents
    docs = [
        Document(
            page_content=item["content"],
            metadata={
                "source": item["source"],
                "disease": item["disease"],
                "id": item["id"],
            },
        )
        for item in MEDICAL_KNOWLEDGE
    ]

    print(f"[SETUP] Indexing {len(docs)} medical knowledge documents...")

    os.makedirs(CHROMADB_PATH, exist_ok=True)
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMADB_PATH,
    )
    vectorstore.persist()

    print(f"[SETUP] ChromaDB created at: {CHROMADB_PATH}")

    # Test retrieval
    print("\n[SETUP] Testing retrieval...")
    results = vectorstore.similarity_search("TCF7L2 diabetes risk", k=2)
    for r in results:
        print(f"  Found: {r.metadata['id']} — {r.page_content[:80]}...")

    print("\n[SETUP] ChromaDB setup complete!")


if __name__ == "__main__":
    print("=" * 50)
    print("GeneRisk — ChromaDB Knowledge Base Setup")
    print("=" * 50)
    setup_chromadb()
