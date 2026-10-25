import time
from typing import Callable

import psutil

from engine.events import SecurityEvent, now_utc


class ProcessSensor:

    def __init__(
        self,
        callback: Callable[[SecurityEvent], None],
        interval: float = 2.0
    ):
        self.callback = callback
        self.interval = interval
        self.running = False
        self.previous_pids: set[int] = set()

        # Keeps Process objects alive between scans
        # so CPU measurements can be calculated.
        self.process_objects = {}

    def get_current_processes(self) -> set[int]:

        current_pids = set()

        for process in psutil.process_iter(
            ["pid", "name", "exe"]
        ):
            try:
                current_pids.add(
                    process.info["pid"]
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):
                continue

        return current_pids

    def get_process_details(self, pid: int):

        try:

            if pid not in self.process_objects:
                self.process_objects[pid] = (
                    psutil.Process(pid)
                )

            process = self.process_objects[pid]

            return {
                "pid": process.pid,
                "name": process.name(),
                "exe": process.exe(),
                "username": process.username(),
                "status": process.status(),
                "cpu_percent": process.cpu_percent(
                    interval=None
                ),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
            }

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):

            self.process_objects.pop(
                pid,
                None
            )

            return None

    def scan_once(self):

        current_pids = self.get_current_processes()

        started = (
            current_pids -
            self.previous_pids
        )

        stopped = (
            self.previous_pids -
            current_pids
        )

        # Process start events
        for pid in started:

            details = self.get_process_details(pid)

            if details is None:
                continue

            event = SecurityEvent(
                event_type="process_start",
                timestamp=now_utc(),
                pid=pid,
                process_name=details["name"],
                executable=details["exe"],
                data=details
            )

            self.callback(event)

        # Process stop events
        for pid in stopped:

            event = SecurityEvent(
                event_type="process_stop",
                timestamp=now_utc(),
                pid=pid,
                data={}
            )

            self.callback(event)

            self.process_objects.pop(
                pid,
                None
            )

        # Process behavior snapshots
        for pid in current_pids:

            details = self.get_process_details(pid)

            if details is None:
                continue

            event = SecurityEvent(
                event_type="process_snapshot",
                timestamp=now_utc(),
                pid=pid,
                process_name=details["name"],
                executable=details["exe"],
                data=details
            )

            self.callback(event)

        self.previous_pids = current_pids

    def run(self):

        self.running = True

        self.previous_pids = (
            self.get_current_processes()
        )

        # Establish the first CPU measurement.
        for pid in self.previous_pids:
            self.get_process_details(pid)

        while self.running:

            try:
                self.scan_once()

            except Exception as error:
                print(
                    f"Process sensor error: {error}"
                )

            time.sleep(self.interval)

    def stop(self):

        self.running = False