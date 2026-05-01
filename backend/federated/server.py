"""
GeneRisk — Federated Learning Server (Flower Coordinator)
==========================================================
Run this on your laptop to start the FL aggregation server.
It coordinates 3 simulated hospital clients.

Usage:
  Terminal 1: python backend/federated/server.py
  Terminal 2: python backend/federated/client.py --client-id 0
  Terminal 3: python backend/federated/client.py --client-id 1
  Terminal 4: python backend/federated/client.py --client-id 2

Or just run: python backend/federated/run_simulation.py
"""
import flwr as fl
from flwr.server.strategy import FedAvg
from typing import List, Tuple, Optional, Dict
import numpy as np


class GeneRiskFedAvgStrategy(FedAvg):
    """
    Custom FedAvg strategy that logs per-round accuracy improvements.
    This produces the table/chart that goes in your research paper.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.round_results = []

    def aggregate_fit(self, server_round, results, failures):
        aggregated = super().aggregate_fit(server_round, results, failures)
        print(f"\n[FL SERVER] Round {server_round} — {len(results)} clients contributed, {len(failures)} failed")
        return aggregated

    def aggregate_evaluate(self, server_round, results, failures):
        if not results:
            return None, {}

        # Weighted average of accuracy across clients
        total_examples = sum(num for num, _ in results)
        weighted_acc = sum(num * metrics["accuracy"] for num, metrics in results) / total_examples
        weighted_auc = sum(num * metrics.get("auc", 0) for num, metrics in results) / total_examples

        self.round_results.append({
            "round": server_round,
            "accuracy": round(weighted_acc, 4),
            "auc": round(weighted_auc, 4),
            "clients": len(results),
        })

        print(f"[FL SERVER] Round {server_round} aggregated — Accuracy: {weighted_acc:.4f}  AUC: {weighted_auc:.4f}")
        return weighted_acc, {"accuracy": weighted_acc, "auc": weighted_auc}


def start_server(num_rounds: int = 5, min_clients: int = 3):
    """Start the Flower FL server."""
    print("\n" + "="*55)
    print("  GeneRisk Federated Learning Server")
    print("  Waiting for 3 hospital clients to connect...")
    print("="*55 + "\n")

    strategy = GeneRiskFedAvgStrategy(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=min_clients,
        min_evaluate_clients=min_clients,
        min_available_clients=min_clients,
    )

    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
    )

    # Print final results table (for your paper)
    print("\n" + "="*55)
    print("  FEDERATED LEARNING RESULTS")
    print("  (Include this table in your research paper)")
    print("="*55)
    print(f"{'Round':<8} {'Accuracy':<12} {'AUC-ROC':<12} {'Clients'}")
    print("-"*44)
    for r in strategy.round_results:
        print(f"{r['round']:<8} {r['accuracy']:<12} {r['auc']:<12} {r['clients']}")
    print("="*55)


if __name__ == "__main__":
    start_server(num_rounds=5, min_clients=3)
