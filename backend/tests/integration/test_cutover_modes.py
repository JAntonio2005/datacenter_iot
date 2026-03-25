from __future__ import annotations

import json
import os
from contextlib import AbstractContextManager
from typing import Any

from app.mqtt.telemetry_consumer import TelemetryConsumer


class DummyEngine:
    def __init__(self) -> None:
        self.called = False

    def evaluate(self, **_: Any) -> None:
        self.called = True


class FakeSession(AbstractContextManager):
    def __init__(self) -> None:
        self.added: list[Any] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        return None

    def refresh(self, obj: Any) -> None:
        return None


def _payload() -> bytes:
    return json.dumps(
        {
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
    ).encode("utf-8")


def test_cutover_modes(monkeypatch) -> None:
    import app.mqtt.telemetry_consumer as module

    class FakeIdempotencyRepo:
        def __init__(self, db: Any, source: str) -> None:
            self.db = db

        def has_seen(self, message_id: str) -> bool:
            return False

        def mark_seen(self, message_id: str) -> None:
            return None

    monkeypatch.setattr(module, "resolve_rack_id", lambda db, zone, rack: 1)
    monkeypatch.setattr(module, "resolve_container_id", lambda db, rack_id, container_name, host, container_id: 10)
    monkeypatch.setattr(module, "IdempotencyRepository", FakeIdempotencyRepo)

    events: list[str] = []

    class FakeAuditService:
        def __init__(self, db: Any) -> None:
            self.db = db

        def record(self, event_type: str, **kwargs: Any) -> None:
            events.append(event_type)

    monkeypatch.setattr(module, "AuditService", FakeAuditService)

    engine = DummyEngine()
    consumer = TelemetryConsumer(engine)

    for mode in ("legacy", "dual", "normalized"):
        session = FakeSession()
        monkeypatch.setattr(module, "SessionLocal", lambda: session)
        monkeypatch.setenv("DB_WRITE_MODE", mode)

        consumer.handle_message("dc/telemetria/zona/A/rack/A1/host/h1/contenedor/c1", _payload())

        table_names = sorted({getattr(obj, "__tablename__", "") for obj in session.added})
        if mode == "legacy":
            assert "telemetry_samples" in table_names
            assert "muestras_telemetria" not in table_names
        elif mode == "normalized":
            assert "muestras_telemetria" in table_names
            assert "telemetry_samples" not in table_names
        else:
            assert "muestras_telemetria" in table_names
            assert "telemetry_samples" in table_names

    monkeypatch.delenv("DB_WRITE_MODE", raising=False)
    assert "telemetry_ingested" in events
