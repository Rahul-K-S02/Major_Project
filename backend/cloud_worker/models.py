"""
GeneRisk — Pydantic Data Models
================================
Defines request/response schemas for FastAPI endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class FilteredSNP(BaseModel):
    rs_id: str
    chromosome: str = ""
    position: Optional[int] = None
    genotype_dosage: int = Field(..., ge=0, le=2, description="0, 1, or 2 copies of risk allele")


class UserProfile(BaseModel):
    age: int = Field(default=30, ge=1, le=120)
    sex: str = "unknown"
    ancestry: str = "south_asian"
    bmi: Optional[float] = None
    smoking: bool = False
    alcohol: bool = False
    exercise_days_per_week: int = Field(default=3, ge=0, le=7)
    diet_type: str = "balanced"
    family_history: List[str] = []
    existing_conditions: List[str] = []


class EdgeStats(BaseModel):
    total_variants: int = 0
    filtered_variants: int = 0
    reduction_percent: float = 0.0
    data_sent_to_cloud_mb: float = 0.0
    processing_time_sec: float = 0.0


class AnalysisRequest(BaseModel):
    filtered_snps: List[FilteredSNP]
    user_profile: UserProfile
    edge_stats: Optional[EdgeStats] = None
    route: Optional[str] = "B"   # A, B, or C from offload router
    model: Optional[str] = "llama-3.1-8b-instant"


class DiseaseRisk(BaseModel):
    prs_score: float
    population_mean: float
    risk_multiplier: float
    risk_level: str
    risk_percent: int
    snps_found: int
    snps_total: int
    contributing_snps: List[Dict[str, Any]] = []
    indian_correction_applied: bool = True


class FusedRisk(BaseModel):
    genetic_score: float
    lifestyle_score: float
    fused_multiplier: float
    fused_risk_level: str


class DiseaseExplanation(BaseModel):
    explanation: str
    evidence_retrieved: bool
    llm_used: bool


class AnalysisResponse(BaseModel):
    report_id: str
    prs_results: Dict[str, Any]
    fused_results: Dict[str, Any]
    shap_charts: Dict[str, str]       # {disease: base64_png}
    explanations: Dict[str, Any]
    pdf_base64: Optional[str] = None
    processing_time_sec: float
    timestamp: str
    route_used: str = "B"


class HealthResponse(BaseModel):
    status: str
    groq_connected: bool
    chromadb_loaded: bool
    clinvar_db: bool
    version: str
