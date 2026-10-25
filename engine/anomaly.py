from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:

    def __init__(
        self,
        model_path: str = "models/anomaly_model.pkl"
    ):
        self.model_path = Path(model_path)

        self.model = None

    def train(
        self,
        normal_vectors: list[list[float]]
    ):

        if not normal_vectors:
            raise ValueError(
                "Normal training data is empty."
            )

        self.model = IsolationForest(
            n_estimators=100,
            contamination="auto",
            random_state=42
        )

        self.model.fit(
            np.array(normal_vectors)
        )

        self.model_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        joblib.dump(
            self.model,
            self.model_path
        )

    def load(self):

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}"
            )

        self.model = joblib.load(
            self.model_path
        )

    def predict(
        self,
        vector: list[float]
    ) -> float:

        if self.model is None:
            raise RuntimeError(
                "Anomaly model is not loaded."
            )

        values = np.array(
            [vector]
        )

        decision = self.model.decision_function(
            values
        )[0]

        return float(decision)

    def anomaly_contribution(
            self,
            vector: list[float]
    ) -> int:

        if self.model is None:
            raise RuntimeError(
                "Anomaly model is not loaded."
            )

        values = np.array([vector])

        decision = self.model.decision_function(
            values
        )[0]

        # Isolation Forest:
        # positive = more normal
        # negative = more anomalous
        #
        # Convert anomalous values into
        # a bounded 0-40 risk contribution.
        contribution = -decision * 80

        return int(
            max(
                0,
                min(
                    40,
                    contribution
                )
            )
        )