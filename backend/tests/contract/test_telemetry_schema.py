from __future__ import annotations

import pytest

from app.mqtt.schemas import TelemetryPayload


def test_telemetry_payload_accepts_valid_contract() -> None:
    payload = {
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "host": "host-1",
        "container_id": "abc123",
        "container_name": "critical-service",
        "cpu_pct": 12.5,
        "ram_mb": 256.0,
        "net_rx": 100.0,
        "net_tx": 150.0,
        "io_read": 10.0,
        "io_write": 12.0,
        "temp_c": 43.2,
        "hum_pct": 50.1,
        "power_w": 125.5,
    }

    parsed = TelemetryPayload.model_validate(payload)
    assert parsed.zone == "A"
    assert parsed.rack == "A1"
    assert parsed.temp_c == 43.2


def test_telemetry_payload_rejects_negative_values() -> None:
    payload = {
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "host": "host-1",
        "container_id": "abc123",
        "container_name": "critical-service",
        "cpu_pct": -1.0,
        "ram_mb": 256.0,
        "net_rx": 100.0,
        "net_tx": 150.0,
        "io_read": 10.0,
        "io_write": 12.0,
        "temp_c": 43.2,
        "hum_pct": 50.1,
    }

    with pytest.raises(Exception):
        TelemetryPayload.model_validate(payload)
