from __future__ import annotations

from app.mqtt.telemetry_fusion import TelemetryFusion


def test_fusion_fills_missing_ambient_values_for_same_rack() -> None:
    fusion = TelemetryFusion()

    ambient_message = {
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "temp_c": 46.2,
        "hum_pct": 42.0,
        "power_w": 190.0,
    }
    fused_ambient = fusion.merge(ambient_message)
    assert fused_ambient["temp_c"] == 46.2

    container_message_without_ambient = {
        "timestamp": "2026-03-04T12:00:01Z",
        "zone": "A",
        "rack": "A1",
        "host": "node-a1",
        "container_id": "c-1",
        "container_name": "critical-a1",
        "cpu_pct": 88.5,
        "ram_mb": 1024.0,
        "net_rx": 50.0,
        "net_tx": 20.0,
        "io_read": 4.0,
        "io_write": 3.0,
    }

    fused = fusion.merge(container_message_without_ambient)

    assert fused["temp_c"] == 46.2
    assert fused["hum_pct"] == 42.0
    assert fused["power_w"] == 190.0
