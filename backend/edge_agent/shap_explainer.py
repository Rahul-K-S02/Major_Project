"""
GeneRisk — SHAP Explainability Engine
======================================
Generates gene-level contribution charts.
Shows WHICH gene contributed HOW MUCH to each disease risk.
This is your key differentiator — clinical trust feature.
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")  # No display needed — runs on server
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import base64


class SHAPExplainer:
    """
    Generates SHAP-style waterfall charts for gene attribution.

    In full implementation: use actual SHAP library with XGBoost model.
    Here: uses PRS contribution values as SHAP approximations.
    """

    def generate_waterfall_chart(
        self, disease: str, contributing_snps: list, base_value: float = 1.0
    ) -> str:
        """
        Generate a waterfall chart showing gene contributions.

        Args:
            disease: Disease name (e.g., "type2_diabetes")
            contributing_snps: List of {gene, contribution, rs_id} from PRS engine
            base_value: Population mean PRS

        Returns:
            Base64 encoded PNG image string (for embedding in HTML/PDF)
        """
        if not contributing_snps:
            return ""

        # Take top 8 contributors
        snps = contributing_snps[:8]
        genes = [s["gene"] for s in snps]
        contributions = [s["contribution"] for s in snps]
        rs_ids = [s["rs_id"] for s in snps]

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#FAFAFA")
        ax.set_facecolor("#FAFAFA")

        colors = ["#E24B4A" if c > 0 else "#1D9E75" for c in contributions]
        bars = ax.barh(
            [f"{g}\n({r})" for g, r in zip(genes, rs_ids)],
            contributions,
            color=colors,
            edgecolor="white",
            linewidth=0.5,
            height=0.6,
        )

        ax.axvline(x=0, color="#444441", linewidth=0.8, linestyle="-")
        ax.set_xlabel("SHAP Value (contribution to risk score)", fontsize=11, color="#444441")
        ax.set_title(
            f"Gene Contributions — {disease.replace('_', ' ').title()}",
            fontsize=13, fontweight="bold", color="#1F3864", pad=12
        )

        # Add value labels on bars
        for bar, val in zip(bars, contributions):
            label = f"+{val:.3f}" if val > 0 else f"{val:.3f}"
            x_pos = val + 0.005 if val >= 0 else val - 0.005
            ha = "left" if val >= 0 else "right"
            ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                    label, va="center", ha=ha, fontsize=9, color="#444441")

        risk_patch = mpatches.Patch(color="#E24B4A", label="Increases risk")
        protect_patch = mpatches.Patch(color="#1D9E75", label="Decreases risk")
        ax.legend(handles=[risk_patch, protect_patch], loc="lower right", fontsize=9)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(colors="#666666")

        plt.tight_layout()

        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="#FAFAFA")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)

        return f"data:image/png;base64,{img_base64}"

    def generate_all_charts(self, prs_results: dict) -> dict:
        """Generate SHAP charts for all diseases. Returns {disease: base64_img}"""
        charts = {}
        for disease, data in prs_results.items():
            if data.get("contributing_snps"):
                charts[disease] = self.generate_waterfall_chart(
                    disease,
                    data["contributing_snps"],
                    data.get("population_mean", 1.0),
                )
        return charts

    def get_text_explanation(self, disease: str, prs_data: dict) -> str:
        """
        Generate a plain English text explanation of gene contributions.
        Used as context for the LLM report generator.
        """
        snps = prs_data.get("contributing_snps", [])
        if not snps:
            return f"No significant genetic variants found for {disease}."

        top = snps[0]
        explanation = (
            f"For {disease.replace('_', ' ')}, your highest contributing gene is "
            f"{top['gene']} (variant {top['rs_id']}) with a contribution of "
            f"{top['contribution']:.3f}. "
        )
        if len(snps) > 1:
            second = snps[1]
            explanation += (
                f"The second contributor is {second['gene']} ({second['rs_id']}) "
                f"with {second['contribution']:.3f}. "
            )

        risk = prs_data.get("risk_level", "Unknown")
        multiplier = prs_data.get("risk_multiplier", 1.0)
        explanation += (
            f"Overall, your genetic risk is {multiplier}x the population average, "
            f"classified as {risk}."
        )

        return explanation


if __name__ == "__main__":
    # Test with sample data
    test_snps = [
        {"gene": "TCF7L2", "rs_id": "rs7903146", "contribution": 0.678, "dosage": 2},
        {"gene": "KCNJ11", "rs_id": "rs5219",    "contribution": 0.220, "dosage": 1},
        {"gene": "CDKN2A", "rs_id": "rs10811661","contribution": 0.261, "dosage": 2},
        {"gene": "GCK",    "rs_id": "rs4607517", "contribution": 0.000, "dosage": 0},
    ]

    explainer = SHAPExplainer()
    img = explainer.generate_waterfall_chart("type2_diabetes", test_snps)
    print(f"Chart generated: {img[:50]}...")

    text = explainer.get_text_explanation(
        "type2_diabetes",
        {"contributing_snps": test_snps, "risk_level": "High", "risk_multiplier": 1.94}
    )
    print(f"\nText explanation:\n{text}")
