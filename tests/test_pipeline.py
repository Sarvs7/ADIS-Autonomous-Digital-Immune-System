from engine.events import SecurityEvent, now_utc
from engine.pipeline import DetectionPipeline


def test_pipeline_process_event():

    pipeline = DetectionPipeline()

    event = SecurityEvent(
        event_type="process_start",
        timestamp=now_utc(),
        pid=12345,
        process_name="test.exe",
        executable="C:\\test.exe",
        data={}
    )

    result = pipeline.process_event(event)

    assert result is not None
    assert result["pid"] == 12345
    assert result["process_name"] == "test.exe"
    assert "summary" in result
    assert "features" in result
    assert "rules" in result
    assert "risk" in result