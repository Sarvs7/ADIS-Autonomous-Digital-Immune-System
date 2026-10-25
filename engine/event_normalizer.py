from datetime import datetime, timedelta

from engine.events import SecurityEvent


class EventNormalizer:

    def __init__(self, duplicate_window_ms: int = 100):

        self.duplicate_window = timedelta(
            milliseconds=duplicate_window_ms
        )

        self.last_events = {}

    def normalize(
        self,
        event: SecurityEvent
    ) -> SecurityEvent | None:

        path = event.data.get("path")

        if not path:
            return event

        key = (
            event.event_type,
            str(path).lower()
        )

        previous_time = self.last_events.get(key)

        if previous_time is not None:

            difference = (
                event.timestamp -
                previous_time
            )

            if difference <= self.duplicate_window:
                return None

        self.last_events[key] = event.timestamp

        return event