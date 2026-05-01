"""
GeneRisk — Offload Router
==========================
Decides which cloud tier to use based on:
  - genomic profile complexity score
  - current network bandwidth
  - user priority setting

Routes:
  Route A → simple profile  → llama-3.1-8b-instant  (fast, free)
  Route B → moderate        → llama-3.1-70b-versatile (better, free)
  Route C → complex/cancer  → llama-3.1-70b + full RAG (thorough)
"""
import time
import urllib.request
import os


class OffloadRouter:
    """Adaptive routing decision engine."""

    ROUTES = {
        "A": {"model": "llama-3.1-8b-instant",     "rag_depth": 1, "label": "Standard"},
        "B": {"model": "llama-3.1-70b-versatile",   "rag_depth": 3, "label": "Enhanced"},
        "C": {"model": "llama-3.1-70b-versatile",   "rag_depth": 5, "label": "Comprehensive"},
    }

    def decide(self, complexity_score: float, priority: str = "standard") -> dict:
        """
        Return routing decision.

        Args:
            complexity_score: 0.0–1.0 from PRSEngine.get_complexity_score()
            priority: "standard" | "priority" | "clinical"

        Returns:
            {"route": "B", "model": "llama-3.1-70b-versatile", "rag_depth": 3, "label": "Enhanced"}
        """
        # Clinical priority always gets Route C
        if priority == "clinical":
            route = "C"
        elif complexity_score >= 0.6 or priority == "priority":
            route = "C"
        elif complexity_score >= 0.3:
            route = "B"
        else:
            route = "A"

        decision = {"route": route, **self.ROUTES[route]}
        print(f"[ROUTER] Complexity={complexity_score:.2f} Priority={priority} → Route {route} ({decision['label']})")
        return decision

    def measure_bandwidth_mbps(self) -> float:
        """
        Quick bandwidth estimate (downloads 500KB test file).
        Returns Mbps. Falls back to 10 Mbps if test fails.
        """
        try:
            url = "https://httpbin.org/bytes/512000"  # 512KB
            start = time.time()
            urllib.request.urlretrieve(url, os.devnull)
            elapsed = time.time() - start
            mbps = round((0.512 * 8) / elapsed, 1)
            print(f"[ROUTER] Bandwidth: {mbps} Mbps")
            return mbps
        except Exception:
            print("[ROUTER] Bandwidth test failed — assuming 10 Mbps")
            return 10.0

    def build_payload(self, filtered_snps: list, prs_results: dict,
                      user_profile: dict, edge_stats: dict) -> dict:
        """
        Build the anonymised payload to send to cloud.
        NEVER includes raw genotype sequences — only rs-IDs and dosage numbers.
        """
        return {
            "filtered_snps": [
                {"rs_id": s["rs_id"], "genotype_dosage": s["genotype_dosage"],
                 "chromosome": s.get("chromosome", "")}
                for s in filtered_snps
            ],
            "user_profile": {
                "age":    user_profile.get("age", 30),
                "sex":    user_profile.get("sex", "unknown"),
                "ancestry": user_profile.get("ancestry", "south_asian"),
                "bmi":    user_profile.get("bmi"),
                "smoking":               user_profile.get("smoking", False),
                "alcohol":               user_profile.get("alcohol", False),
                "exercise_days_per_week":user_profile.get("exercise_days_per_week", 3),
                "diet_type":             user_profile.get("diet_type", "balanced"),
                "family_history":        user_profile.get("family_history", []),
                "existing_conditions":   user_profile.get("existing_conditions", []),
            },
            "edge_stats": edge_stats,
        }


if __name__ == "__main__":
    router = OffloadRouter()
    for score in [0.1, 0.4, 0.75]:
        d = router.decide(score)
        print(f"  Score {score} → Route {d['route']}: {d['model']}, RAG depth {d['rag_depth']}")
