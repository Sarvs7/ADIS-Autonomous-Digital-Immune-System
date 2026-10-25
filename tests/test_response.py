from engine.response import ThreatResponder


def test_normal_response():

    responder = ThreatResponder()

    result = responder.respond(
        pid=1234,
        process_name="test.exe",
        risk_level="NORMAL"
    )

    assert result.action == "ALLOW"
    assert result.verified is True


def test_medium_response():

    responder = ThreatResponder()

    result = responder.respond(
        pid=1234,
        process_name="test.exe",
        risk_level="MEDIUM"
    )

    assert result.action == "ALERT"
    assert result.executed is True


def test_high_response_dry_run():

    responder = ThreatResponder()

    result = responder.respond(
        pid=1234,
        process_name="test.exe",
        risk_level="HIGH"
    )

    assert result.action == "CONTAIN_PROCESS"
    assert result.executed is False
    assert result.verified is True