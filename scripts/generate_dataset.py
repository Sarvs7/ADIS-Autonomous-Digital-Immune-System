
import csv
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "synthetic_behavior.csv"

SAMPLES_PER_SCENARIO = 250
RANDOM_SEED = 42

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

SCENARIOS = {
    # BENIGN scenarios
    "browser_activity": {
        "label": "BENIGN",
        "process_starts": (0, 2),
        "cpu": (1, 35),
        "memory": (2, 45),
        "threads": (5, 80),
        "children": (0, 3),
        "age": (60, 86400),
        "creates": (0, 8),
        "modifies": (0, 25),
        "deletes": (0, 5),
        "connections": (0, 25),
        "remote_ips": (0, 12),
        "remote_ports": (0, 8),
    },
    "ide_build": {
        "label": "BENIGN",
        "process_starts": (0, 12),
        "cpu": (10, 95),
        "memory": (5, 75),
        "threads": (5, 100),
        "children": (0, 15),
        "age": (10, 86400),
        "creates": (0, 80),
        "modifies": (0, 150),
        "deletes": (0, 25),
        "connections": (0, 12),
        "remote_ips": (0, 5),
        "remote_ports": (0, 8),
    },
    "file_copy": {
        "label": "BENIGN",
        "process_starts": (0, 2),
        "cpu": (1, 30),
        "memory": (1, 35),
        "threads": (1, 30),
        "children": (0, 2),
        "age": (30, 86400),
        "creates": (5, 100),
        "modifies": (0, 30),
        "deletes": (0, 10),
        "connections": (0, 3),
        "remote_ips": (0, 2),
        "remote_ports": (0, 3),
    },
    "cloud_sync": {
        "label": "BENIGN",
        "process_starts": (0, 2),
        "cpu": (1, 35),
        "memory": (2, 50),
        "threads": (3, 60),
        "children": (0, 3),
        "age": (60, 86400),
        "creates": (0, 35),
        "modifies": (0, 80),
        "deletes": (0, 15),
        "connections": (1, 40),
        "remote_ips": (1, 15),
        "remote_ports": (1, 8),
    },

    # CONTROLLED SUSPICIOUS scenarios
    "rapid_file_modification": {
        "label": "SUSPICIOUS",
        "process_starts": (0, 5),
        "cpu": (5, 90),
        "memory": (2, 70),
        "threads": (2, 100),
        "children": (0, 5),
        "age": (5, 3600),
        "creates": (0, 50),
        "modifies": (60, 300),
        "deletes": (0, 30),
        "connections": (0, 20),
        "remote_ips": (0, 10),
        "remote_ports": (0, 8),
    },
    "rapid_file_deletion": {
        "label": "SUSPICIOUS",
        "process_starts": (0, 5),
        "cpu": (5, 90),
        "memory": (2, 70),
        "threads": (2, 100),
        "children": (0, 5),
        "age": (5, 3600),
        "creates": (0, 30),
        "modifies": (0, 60),
        "deletes": (35, 250),
        "connections": (0, 20),
        "remote_ips": (0, 10),
        "remote_ports": (0, 8),
    },
    "abnormal_process_spawning": {
        "label": "SUSPICIOUS",
        "process_starts": (10, 50),
        "cpu": (5, 90),
        "memory": (2, 70),
        "threads": (5, 120),
        "children": (10, 50),
        "age": (5, 3600),
        "creates": (0, 40),
        "modifies": (0, 60),
        "deletes": (0, 20),
        "connections": (0, 30),
        "remote_ips": (0, 15),
        "remote_ports": (0, 10),
    },
    "mixed_activity": {
        "label": "SUSPICIOUS",
        "process_starts": (5, 30),
        "cpu": (10, 95),
        "memory": (5, 85),
        "threads": (5, 120),
        "children": (3, 30),
        "age": (5, 3600),
        "creates": (20, 120),
        "modifies": (50, 250),
        "deletes": (15, 100),
        "connections": (10, 60),
        "remote_ips": (3, 25),
        "remote_ports": (2, 15),
    },
}


def integer_range(rng, limits):
    return rng.randint(limits[0], limits[1])


def generate_sample(rng, scenario_name, scenario, index):
    cpu_mean = rng.uniform(*scenario["cpu"])
    cpu_max = rng.uniform(cpu_mean, 100)

    memory_mean = rng.uniform(*scenario["memory"])
    memory_max = rng.uniform(memory_mean, 100)

    thread_mean = rng.uniform(*scenario["threads"])
    thread_max = rng.uniform(thread_mean, max(thread_mean, 300))

    creates = integer_range(rng, scenario["creates"])
    modifies = integer_range(rng, scenario["modifies"])
    deletes = integer_range(rng, scenario["deletes"])

    # Generate total connections first so unique counts cannot exceed it.
    connection_count = integer_range(rng, scenario["connections"])

    remote_ips = rng.randint(
        0,
        min(connection_count, scenario["remote_ips"][1]),
    )
    remote_ports = rng.randint(
        0,
        min(connection_count, scenario["remote_ports"][1]),
    )

    total_file_events = creates + modifies + deletes
    unique_files_touched = rng.randint(
        0,
        total_file_events,
    )

    return {
        "scenario_id": f"{scenario_name}_{index:04d}",
        "scenario_family": scenario_name,
        "label": scenario["label"],

        "process_snapshot_count": 30,
        "process_start_count": integer_range(
            rng, scenario["process_starts"]
        ),
        "process_stop_count": rng.randint(0, 3),

        "cpu_mean": round(cpu_mean, 2),
        "cpu_max": round(cpu_max, 2),
        "memory_mean": round(memory_mean, 2),
        "memory_max": round(memory_max, 2),

        "thread_mean": round(thread_mean, 2),
        "thread_max": round(thread_max, 2),

        "child_process_count": integer_range(
            rng, scenario["children"]
        ),
        "process_age_seconds": integer_range(
            rng, scenario["age"]
        ),

        "file_create_count": creates,
        "file_modify_count": modifies,
        "file_delete_count": deletes,
        "unique_files_touched": unique_files_touched,

        "network_connection_count": connection_count,
        "unique_remote_ip_count": remote_ips,
        "unique_remote_port_count": remote_ports,
    }


def main():
    rng = random.Random(RANDOM_SEED)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "scenario_id",
        "scenario_family",
        "label",
        *FEATURE_NAMES,
    ]

    rows = []

    for scenario_name, scenario in SCENARIOS.items():
        for index in range(SAMPLES_PER_SCENARIO):
            rows.append(
                generate_sample(
                    rng,
                    scenario_name,
                    scenario,
                    index,
                )
            )

    rng.shuffle(rows)

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
        )
        writer.writeheader()
        writer.writerows(rows)

    benign_count = sum(
        row["label"] == "BENIGN"
        for row in rows
    )
    suspicious_count = sum(
        row["label"] == "SUSPICIOUS"
        for row in rows
    )

    print("ADIS synthetic dataset generated.")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total samples: {len(rows)}")
    print(f"Features: {len(FEATURE_NAMES)}")
    print(f"Benign samples: {benign_count}")
    print(f"Suspicious samples: {suspicious_count}")
    print(f"Scenario families: {len(SCENARIOS)}")
    print("Note: synthetic data only; not real malware telemetry.")


if __name__ == "__main__":
    main()
