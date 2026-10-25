import csv
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.anomaly import AnomalyDetector
from engine.behavior import BehaviorCorrelator
from engine.events import SecurityEvent
from engine.features import FEATURE_NAMES, feature_vector
from sensors.process_sensor import ProcessSensor


BASELINE_SECONDS = 60

DATASET_PATH = PROJECT_ROOT / "data" / "normal_behavior.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "anomaly_model.pkl"


class BaselineCollector:

    def __init__(self):

        self.correlator = BehaviorCorrelator(
            window_seconds=60
        )

        self.vectors = []

    def receive_event(
        self,
        event: SecurityEvent
    ):

        self.correlator.add_event(event)

    def collect(self):

        sensor = ProcessSensor(
            callback=self.receive_event,
            interval=2
        )

        print(
            "Collecting normal process behavior..."
        )

        sensor.previous_pids = (
            sensor.get_current_processes()
        )

        for pid in sensor.previous_pids:
            sensor.get_process_details(pid)

        start_time = time.time()

        while (
            time.time() - start_time
            < BASELINE_SECONDS
        ):

            sensor.scan_once()

            for pid in list(
                sensor.previous_pids
            ):

                summary = (
                    self.correlator.summarize(pid)
                )

                if summary["event_count"] == 0:
                    continue

                vector = feature_vector(
                    summary
                )

                self.vectors.append(
                    vector
                )

            time.sleep(
                sensor.interval
            )

        print(
            f"Collected {len(self.vectors)} "
            "behavior vectors."
        )

        return self.vectors


def save_dataset(vectors):

    DATASET_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        DATASET_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            FEATURE_NAMES
        )

        writer.writerows(
            vectors
        )

    print(
        f"Saved baseline dataset to: "
        f"{DATASET_PATH}"
    )


def print_statistics(vectors):

    print()
    print("Baseline dataset statistics:")
    print(
        f"  Samples: {len(vectors)}"
    )
    print(
        f"  Features: {len(FEATURE_NAMES)}"
    )

    for index, name in enumerate(
        FEATURE_NAMES
    ):

        values = [
            row[index]
            for row in vectors
        ]

        print(
            f"  {name}: "
            f"min={min(values):.2f}, "
            f"max={max(values):.2f}, "
            f"mean={sum(values) / len(values):.2f}"
        )


def main():

    collector = BaselineCollector()

    vectors = collector.collect()

    if len(vectors) < 10:

        print(
            "Not enough baseline data."
        )

        return

    save_dataset(
        vectors
    )

    print_statistics(
        vectors
    )

    detector = AnomalyDetector(
        MODEL_PATH
    )

    detector.train(
        vectors
    )

    print()
    print(
        "Baseline model trained successfully."
    )

    print(
        f"Saved to: {MODEL_PATH}"
    )


if __name__ == "__main__":
    main()