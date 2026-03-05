from __future__ import annotations

import pytest

from app.mqtt.schemas import AckPayload, CommandPayload


def test_command_payload_accepts_stop_critico() -> None:
    payload = {
        "command_id": "cmd-001",
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "action": "stop_critico",
        "reason": "temp >= T2",
        "correlation_id": "corr-001",
    }

    parsed = CommandPayload.model_validate(payload)
    assert parsed.action == "stop_critico"


def test_command_payload_rejects_unknown_action() -> None:
    payload = {
        "command_id": "cmd-001",
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "action": "restart",
        "reason": "manual",
        "correlation_id": "corr-001",
    }

    with pytest.raises(Exception):
        CommandPayload.model_validate(payload)


def test_ack_payload_accepts_ok_fail_status() -> None:
    ok_payload = {
        "command_id": "cmd-001",
        "timestamp": "2026-03-04T12:00:01Z",
        "status": "ok",
        "details": "stopped",
    }
    fail_payload = {
        "command_id": "cmd-001",
        "timestamp": "2026-03-04T12:00:01Z",
        "status": "fail",
        "details": "not found",
    }

    assert AckPayload.model_validate(ok_payload).status == "ok"
    assert AckPayload.model_validate(fail_payload).status == "fail"
