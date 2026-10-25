import time
from typing import Callable

import psutil

from engine.events import SecurityEvent, now_utc


class NetworkSensor:

    def __init__(
        self,
        callback: Callable[[SecurityEvent], None],
        interval: float = 5.0
    ):
        self.callback = callback
        self.interval = interval
        self.running = False
        self.previous_connections = set()

    def get_connections(self):

        connections = set()

        try:
            for connection in psutil.net_connections(
                kind="inet"
            ):

                if connection.status != "ESTABLISHED":
                    continue

                local = connection.laddr

                if connection.raddr:
                    remote = connection.raddr
                else:
                    remote = None

                key = (
                    connection.pid,
                    local.ip if local else None,
                    local.port if local else None,
                    remote.ip if remote else None,
                    remote.port if remote else None,
                )

                connections.add(key)

        except (
            psutil.AccessDenied,
            PermissionError
        ):
            pass

        return connections

    def get_process_details(self, pid):

        if pid is None:
            return None

        try:
            process = psutil.Process(pid)

            return {
                "name": process.name(),
                "exe": process.exe(),
            }

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):
            return None

    def scan_once(self):

        current_connections = (
            self.get_connections()
        )

        new_connections = (
            current_connections -
            self.previous_connections
        )

        for connection in new_connections:

            (
                pid,
                local_ip,
                local_port,
                remote_ip,
                remote_port,
            ) = connection

            process_details = (
                self.get_process_details(pid)
            )

            process_name = None
            executable = None

            if process_details:

                process_name = process_details["name"]
                executable = process_details["exe"]

            event = SecurityEvent(
                event_type="network_connection",
                timestamp=now_utc(),
                pid=pid,
                process_name=process_name,
                executable=executable,
                data={
                    "local_ip": local_ip,
                    "local_port": local_port,
                    "remote_ip": remote_ip,
                    "remote_port": remote_port,
                }
            )

            self.callback(event)

        self.previous_connections = (
            current_connections
        )

    def run(self):

        self.running = True

        self.previous_connections = (
            self.get_connections()
        )

        while self.running:

            try:
                self.scan_once()

            except Exception as error:
                print(
                    f"Network sensor error: {error}"
                )

            time.sleep(self.interval)

    def stop(self):

        self.running = False