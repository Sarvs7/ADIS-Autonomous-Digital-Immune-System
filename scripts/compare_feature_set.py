
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "synthetic_behavior.csv"

ALL_FEATURES = [
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

HELD_OUT_FAMILIES = [
    "cloud_sync",
    "file_copy",
    "rapid_file_deletion",
    "mixed_activity",
]


def evaluate_model(df, features, title):
    test_mask = df["scenario_family"].isin(HELD_OUT_FAMILIES)

    X_train = df.loc[~test_mask, features]
    y_train = df.loc[~test_mask, "label"]
    X_test = df.loc[test_mask, features]
    y_test = df.loc[test_mask, "label"]

    model = make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced",
            min_samples_leaf=2,
            n_jobs=-1,
        ),
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=["BENIGN", "SUSPICIOUS"],
    )

    print(f"\n{'=' * 50}")
    print(title)
    print(f"{'=' * 50}")
    print(f"Features used: {len(features)}")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
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

    print("Confusion matrix (actual rows, predicted columns):")
    print("Labels: BENIGN, SUSPICIOUS")
    print(matrix)

    return {
        "model": model,
        "accuracy": accuracy,
        "matrix": matrix,
    }


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    required = ALL_FEATURES + ["label", "scenario_family"]
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Dataset is missing columns: {missing}")

    if df[required].isnull().any().any():
        raise ValueError("Required dataset columns contain missing values.")

    if set(df["label"].unique()) != {"BENIGN", "SUSPICIOUS"}:
        raise ValueError("Dataset contains unexpected labels.")

    if not set(HELD_OUT_FAMILIES).issubset(set(df["scenario_family"])):
        raise ValueError("One or more held-out scenario families are missing.")

    without_age = [
        feature
        for feature in ALL_FEATURES
        if feature != "process_age_seconds"
    ]

    print("ADIS FEATURE-SET COMPARISON")
    print("Dataset: synthetic_behavior.csv")
    print(f"Held-out scenarios: {HELD_OUT_FAMILIES}")
    print(
        "\nThis compares feature sets on the same synthetic test rows. "
        "It does not establish real-world detection performance."
    )

    full_result = evaluate_model(
        df,
        ALL_FEATURES,
        "MODEL A: ALL 18 FEATURES",
    )

    reduced_result = evaluate_model(
        df,
        without_age,
        "MODEL B: WITHOUT process_age_seconds",
    )

    difference = reduced_result["accuracy"] - full_result["accuracy"]

    print(f"\n{'=' * 50}")
    print("COMPARISON SUMMARY")
    print(f"{'=' * 50}")
    print(f"All features accuracy: {full_result['accuracy']:.4f}")
    print(f"Without process age:   {reduced_result['accuracy']:.4f}")
    print(f"Accuracy difference:   {difference:+.4f}")
    print(
        "\nInterpretation: a performance drop suggests the model relies "
        "on process age. It does not prove process age is a valid or "
        "invalid real-world indicator."
    )


if __name__ == "__main__":
    main()
