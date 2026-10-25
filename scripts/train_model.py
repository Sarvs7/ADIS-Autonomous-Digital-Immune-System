
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "synthetic_behavior.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "supervised_model.pkl"
METRICS_PATH = PROJECT_ROOT / "models" / "training_metrics.json"

FEATURE_NAMES = [
    "process_snapshot_count",
    "process_start_count",
    "process_stop_count",
    "cpu_mean",
    "cpu_max",
    "memory_mean",
    "memory_max",
    "thread_mean",
    "thread_max",
    "child_process_count",
    "process_age_seconds",
    "file_create_count",
    "file_modify_count",
    "file_delete_count",
    "unique_files_touched",
    "network_connection_count",
    "unique_remote_ip_count",
    "unique_remote_port_count",
]


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    required_columns = FEATURE_NAMES + [
        "label",
        "scenario_family",
    ]
    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {missing}"
        )

    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Dataset contains missing values in required columns."
        )

    X = df[FEATURE_NAMES]
    y = df["label"]

    if set(y.unique()) != {"BENIGN", "SUSPICIOUS"}:
        raise ValueError(
            f"Unexpected labels: {sorted(y.unique())}"
        )

    # Hold out complete scenario families to test generalization.
    # Two benign and two suspicious families are held out.
    held_out_families = [
        "cloud_sync",
        "file_copy",
        "rapid_file_deletion",
        "mixed_activity",
    ]

    test_mask = df["scenario_family"].isin(held_out_families)
    X_train = X.loc[~test_mask]
    y_train = y.loc[~test_mask]
    X_test = X.loc[test_mask]
    y_test = y.loc[test_mask]

    if X_train.empty or X_test.empty:
        raise ValueError(
            "Training or testing split is empty."
        )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=2,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(
        y_test,
        predictions,
        labels=["BENIGN", "SUSPICIOUS"],
        output_dict=True,
        zero_division=0,
    )
    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=["BENIGN", "SUSPICIOUS"],
    )

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        {
            "model": model,
            "feature_names": FEATURE_NAMES,
            "classes": list(model.classes_),
            "training_data_type": "synthetic",
            "held_out_scenario_families": held_out_families,
        },
        MODEL_PATH,
    )

    metrics = {
        "dataset": str(DATASET_PATH),
        "training_data_type": "synthetic",
        "total_samples": int(len(df)),
        "training_samples": int(len(X_train)),
        "testing_samples": int(len(X_test)),
        "feature_count": len(FEATURE_NAMES),
        "held_out_scenario_families": held_out_families,
        "accuracy": float(accuracy),
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_labels": [
            "BENIGN",
            "SUSPICIOUS",
        ],
    }

    with METRICS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(metrics, file, indent=4)

    print("ADIS SUPERVISED MODEL TRAINING")
    print("=" * 40)
    print(f"Dataset samples: {len(df)}")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    print(f"Feature count: {len(FEATURE_NAMES)}")
    print(f"Held-out scenarios: {held_out_families}")
    print(f"Accuracy: {accuracy:.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            labels=["BENIGN", "SUSPICIOUS"],
            zero_division=0,
        )
    )

    print("Confusion matrix")
    print("Rows = actual; columns = predicted")
    print("Labels: BENIGN, SUSPICIOUS")
    print(matrix)

    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")
    print(
        "\nWARNING: Results use synthetic data and do not "
        "establish real-world malware detection accuracy."
    )


if __name__ == "__main__":
    main()
