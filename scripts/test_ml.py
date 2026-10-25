import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from engine.anomaly import AnomalyDetector


MODEL_PATH = "models/anomaly_model.pkl"


def test_model():

    detector = AnomalyDetector(MODEL_PATH)
    detector.load()

    test_cases = {

        "NORMAL": [
            10, 0, 0, 10, 2, 5, 0, 5
        ],

        "SLIGHTLY_UNUSUAL": [
            15, 1, 0, 15, 5, 8, 1, 7
        ],

        "MODERATELY_UNUSUAL": [
            25, 3, 1, 25, 10, 15, 3, 10
        ],

        "VERY_UNUSUAL": [
            50, 8, 3, 40, 25, 40, 10, 20
        ],

        "EXTREMELY_UNUSUAL": [
            100, 20, 8, 70, 50, 100, 25, 35
        ],

        "HIGHLY_ANOMALOUS": [
            250, 40, 15, 100, 100, 200, 80, 60
        ],
    }

    print("=" * 60)
    print("ADIS - ML ANOMALY DETECTION TEST")
    print("=" * 60)

    for name, vector in test_cases.items():

        raw_score = detector.predict(vector)

        contribution = detector.anomaly_contribution(
            vector
        )

        print()
        print(f"Case: {name}")
        print(f"Vector: {vector}")
        print(f"Raw anomaly score: {raw_score:.4f}")
        print(f"Risk contribution: {contribution}/40")

    print()
    print("=" * 60)


if __name__ == "__main__":
    test_model()