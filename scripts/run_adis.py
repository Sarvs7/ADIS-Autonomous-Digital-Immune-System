import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import threading
import time
from pathlib import Path

from config import (
    FILE_MONITOR_ENABLED,
    NETWORK_MONITOR_INTERVAL,
    PROCESS_MONITOR_INTERVAL,
)

from engine.collector import EventCollector
from engine.event_bus import EventBus
from engine.pipeline import DetectionPipeline
from sensors.file_sensor import FileSensor
from sensors.network_sensor import NetworkSensor
from sensors.process_sensor import ProcessSensor


def main():

    print("=" * 60)
    print("ADIS - Autonomous Digital Immune System")
    print("=" * 60)

    # Central event queue
    event_bus = EventBus()

    # Detection pipeline
    pipeline = DetectionPipeline()

    # Event collector
    collector = EventCollector(
        event_bus,
        pipeline
    )

    # Process sensor
    process_sensor = ProcessSensor(
        callback=event_bus.publish,
        interval=PROCESS_MONITOR_INTERVAL
    )

    # Network sensor
    network_sensor = NetworkSensor(
        callback=event_bus.publish,
        interval=NETWORK_MONITOR_INTERVAL
    )

    # File sensor
    file_sensor = None

    if FILE_MONITOR_ENABLED:

        watch_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "watch"
        )

        file_sensor = FileSensor(
            watch_path=watch_path,
            callback=event_bus.publish
        )

    # Start collector
    collector_thread = threading.Thread(
        target=collector.run,
        daemon=True
    )

    collector_thread.start()

    # Start process sensor
    process_thread = threading.Thread(
        target=process_sensor.run,
        daemon=True
    )

    process_thread.start()

    # Start network sensor
    network_thread = threading.Thread(
        target=network_sensor.run,
        daemon=True
    )

    network_thread.start()

    # Start file sensor
    if file_sensor is not None:
        file_sensor.start()

    print()
    print("ADIS is running.")
    print("Monitoring:")
    print("  - Processes")
    print("  - Files")
    print("  - Network connections")
    print()
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print("Stopping ADIS...")

        process_sensor.stop()
        network_sensor.stop()
        collector.stop()

        if file_sensor is not None:
            file_sensor.stop()

        process_thread.join(
            timeout=3
        )

        network_thread.join(
            timeout=3
        )

        collector_thread.join(
            timeout=3
        )

        print("ADIS stopped.")


if __name__ == "__main__":
    main()