import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np


MODEL_PATH = PROJECT_ROOT / "models" / "anomaly_model.pkl"


def main():

    model = joblib.load(MODEL_PATH)

    print("=" * 60)
    print("ADIS - ISOLATION FOREST MODEL INSPECTION")
    print("=" * 60)

    print()
    print("Model type:")
    print(type(model).__name__)

    print()
    print("Number of estimators:")
    print(model.n_estimators)

    print()
    print("Contamination:")
    print(model.contamination)

    print()
    print("Feature count:")
    print(model.n_features_in_)

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()