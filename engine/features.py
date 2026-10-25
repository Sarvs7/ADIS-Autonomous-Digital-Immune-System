FEATURE_NAMES = [
    "event_count",
    "process_starts",
    "process_stops",
    "process_snapshots",
    "file_creates",
    "file_modifies",
    "file_deletes",
    "network_connections",
]


def extract_features(summary: dict) -> dict:
    """
    Convert a behavior summary into numerical features.
    """

    return {
        name: float(summary.get(name, 0))
        for name in FEATURE_NAMES
    }


def feature_vector(summary: dict) -> list[float]:
    """
    Return features in a fixed order for ML models.
    """

    features = extract_features(summary)

    return [
        features[name]
        for name in FEATURE_NAMES
    ]