from __future__ import annotations

import json
from pathlib import Path

from app.mqtt.schemas import AckPayload, CommandPayload, TelemetryPayload


ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "contracts" / "mqtt"


def test_telemetry_contract_regression() -> None:
    sample = json.loads((CONTRACTS / "telemetry.v1.json").read_text(encoding="utf-8"))
    assert "metadata" in sample
    assert "environment" in sample
    assert "zone" in sample["metadata"]
    assert "rack" in sample["metadata"]

    TelemetryPayload.model_validate({
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "host": "host-1",
        "container_id": "abc123",
        "container_name": "svc",
        "cpu_pct": 12.5,
        "ram_mb": 256.0,
        "net_rx": 100.0,
        "net_tx": 150.0,
        "io_read": 10.0,
        "io_write": 12.0,
    })


def test_command_ack_contract_regression() -> None:
    CommandPayload.model_validate(
        {
            "command_id": "cmd-1",
            "timestamp": "2026-03-04T12:00:00Z",
            "zone": "A",
            "rack": "A1",
            "action": "stop_critico",
            "reason": "temp >= 45",
            "correlation_id": "corr-1",
        }
    )

    AckPayload.model_validate(
        {
            "command_id": "cmd-1",
            "timestamp": "2026-03-04T12:00:01Z",
            "status": "ok",
            "details": "done",
        }
    )
