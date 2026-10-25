
from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "supervised_model.pkl"


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_PATH}"
        )

    saved = joblib.load(MODEL_PATH)
    model = saved["model"]
    feature_names = saved["feature_names"]

    importance = pd.DataFrame({
        "feature": feature_names,
        "importance": model.feature_importances_,
    })

    importance = importance.sort_values(
        "importance",
        ascending=False,
    )

    print("ADIS MODEL FEATURE IMPORTANCE")
    print("=" * 40)
    print(importance.to_string(
        index=False,
        formatters={
            "importance": lambda value: f"{value:.4f}"
        },
    ))

    print(
        "\nNote: importance measures the model's use of features "
        "within this synthetic training setup."
    )


if __name__ == "__main__":
    main()
