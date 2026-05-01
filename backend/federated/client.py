"""
GeneRisk — Federated Learning Client (Hospital Node)
======================================================
Each client simulates one hospital that trains a local PRS model
on its own data slice without sharing patient records.

Only model weight gradients are shared — never patient data.
"""
import argparse
import numpy as np
import flwr as fl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")


def generate_hospital_data(client_id: int, n_samples: int = 300):
    """
    Generate synthetic genomic data for a simulated hospital.
    In production: each hospital would use its real patient data locally.

    Client 0 = Hospital in North India (higher T2D prevalence)
    Client 1 = Hospital in South India (different genetic background)
    Client 2 = Hospital in West India (mixed population)
    """
    np.random.seed(client_id * 42)

    # 10 SNP features (genotype dosage 0/1/2) — simulating key PRS SNPs
    n_features = 10

    # Different risk profiles per hospital/region
    risk_bias = [0.55, 0.48, 0.52][client_id]

    X = np.random.randint(0, 3, size=(n_samples, n_features)).astype(float)
    # Labels: 1 = diabetes, 0 = no diabetes
    # Weighted by known risk SNPs (SNP 0 = TCF7L2, SNP 1 = KCNJ11)
    logit = (X[:, 0] * 0.35 + X[:, 1] * 0.22 + X[:, 2] * 0.18 +
             np.random.randn(n_samples) * 0.3 - (1 - risk_bias))
    y = (logit > 0).astype(int)

    split = int(n_samples * 0.8)
    return (X[:split], y[:split]), (X[split:], y[split:])


class GeneRiskFLClient(fl.client.NumPyClient):
    """Flower client representing one hospital."""

    def __init__(self, client_id: int):
        self.client_id = client_id
        self.hospital_name = ["North India Hospital", "South India Hospital", "West India Hospital"][client_id]
        (self.X_train, self.y_train), (self.X_test, self.y_test) = generate_hospital_data(client_id)

        self.scaler = StandardScaler()
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_test = self.scaler.transform(self.X_test)

        self.model = LogisticRegression(max_iter=1000, random_state=42)
        # Initial fit so model has parameters
        self.model.fit(self.X_train, self.y_train)

        print(f"[Client {client_id}] {self.hospital_name}: {len(self.X_train)} train, {len(self.X_test)} test samples")

    def get_parameters(self, config):
        """Return model weights to server."""
        return [self.model.coef_, self.model.intercept_]

    def set_parameters(self, parameters):
        """Receive aggregated weights from server."""
        self.model.coef_ = parameters[0]
        self.model.intercept_ = parameters[1]

    def fit(self, parameters, config):
        """Train on local data — data never leaves this client."""
        self.set_parameters(parameters)
        self.model.fit(self.X_train, self.y_train)
        print(f"[Client {self.client_id}] Trained on local data — NOT sharing patient records")
        return self.get_parameters(config={}), len(self.X_train), {}

    def evaluate(self, parameters, config):
        """Evaluate model on local test data."""
        self.set_parameters(parameters)
        y_pred = self.model.predict(self.X_test)
        y_prob = self.model.predict_proba(self.X_test)[:, 1]

        acc = accuracy_score(self.y_test, y_pred)
        try:
            auc = roc_auc_score(self.y_test, y_prob)
        except Exception:
            auc = 0.5

        loss = 1 - acc
        print(f"[Client {self.client_id}] Eval — Accuracy: {acc:.4f}  AUC: {auc:.4f}")
        return loss, len(self.X_test), {"accuracy": acc, "auc": auc}


def start_client(client_id: int):
    print(f"\n[Client {client_id}] Connecting to FL server at localhost:8080...")
    client = GeneRiskFLClient(client_id)
    fl.client.start_numpy_client(server_address="localhost:8080", client=client)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", type=int, required=True, choices=[0, 1, 2])
    args = parser.parse_args()
    start_client(args.client_id)
