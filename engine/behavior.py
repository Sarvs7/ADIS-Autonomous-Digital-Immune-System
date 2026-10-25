from collections import defaultdict, deque
from datetime import timedelta

from engine.events import SecurityEvent


class BehaviorCorrelator:

    def __init__(
        self,
        window_seconds: int = 60
    ):
        self.window_seconds = window_seconds

        self.events_by_pid = defaultdict(
            deque
        )

    def add_event(
        self,
        event: SecurityEvent
    ):

        if event.pid is None:
            return

        events = self.events_by_pid[
            event.pid
        ]

        events.append(event)

        self._cleanup(event.pid)

    def _cleanup(self, pid: int):

        events = self.events_by_pid[pid]

        if not events:
            return

        newest = events[-1].timestamp

        cutoff = (
            newest -
            timedelta(
                seconds=self.window_seconds
            )
        )

        while (
            events
            and events[0].timestamp < cutoff
        ):
            events.popleft()

    def get_events(self, pid: int):

        self._cleanup(pid)

        return list(
            self.events_by_pid[pid]
        )

    def summarize(self, pid: int):

        events = self.get_events(pid)

        summary = {
            "pid": pid,
            "event_count": len(events),

            "process_starts": 0,
            "process_stops": 0,

            "process_snapshots": 0,

            "file_creates": 0,
            "file_modifies": 0,
            "file_deletes": 0,

            "network_connections": 0,
        }

        for event in events:

            event_type = event.event_type

            if event_type == "process_start":
                summary["process_starts"] += 1

            elif event_type == "process_stop":
                summary["process_stops"] += 1

            elif event_type == "process_snapshot":
                summary["process_snapshots"] += 1

            elif event_type == "file_created":
                summary["file_creates"] += 1

            elif event_type == "file_modified":
                summary["file_modifies"] += 1

            elif event_type == "file_deleted":
                summary["file_deletes"] += 1

            elif event_type == "network_connection":
                summary["network_connections"] += 1

        return summary