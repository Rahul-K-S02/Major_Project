"""
GeneRisk — Multimodal Fusion: Genetics + Lifestyle
====================================================
Combines genetic PRS with lifestyle risk factors.
This is your second novel contribution — multimodal fusion.

Disease risk = f(genetic_PRS, lifestyle_score)
"""


class LifestyleFusion:
    """
    Fuses genetic risk score with lifestyle factors.
    Uses late fusion: compute separate scores, then combine.
    """

    # Lifestyle risk weights (from medical literature)
    LIFESTYLE_WEIGHTS = {
        "type2_diabetes": {
            "bmi_overweight": 0.35,      # BMI 25-30
            "bmi_obese":      0.65,      # BMI > 30
            "sedentary":      0.28,      # No regular exercise
            "smoking":        0.15,
            "family_history": 0.40,
            "high_sugar_diet":0.22,
        },
        "coronary_artery_disease": {
            "smoking":        0.55,
            "bmi_obese":      0.30,
            "sedentary":      0.35,
            "high_fat_diet":  0.25,
            "family_history": 0.45,
            "hypertension_history": 0.38,
        },
        "breast_cancer": {
            "smoking":        0.12,
            "alcohol":        0.20,
            "bmi_obese":      0.18,
            "family_history": 0.55,
            "late_childbirth":0.10,
        },
        "alzheimers": {
            "sedentary":      0.20,
            "smoking":        0.18,
            "low_education":  0.15,
            "family_history": 0.50,
            "hypertension_history": 0.22,
        },
        "hypertension": {
            "bmi_obese":      0.40,
            "high_salt_diet": 0.30,
            "smoking":        0.25,
            "sedentary":      0.22,
            "family_history": 0.38,
            "age_over50":     0.20,
        },
    }

    def calculate_lifestyle_score(self, lifestyle_data: dict) -> dict:
        """
        Calculate lifestyle risk score for each disease.

        Args:
            lifestyle_data: {
                "age": 35,
                "sex": "male",
                "bmi": 27.5,
                "smoking": true,
                "alcohol": false,
                "exercise_days_per_week": 2,
                "diet_type": "high_sugar",
                "family_history": ["diabetes", "heart_disease"],
                "existing_conditions": ["hypertension"]
            }

        Returns:
            {"type2_diabetes": 0.45, "coronary_artery_disease": 0.62, ...}
        """
        # Extract flags from lifestyle data
        bmi = lifestyle_data.get("bmi", 22)
        flags = {
            "bmi_overweight":  25 <= bmi < 30,
            "bmi_obese":       bmi >= 30,
            "smoking":         lifestyle_data.get("smoking", False),
            "alcohol":         lifestyle_data.get("alcohol", False),
            "sedentary":       lifestyle_data.get("exercise_days_per_week", 3) < 2,
            "high_sugar_diet": lifestyle_data.get("diet_type") == "high_sugar",
            "high_fat_diet":   lifestyle_data.get("diet_type") == "high_fat",
            "high_salt_diet":  lifestyle_data.get("diet_type") == "high_salt",
            "low_education":   lifestyle_data.get("education_years", 12) < 10,
            "late_childbirth": (
                lifestyle_data.get("sex") == "female"
                and lifestyle_data.get("age_first_child", 25) > 30
            ),
            "hypertension_history": "hypertension" in lifestyle_data.get("existing_conditions", []),
            "family_history":  len(lifestyle_data.get("family_history", [])) > 0,
            "age_over50":      lifestyle_data.get("age", 30) > 50,
        }

        scores = {}
        for disease, weights in self.LIFESTYLE_WEIGHTS.items():
            score = sum(
                weight for factor, weight in weights.items() if flags.get(factor, False)
            )
            # Normalise to 0-1 range
            max_possible = sum(weights.values())
            scores[disease] = round(score / max_possible, 4)

        return scores

    def fuse_scores(
        self,
        prs_results: dict,
        lifestyle_scores: dict,
        genetic_weight: float = 0.60,
        lifestyle_weight: float = 0.40,
    ) -> dict:
        """
        Combine genetic and lifestyle scores using weighted late fusion.

        Args:
            genetic_weight: How much weight to give genetic risk (default 60%)
            lifestyle_weight: How much weight to give lifestyle risk (default 40%)

        Returns:
            Enhanced PRS results with fused risk scores
        """
        fused = {}
        for disease, prs_data in prs_results.items():
            lifestyle_score = lifestyle_scores.get(disease, 0.0)
            genetic_score = min(prs_data.get("risk_multiplier", 1.0) / 3.0, 1.0)

            # Weighted fusion
            fused_score = (
                genetic_score * genetic_weight + lifestyle_score * lifestyle_weight
            )

            # Map back to risk multiplier scale
            fused_multiplier = round(fused_score * 3.0, 2)

            fused[disease] = {
                **prs_data,
                "genetic_score": round(genetic_score, 3),
                "lifestyle_score": round(lifestyle_score, 3),
                "fused_multiplier": fused_multiplier,
                "fused_risk_level": self._classify_fused_risk(fused_multiplier),
                "fusion_weights": {
                    "genetic": genetic_weight,
                    "lifestyle": lifestyle_weight,
                },
            }

        return fused

    def _classify_fused_risk(self, fused_multiplier: float) -> str:
        if fused_multiplier < 0.5:   return "Low"
        elif fused_multiplier < 0.8: return "Below Average"
        elif fused_multiplier < 1.2: return "Average"
        elif fused_multiplier < 1.6: return "Moderate"
        elif fused_multiplier < 2.0: return "High"
        else:                        return "Very High"


if __name__ == "__main__":
    from prs_engine import PRSEngine

    test_snps = [
        {"rs_id": "rs7903146", "genotype_dosage": 2},
        {"rs_id": "rs5219",    "genotype_dosage": 1},
        {"rs_id": "rs10811661","genotype_dosage": 2},
    ]

    prs_engine = PRSEngine()
    prs_results = prs_engine.calculate_all_diseases(test_snps)

    lifestyle_data = {
        "age": 38, "sex": "male", "bmi": 28.5,
        "smoking": True, "alcohol": False,
        "exercise_days_per_week": 1,
        "diet_type": "high_sugar",
        "family_history": ["diabetes"],
        "existing_conditions": [],
    }

    fusion = LifestyleFusion()
    lifestyle_scores = fusion.calculate_lifestyle_score(lifestyle_data)
    fused_results = fusion.fuse_scores(prs_results, lifestyle_scores)

    print("\n=== FUSED RISK SCORES ===")
    for disease, data in fused_results.items():
        print(f"\n{disease}:")
        print(f"  Genetic score:   {data['genetic_score']}")
        print(f"  Lifestyle score: {data['lifestyle_score']}")
        print(f"  Fused risk:      {data['fused_risk_level']}")
