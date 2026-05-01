"""
GeneRisk — FastAPI Cloud Worker
================================
Deploy this on Railway.app (free tier).
This is what your Vercel frontend calls via API.

Endpoints:
  POST /analyze        — main analysis endpoint
  GET  /health         — health check
  GET  /report/{id}    — get saved report
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge_agent.prs_engine import PRSEngine
from edge_agent.shap_explainer import SHAPExplainer
from edge_agent.lifestyle_fusion import LifestyleFusion
from cloud_worker.rag_pipeline import RAGPipeline, AgentPipeline
from cloud_worker.report_generator import ReportGenerator
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="GeneRisk API",
    description="AI-Powered Genomic Risk Intelligence System — JNNCE B13",
    version="1.0.0",
)

# Allow Vercel frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Initialize components ────────────────────────────────────────────────────
prs_engine = PRSEngine(use_indian_correction=True)
shap_explainer = SHAPExplainer()
lifestyle_fusion = LifestyleFusion()
rag = RAGPipeline()
agent = AgentPipeline(rag)
report_gen = ReportGenerator()


# ─── Request / Response Models ────────────────────────────────────────────────
class FilteredSNP(BaseModel):
    rs_id: str
    chromosome: str
    position: Optional[int] = None
    genotype_dosage: int  # 0, 1, or 2


class UserProfile(BaseModel):
    age: int = 30
    sex: str = "unknown"
    ancestry: str = "south_asian"
    bmi: Optional[float] = None
    smoking: bool = False
    alcohol: bool = False
    exercise_days_per_week: int = 3
    diet_type: str = "balanced"
    family_history: list = []
    existing_conditions: list = []


class AnalysisRequest(BaseModel):
    filtered_snps: list[FilteredSNP]
    user_profile: UserProfile
    edge_stats: Optional[dict] = None   # Stats from VCF filtering


class AnalysisResponse(BaseModel):
    report_id: str
    prs_results: dict
    fused_results: dict
    shap_charts: dict
    explanations: dict
    pdf_base64: Optional[str] = None
    processing_time_sec: float
    timestamp: str


# ─── Main Analysis Endpoint ───────────────────────────────────────────────────
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_genomic_risk(request: AnalysisRequest):
    """
    Main endpoint. Receives filtered SNPs from edge agent.
    Runs: PRS → SHAP → Lifestyle Fusion → RAG → Report
    """
    import time
    start = time.time()
    report_id = str(uuid.uuid4())[:8].upper()

    print(f"\n[API] New analysis request — ID: {report_id}")
    print(f"[API] Received {len(request.filtered_snps)} filtered SNPs")
    print(f"[API] User: Age {request.user_profile.age}, {request.user_profile.sex}")

    # Convert to list of dicts for engine
    snps = [snp.dict() for snp in request.filtered_snps]
    profile = request.user_profile.dict()

    try:
        # Step 1: Calculate PRS for all diseases
        print("[API] Step 1: Calculating PRS...")
        prs_results = prs_engine.calculate_all_diseases(snps, profile)

        # Step 2: Generate SHAP gene attribution charts
        print("[API] Step 2: Generating SHAP charts...")
        shap_charts = shap_explainer.generate_all_charts(prs_results)
        shap_text_explanations = {
            disease: shap_explainer.get_text_explanation(disease, data)
            for disease, data in prs_results.items()
        }

        # Step 3: Multimodal fusion (genetics + lifestyle)
        print("[API] Step 3: Multimodal fusion...")
        lifestyle_scores = lifestyle_fusion.calculate_lifestyle_score(profile)
        fused_results = lifestyle_fusion.fuse_scores(prs_results, lifestyle_scores)

        # Step 4: RAG + LLM explanations (semi-agentic pipeline)
        print("[API] Step 4: Generating AI explanations...")
        explanations = agent.process(prs_results, shap_text_explanations, profile)

        # Step 5: Generate PDF report
        print("[API] Step 5: Generating PDF report...")
        pdf_base64 = report_gen.generate_pdf(
            report_id=report_id,
            prs_results=prs_results,
            fused_results=fused_results,
            explanations=explanations,
            shap_charts=shap_charts,
            user_profile=profile,
        )

        elapsed = round(time.time() - start, 2)
        print(f"[API] Analysis complete in {elapsed}s")

        return AnalysisResponse(
            report_id=report_id,
            prs_results=prs_results,
            fused_results=fused_results,
            shap_charts=shap_charts,
            explanations=explanations,
            pdf_base64=pdf_base64,
            processing_time_sec=elapsed,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        print(f"[API] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "groq_connected": rag.llm is not None,
        "chromadb_loaded": rag.vectorstore is not None,
        "version": "1.0.0",
    }


@app.get("/")
def root():
    return {
        "project": "GeneRisk — AI-Powered Genomic Risk Intelligence",
        "team": "JNNCE Batch B13",
        "docs": "/docs",
    }


# ─── Run locally ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n GeneRisk API Server")
    print("=" * 40)
    print("Visit http://localhost:8000/docs for interactive API docs")
    print("=" * 40 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
