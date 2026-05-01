"""
GeneRisk — PDF Report Generator
=================================
Generates a downloadable PDF report for the patient.
"""

import io
import base64
from datetime import datetime


class ReportGenerator:
    """Generates PDF report using ReportLab."""

    def generate_pdf(
        self,
        report_id: str,
        prs_results: dict,
        fused_results: dict,
        explanations: dict,
        shap_charts: dict,
        user_profile: dict,
    ) -> str:
        """
        Generate PDF and return as base64 string.
        Returns empty string if ReportLab not available.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor, white, black
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table,
                TableStyle, HRFlowable,
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm, leftMargin=2*cm,
                topMargin=2*cm, bottomMargin=2*cm,
            )

            styles = getSampleStyleSheet()
            PRIMARY = HexColor("#1F3864")
            ACCENT  = HexColor("#2E75B6")
            HIGH    = HexColor("#E24B4A")
            LOW     = HexColor("#1D9E75")

            title_style = ParagraphStyle(
                "Title", parent=styles["Title"],
                fontSize=20, textColor=PRIMARY, spaceAfter=6,
            )
            h2_style = ParagraphStyle(
                "H2", parent=styles["Heading2"],
                fontSize=13, textColor=ACCENT, spaceBefore=12, spaceAfter=4,
            )
            body_style = ParagraphStyle(
                "Body", parent=styles["Normal"],
                fontSize=10, leading=14, spaceAfter=6,
            )
            disclaimer_style = ParagraphStyle(
                "Disclaimer", parent=styles["Normal"],
                fontSize=8, textColor=HexColor("#888888"), leading=11,
            )

            story = []

            # Header
            story.append(Paragraph("GeneRisk Genomic Risk Report", title_style))
            story.append(Paragraph(
                "AI-Powered Genomic Risk Intelligence System", 
                ParagraphStyle("sub", parent=styles["Normal"], fontSize=11, 
                               textColor=ACCENT, spaceAfter=4)
            ))
            story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
            story.append(Spacer(1, 0.3*cm))

            # Patient info
            story.append(Paragraph(f"<b>Report ID:</b> {report_id}", body_style))
            story.append(Paragraph(
                f"<b>Generated:</b> {datetime.now().strftime('%d %B %Y, %H:%M')}",
                body_style
            ))
            age = user_profile.get("age", "N/A")
            sex = user_profile.get("sex", "N/A")
            story.append(Paragraph(f"<b>Patient:</b> Age {age}, {sex.title()}", body_style))
            story.append(Spacer(1, 0.4*cm))

            # Risk Summary Table
            story.append(Paragraph("Disease Risk Summary", h2_style))

            table_data = [["Disease", "Risk Level", "Multiplier", "Fused Risk"]]
            risk_colors = {
                "Low": LOW, "Average": HexColor("#888888"),
                "Moderate": HexColor("#EF9F27"), "High": HIGH, "Very High": HIGH,
            }

            for disease, data in prs_results.items():
                fused = fused_results.get(disease, {})
                risk = data.get("risk_level", "N/A")
                fused_risk = fused.get("fused_risk_level", "N/A")
                mult = f"{data.get('risk_multiplier', 0):.2f}x"
                table_data.append([
                    disease.replace("_", " ").title(),
                    risk, mult, fused_risk,
                ])

            table = Table(table_data, colWidths=[5.5*cm, 3*cm, 3*cm, 3.5*cm])
            table_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR",  (0, 0), (-1, 0), white),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",   (0, 0), (-1, 0), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F5F5F5"), white]),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ])
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 0.5*cm))

            # Disease explanations
            story.append(Paragraph("Detailed Findings", h2_style))
            for disease, exp_data in explanations.items():
                prs = prs_results.get(disease, {})
                risk_level = prs.get("risk_level", "Unknown")
                story.append(Paragraph(
                    f"<b>{disease.replace('_', ' ').title()}</b> — {risk_level}",
                    ParagraphStyle("DiseaseTitle", parent=styles["Normal"],
                                   fontSize=11, textColor=PRIMARY, spaceBefore=8, spaceAfter=3)
                ))
                explanation = exp_data.get("explanation", "No explanation available.")
                # Clean up for PDF
                explanation = explanation.replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(explanation, body_style))

            story.append(Spacer(1, 0.5*cm))

            # Disclaimer
            story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#CCCCCC")))
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(
                "⚠ IMPORTANT DISCLAIMER: This report is generated by an AI system for "
                "educational and research purposes only. It is NOT a medical diagnosis. "
                "Genetic risk scores are probabilistic indicators based on population studies. "
                "Please consult a qualified physician or genetic counsellor before making any "
                "health decisions. Developed by JNNCE Batch B13 — GeneRisk Project.",
                disclaimer_style,
            ))

            doc.build(story)
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("utf-8")

        except ImportError:
            print("[REPORT] ReportLab not installed: pip install reportlab")
            return ""
        except Exception as e:
            print(f"[REPORT] PDF generation error: {e}")
            return ""
