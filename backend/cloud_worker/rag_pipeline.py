"""
GeneRisk — RAG Pipeline
=======================
Retrieval-Augmented Generation using:
- ChromaDB (vector store of OMIM + PubMed summaries)
- sentence-transformers (embeddings)
- LLaMA 3 via Groq (free LLM)
- LangChain (orchestration)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Lazy imports (don't fail if libraries not installed yet) ─────────────────
try:
    from langchain_groq import ChatGroq
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[RAG] LangChain not installed. Run: pip install langchain langchain-groq langchain-community")


# ─── Fallback knowledge base (used when ChromaDB not set up yet) ──────────────
FALLBACK_KNOWLEDGE = {
    "type2_diabetes": """
Type 2 Diabetes is influenced by variants in TCF7L2, KCNJ11, and PPARG genes.
TCF7L2 (rs7903146) is the strongest genetic risk factor, increasing risk by 1.4x per allele.
Lifestyle interventions including diet modification and physical activity reduce risk by 58%
even in high genetic risk individuals (Diabetes Prevention Program, 2002).
Metformin is first-line pharmacotherapy. HbA1c screening recommended annually.
""",
    "coronary_artery_disease": """
Coronary artery disease (CAD) has strong genetic components in CDKN2B, LPA, and APOB genes.
The 9p21 locus (rs1333049) increases CAD risk independently of traditional risk factors.
Statins are highly effective in high-risk individuals. Regular lipid screening recommended.
Lifestyle modification: Mediterranean diet, aerobic exercise, smoking cessation.
""",
    "breast_cancer": """
BRCA1 and BRCA2 mutations confer 50-85% lifetime risk of breast cancer.
Annual MRI screening recommended for BRCA1/2 carriers from age 25.
Prophylactic mastectomy reduces risk by >90%. Tamoxifen chemoprevention available.
Regular self-examination and clinical breast exam every 6 months recommended.
""",
    "alzheimers": """
APOE e4 allele (rs429358) is the strongest genetic risk factor for late-onset Alzheimer's.
One copy increases risk 3-4x; two copies increase risk 8-12x.
Physical exercise, cognitive engagement, and Mediterranean diet show protective effects.
Current treatments are symptomatic. Early screening allows lifestyle interventions.
""",
    "hypertension": """
Hypertension has polygenic basis with variants in MTHFR, NOS3, and AGT genes.
Lifestyle modifications: DASH diet, sodium restriction (<2.3g/day), aerobic exercise.
First-line medications: ACE inhibitors, ARBs, thiazide diuretics, calcium channel blockers.
Target BP: <130/80 mmHg. Home monitoring recommended for high-risk individuals.
""",
}


class RAGPipeline:
    """
    Semi-agentic RAG pipeline for genomic report generation.
    Falls back to curated knowledge if ChromaDB not set up.
    """

    def __init__(self):
        self.chromadb_path = os.getenv("CHROMADB_PATH", "./data/chromadb")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.vectorstore = None
        self.llm = None
        self._initialize()

    def _initialize(self):
        """Initialize LLM and vector store."""
        # Initialize Groq LLM
        if self.groq_api_key and LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatGroq(
                    api_key=self.groq_api_key,
                    model_name=self.model_name,
                    temperature=0.1,
                    max_tokens=2000,
                )
                print("[RAG] Groq LLM initialized successfully")
            except Exception as e:
                print(f"[RAG] Groq init failed: {e}")
        else:
            print("[RAG] No GROQ_API_KEY found. Add it to .env file")

        # Initialize ChromaDB (optional)
        if LANGCHAIN_AVAILABLE and os.path.exists(self.chromadb_path):
            try:
                embeddings = HuggingFaceEmbeddings(
                    model_name="all-MiniLM-L6-v2",
                    model_kwargs={"device": "cpu"},
                )
                self.vectorstore = Chroma(
                    persist_directory=self.chromadb_path,
                    embedding_function=embeddings,
                )
                print("[RAG] ChromaDB loaded successfully")
            except Exception as e:
                print(f"[RAG] ChromaDB load failed: {e}. Using fallback knowledge.")
        else:
            print("[RAG] ChromaDB not found. Using built-in knowledge base.")

    def retrieve_evidence(self, disease: str, query: str = None) -> str:
        """Retrieve relevant research evidence for a disease."""
        if self.vectorstore:
            search_query = query or f"{disease} genetic risk treatment prevention"
            try:
                docs = self.vectorstore.similarity_search(search_query, k=3)
                return "\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                print(f"[RAG] Retrieval failed: {e}. Using fallback.")

        # Fallback to built-in knowledge
        return FALLBACK_KNOWLEDGE.get(disease, f"General information about {disease}.")

    def generate_disease_explanation(
        self,
        disease: str,
        prs_data: dict,
        shap_text: str,
        evidence: str,
        user_profile: dict = None,
    ) -> str:
        """
        Generate a plain-English explanation for one disease.
        Uses LLM with RAG context to avoid hallucination.
        """
        age = user_profile.get("age", "unknown") if user_profile else "unknown"
        sex = user_profile.get("sex", "unknown") if user_profile else "unknown"

        prompt = f"""You are a genetic counsellor assistant. Explain the following genomic risk 
