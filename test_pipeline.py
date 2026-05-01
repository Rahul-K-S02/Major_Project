"""
GeneRisk — End-to-End Test
============================
Run this to test the full pipeline without the frontend.
Perfect for verifying each component works before integrating.

Usage: cd generisk && python tests/test_pipeline.py
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.edge_agent.vcf_parser import VCFEdgeFilter, create_sample_vcf
from backend.edge_agent.prs_engine import PRSEngine
from backend.edge_agent.shap_explainer import SHAPExplainer
from backend.edge_agent.lifestyle_fusion import LifestyleFusion
from backend.cloud_worker.rag_pipeline import RAGPipeline, AgentPipeline
from backend.cloud_worker.report_generator import ReportGenerator


def run_full_pipeline_test():
    """
    Simulates the complete GeneRisk pipeline from VCF upload to PDF report.
    No API calls needed — all runs locally.
    """
    print("\n" + "=" * 60)
    print("  GeneRisk — Full Pipeline Test")
    print("  JNNCE Batch B13 | VTU Final Year Project")
    print("=" * 60 + "\n")

    # ── Step 1: Create sample VCF & run edge filter ────────────────────────
    print("STEP 1: Edge Agent — VCF Parsing & Filtering")
    print("-" * 40)

    vcf_path = create_sample_vcf("./data/sample_test.vcf")
    edge_filter = VCFEdgeFilter()
    edge_result = edge_filter.parse_and_filter(vcf_path)

    filtered_snps = edge_result["filtered_snps"]
    stats = edge_result["stats"]

    print(f"✓ Filtered: {stats['total_variants']} → {stats['filtered_variants']} variants")
    print(f"✓ Data sent to cloud: {stats['data_sent_to_cloud_mb']} MB")
    print(f"✓ Reduction: {stats['reduction_percent']}%")
    print(f"✓ Time: {edge_result['processing_time_sec']}s\n")

    # ── Step 2: PRS Calculation ────────────────────────────────────────────
    print("STEP 2: PRS Engine — Disease Risk Calculation")
    print("-" * 40)

    prs_engine = PRSEngine(use_indian_correction=True)
    prs_results = prs_engine.calculate_all_diseases(filtered_snps)

    for disease, data in prs_results.items():
        risk_emoji = {"Low": "🟢", "Average": "🔵", "Moderate": "🟡",
                      "High": "🔴", "Very High": "🔴"}.get(data["risk_level"], "⚪")
        print(f"  {risk_emoji} {disease.replace('_', ' ').title():<30} "
              f"{data['risk_level']:<12} {data['risk_multiplier']}x")

    complexity = prs_engine.get_complexity_score(prs_results)
    print(f"\n✓ Complexity score: {complexity} (0=simple, 1=complex)")

    # ── Step 3: SHAP Explainability ───────────────────────────────────────
    print("\nSTEP 3: SHAP — Gene Attribution")
    print("-" * 40)

    explainer = SHAPExplainer()
    charts = explainer.generate_all_charts(prs_results)

    for disease in prs_results:
        has_chart = disease in charts and len(charts[disease]) > 50
        print(f"  {'✓' if has_chart else '✗'} Chart generated for {disease}")

    # Get text explanation for one disease
    text_exp = explainer.get_text_explanation(
        "type2_diabetes", prs_results.get("type2_diabetes", {})
    )
    print(f"\n  Sample explanation:\n  → {text_exp[:150]}...")

    # ── Step 4: Multimodal Fusion ─────────────────────────────────────────
    print("\nSTEP 4: Multimodal Fusion — Genetics + Lifestyle")
    print("-" * 40)

    lifestyle_data = {
        "age": 38, "sex": "male", "bmi": 28.0,
        "smoking": True, "alcohol": False,
        "exercise_days_per_week": 1,
        "diet_type": "high_sugar",
        "family_history": ["diabetes"],
        "existing_conditions": [],
    }

    fusion = LifestyleFusion()
    lifestyle_scores = fusion.calculate_lifestyle_score(lifestyle_data)
    fused_results = fusion.fuse_scores(prs_results, lifestyle_scores)

    print(f"  Lifestyle input: BMI {lifestyle_data['bmi']}, "
          f"Smoker: {lifestyle_data['smoking']}, "
          f"Exercise: {lifestyle_data['exercise_days_per_week']}days/week")
    print()

    for disease, data in fused_results.items():
        g = data.get("genetic_score", 0)
        l = data.get("lifestyle_score", 0)
        f = data.get("fused_risk_level", "?")
        print(f"  {disease.replace('_', ' ').title():<30} "
              f"Genetic:{g:.2f} + Lifestyle:{l:.2f} → {f}")

    # ── Step 5: RAG + LLM ─────────────────────────────────────────────────
    print("\nSTEP 5: RAG Pipeline — AI Explanation Generation")
    print("-" * 40)

    rag = RAGPipeline()
    agent = AgentPipeline(rag)

    shap_texts = {
        disease: explainer.get_text_explanation(disease, data)
        for disease, data in prs_results.items()
    }

    print(f"  LLM connected: {rag.llm is not None}")
    print(f"  ChromaDB loaded: {rag.vectorstore is not None}")
    print(f"  Generating explanations for {len(prs_results)} diseases...")

    explanations = agent.process(prs_results, shap_texts, lifestyle_data)

    for disease, exp in explanations.items():
        text = exp.get("explanation", "")
        print(f"\n  [{disease.replace('_', ' ').title()}]")
        print(f"  {text[:200]}...")

    # ── Step 6: PDF Report ────────────────────────────────────────────────
    print("\n\nSTEP 6: Report Generator — PDF Creation")
    print("-" * 40)

    report_gen = ReportGenerator()
    pdf_b64 = report_gen.generate_pdf(
        report_id="TEST-001",
        prs_results=prs_results,
        fused_results=fused_results,
        explanations=explanations,
        shap_charts=charts,
        user_profile=lifestyle_data,
    )

    if pdf_b64:
        # Save test PDF
        import base64
        os.makedirs("./data", exist_ok=True)
        with open("./data/test_report.pdf", "wb") as f:
            f.write(base64.b64decode(pdf_b64))
        print(f"✓ PDF generated: ./data/test_report.pdf")
        print(f"  Size: {len(pdf_b64) // 1024} KB (base64)")
    else:
        print("✗ PDF generation failed (install reportlab: pip install reportlab)")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PIPELINE TEST COMPLETE")
    print("=" * 60)
    print(f"  ✓ Edge filtering:    {stats['reduction_percent']}% data reduction")
    print(f"  ✓ Diseases assessed: {len(prs_results)}")
    print(f"  ✓ SHAP charts:       {len(charts)}")
    print(f"  ✓ LLM explanations:  {len(explanations)}")
    print(f"  ✓ PDF report:        {'Yes' if pdf_b64 else 'No (install reportlab)'}")
    print(f"  ✓ Total time:        {edge_result['processing_time_sec']}s (edge only)")
    print("\n  Your project pipeline is working!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_full_pipeline_test()
