from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any

from app.mqtt.telemetry_consumer import TelemetryConsumer


class DummyEngine:
    def __init__(self) -> None:
        self.called = False

    def evaluate(self, *, db: Any, telemetry: Any) -> None:
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


def test_invalid_payload_is_rejected_and_audited(monkeypatch) -> None:
    records: list[dict[str, Any]] = []

    class FakeAuditService:
        def __init__(self, db: Any) -> None:
            self.db = db

        def record(
            self,
            event_type: str,
            *,
            zone: str | None = None,
            rack: str | None = None,
            correlation_id: str | None = None,
            command_id: str | None = None,
            details: dict | None = None,
        ) -> None:
            records.append(
                {
                    "event_type": event_type,
                    "zone": zone,
                    "rack": rack,
                    "details": details or {},
                }
            )

    import app.mqtt.telemetry_consumer as telemetry_consumer_module

    monkeypatch.setattr(telemetry_consumer_module, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(telemetry_consumer_module, "AuditService", FakeAuditService)

    engine = DummyEngine()
    consumer = TelemetryConsumer(engine)

    invalid_payload = {
        "timestamp": "2026-03-04T12:00:00Z",
        "zone": "A",
        "rack": "A1",
        "cpu_pct": 10.0,
    }

    consumer.handle_message("dc/telemetria/zona/A/rack/A1/host/h1/contenedor/c1", invalid_payload)

    assert engine.called is False
    assert len(records) == 1
    assert records[0]["event_type"] == "telemetry_rejected"
    assert records[0]["zone"] == "A"
    assert records[0]["rack"] == "A1"