finding to a patient in clear, simple English. Be accurate, empathetic, and helpful.

PATIENT PROFILE:
- Age: {age}, Sex: {sex}
- Disease assessed: {disease.replace("_", " ").title()}

GENETIC RISK FINDING:
- Risk level: {prs_data.get("risk_level", "Unknown")}
- Risk multiplier: {prs_data.get("risk_multiplier", 1.0)}x population average
- Gene contributions: {shap_text}

EVIDENCE FROM RESEARCH:
{evidence}

INSTRUCTIONS:
1. Explain what this risk finding means in 2-3 sentences (no medical jargon)
2. Mention the top contributing gene and why it matters
3. Give 3 specific, evidence-based lifestyle recommendations
4. State clearly: this is a RISK INDICATOR, not a diagnosis
5. Recommend consulting a doctor for clinical interpretation
6. Keep total response under 200 words

RESPONSE:"""

        if self.llm:
            try:
                response = self.llm.invoke(prompt)
                return response.content
            except Exception as e:
                print(f"[RAG] LLM call failed: {e}")

        # Fallback response if no LLM
        return self._fallback_explanation(disease, prs_data)

    def _fallback_explanation(self, disease: str, prs_data: dict) -> str:
        """Used when Groq API is not available."""
        risk = prs_data.get("risk_level", "Unknown")
        mult = prs_data.get("risk_multiplier", 1.0)
        return (
            f"Your genetic risk for {disease.replace('_', ' ')} is classified as "
            f"{risk} ({mult}x the population average). "
            f"This is based on your specific gene variants identified in your DNA report. "
            f"Please consult a doctor or genetic counsellor for clinical interpretation. "
            f"This is a risk indicator, not a diagnosis."
        )


class AgentPipeline:
    """
    Semi-agentic pipeline that decides which tools to call
    based on the genomic profile complexity.
    """

    def __init__(self, rag: RAGPipeline):
        self.rag = rag

    def process(self, prs_results: dict, shap_explanations: dict,
                user_profile: dict) -> dict:
        """
        Main agentic loop. For each disease:
        1. Retrieve evidence (RAG tool)
        2. Generate SHAP text explanation
        3. Call LLM to generate explanation
        """
        explanations = {}
        for disease, prs_data in prs_results.items():
            print(f"[AGENT] Processing {disease}...")

            # Tool 1: Retrieve evidence
            evidence = self.rag.retrieve_evidence(disease)

            # Tool 2: Get SHAP text
            shap_text = shap_explanations.get(disease, "No gene attribution available.")

            # Tool 3: Generate explanation
            explanation = self.rag.generate_disease_explanation(
                disease, prs_data, shap_text, evidence, user_profile
            )

            explanations[disease] = {
                "explanation": explanation,
                "evidence_retrieved": len(evidence) > 50,
                "llm_used": self.rag.llm is not None,
            }

        return explanations


if __name__ == "__main__":
    rag = RAGPipeline()

    test_prs = {
        "risk_level": "High",
        "risk_multiplier": 1.94,
        "contributing_snps": [{"gene": "TCF7L2", "contribution": 0.678}],
    }

    evidence = rag.retrieve_evidence("type2_diabetes")
    print(f"\n[TEST] Evidence retrieved ({len(evidence)} chars):")
    print(evidence[:300], "...")

    explanation = rag.generate_disease_explanation(
        "type2_diabetes",
        test_prs,
        "TCF7L2 gene contributes 67.8% of your diabetes risk",
        evidence,
        {"age": 35, "sex": "male"},
    )
    print(f"\n[TEST] LLM Explanation:\n{explanation}")
