from engine.collector import EventCollector
from engine.event_bus import EventBus
from engine.events import SecurityEvent, now_utc
from engine.pipeline import DetectionPipeline


def test_collector():

    bus = EventBus()
    pipeline = DetectionPipeline()

    collector = EventCollector(
        bus,
        pipeline
    )

    event = SecurityEvent(
        event_type="process_start",
        timestamp=now_utc(),
        pid=1234,
        process_name="test.exe",
        executable="C:\\test.exe"
    )

    bus.publish(event)

    event_result = collector.process_once()

    assert event_result is not None

    event, result = event_result

    assert event.pid == 1234
    assert result["pid"] == 1234
    assert result["process_name"] == "test.exe"
    assert result["risk"].level == "NORMAL"

    collector.database.close()