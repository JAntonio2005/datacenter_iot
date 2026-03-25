from __future__ import annotations

import json
from contextlib import AbstractContextManager
from typing import Any

from app.mqtt.telemetry_consumer import TelemetryConsumer


class DummyEngine:
    def __init__(self) -> None:
        self.called = False

    def evaluate(self, **_: Any) -> None:
        self.called = True


class FakeSession(AbstractContextManager):
    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def add(self, obj: Any) -> None:
        return None

    def commit(self) -> None:
        return None

    def refresh(self, obj: Any) -> None:
        return None


def _base_payload() -> dict[str, Any]:
    return {
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "host": "host-1",
        "container_id": "cid-1",
        "container_name": "svc-1",
        "cpu_pct": 10.0,
        "ram_mb": 128.0,
        "net_rx": 1.0,
        "net_tx": 1.0,
        "io_read": 1.0,
        "io_write": 1.0,
        "temp_c": 41.0,
        "hum_pct": 50.0,
        "power_w": 100.0,
    }


def test_payload_edge_cases_rejected(monkeypatch) -> None:
    import app.mqtt.telemetry_consumer as module

    class FakeIdempotencyRepo:
        def __init__(self, db: Any, source: str) -> None:
            self.db = db

        def has_seen(self, message_id: str) -> bool:
            return False

        def mark_seen(self, message_id: str) -> None:
            return None

    events: list[str] = []

    class FakeAuditService:
        def __init__(self, db: Any) -> None:
            self.db = db

        def record(self, event_type: str, **kwargs: Any) -> None:
            events.append(event_type)

    monkeypatch.setattr(module, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(module, "AuditService", FakeAuditService)
    monkeypatch.setattr(module, "IdempotencyRepository", FakeIdempotencyRepo)

    engine = DummyEngine()
    consumer = TelemetryConsumer(engine)

    bad_missing_required = _base_payload()
    bad_missing_required.pop("timestamp")

    monkeypatch.setattr(module, "resolve_rack_id", lambda db, zone, rack: 1)
    consumer.handle_message("topic", json.dumps(bad_missing_required).encode("utf-8"))

    monkeypatch.setattr(module, "resolve_rack_id", lambda db, zone, rack: None)
    consumer.handle_message("topic", json.dumps(_base_payload()).encode("utf-8"))

    missing_container_id = _base_payload()
    missing_container_id.pop("container_id")
    monkeypatch.setattr(module, "resolve_rack_id", lambda db, zone, rack: 1)
    consumer.handle_message("topic", json.dumps(missing_container_id).encode("utf-8"))

    assert engine.called is False
    assert events.count("telemetry_rejected") >= 3
