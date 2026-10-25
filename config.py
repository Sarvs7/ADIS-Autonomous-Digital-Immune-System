import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    return int(value)


PROCESS_MONITOR_INTERVAL = env_int(
    "PROCESS_MONITOR_INTERVAL",
    2
)

NETWORK_MONITOR_INTERVAL = env_int(
    "NETWORK_MONITOR_INTERVAL",
    5
)

FILE_MONITOR_ENABLED = env_bool(
    "FILE_MONITOR_ENABLED",
    True
)

DRY_RUN = env_bool(
    "DRY_RUN",
    True
)

ANOMALY_DETECTION_ENABLED = env_bool(
    "ANOMALY_DETECTION_ENABLED",
    True
)

RULE_DETECTION_ENABLED = env_bool(
    "RULE_DETECTION_ENABLED",
    True
)

LOW_RISK_THRESHOLD = env_int(
    "LOW_RISK_THRESHOLD",
    30
)

MEDIUM_RISK_THRESHOLD = env_int(
    "MEDIUM_RISK_THRESHOLD",
    60
)

HIGH_RISK_THRESHOLD = env_int(
    "HIGH_RISK_THRESHOLD",
    80
)

DATABASE_PATH = PROJECT_ROOT / os.getenv(
    "DATABASE_PATH",
    "data/adis.db"
)

LOG_FILE = PROJECT_ROOT / os.getenv(
    "LOG_FILE",
    "logs/adis.log"
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)

DASHBOARD_REFRESH_MS = env_int(
    "DASHBOARD_REFRESH_MS",
    1000
)