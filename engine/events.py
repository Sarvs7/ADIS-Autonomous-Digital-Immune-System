from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SecurityEvent:
    """
    Standard event format used throughout ADIS.
    """

    event_type: str
    timestamp: datetime

    pid: int | None = None
    process_name: str | None = None
    executable: str | None = None

    data: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:

        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "pid": self.pid,
            "process_name": self.process_name,
            "executable": self.executable,
            "data": self.data,
        }


def now_utc() -> datetime:
    return datetime.now(timezone.utc)