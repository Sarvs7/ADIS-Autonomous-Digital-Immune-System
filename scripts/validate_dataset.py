import pandas as pd

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT / "data" / "synthetic_behavior.csv"
)

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

METADATA_COLUMNS = [
    "scenario_id",
    "scenario_family",
    "label",
]


def main():
    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found: {DATASET_PATH}")
        return

    df = pd.read_csv(DATASET_PATH)

    print("ADIS DATASET VALIDATION")
    print("=" * 40)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    expected_columns = METADATA_COLUMNS + FEATURE_NAMES

    missing_columns = sorted(
        set(expected_columns) - set(df.columns)
    )
    extra_columns = sorted(
        set(df.columns) - set(expected_columns)
    )

    print(f"Missing columns: {missing_columns}")
    print(f"Unexpected columns: {extra_columns}")

    if missing_columns or extra_columns:
        print("FAIL: Column schema mismatch.")
        return

    print("\nLabel distribution:")
    print(df["label"].value_counts().to_string())

    print("\nScenario distribution:")
    print(
        df.groupby(
            ["scenario_family", "label"]
        ).size().to_string()
    )

    print("\nMissing values:")
    print(int(df.isna().sum().sum()))

    print("\nDuplicate scenario IDs:")
    print(int(df["scenario_id"].duplicated().sum()))

    print("\nDuplicate feature vectors:")
    print(int(df[FEATURE_NAMES].duplicated().sum()))

    numeric = df[FEATURE_NAMES]

    print("\nNon-numeric feature values:")
    print(int(numeric.isna().sum().sum()))

    print("\nNegative feature values:")
    print(int((numeric < 0).sum().sum()))

    print("\nLogical consistency checks:")

    checks = {
        "CPU mean <= CPU maximum":
            (df["cpu_mean"] <= df["cpu_max"]).all(),

        "CPU maximum <= 100":
            (df["cpu_max"] <= 100).all(),

        "Memory mean <= memory maximum":
            (df["memory_mean"] <= df["memory_max"]).all(),

        "Memory maximum <= 100":
            (df["memory_max"] <= 100).all(),

        "Mean threads <= maximum threads":
            (df["thread_mean"] <= df["thread_max"]).all(),

        "Unique files <= total file events":
            (
                df["unique_files_touched"]
                <= df[
                    [
                        "file_create_count",
                        "file_modify_count",
                        "file_delete_count",
                    ]
                ].sum(axis=1)
            ).all(),

        "Unique remote IPs <= connections":
            (
                df["unique_remote_ip_count"]
                <= df["network_connection_count"]
            ).all(),

        "Unique remote ports <= connections":
            (
                df["unique_remote_port_count"]
                <= df["network_connection_count"]
            ).all(),

        "Known labels only":
            df["label"].isin(
                ["BENIGN", "SUSPICIOUS"]
            ).all(),
    }

    for description, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {description}")

    print("\nFeature statistics:")
    print(
        numeric.describe().round(2).to_string()
    )

    print("\nValidation finished.")
    print(
        "Reminder: passing checks does not establish "
        "real-world malware detection accuracy."
    )


if __name__ == "__main__":
    main()