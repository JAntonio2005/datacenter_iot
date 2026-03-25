from __future__ import annotations

from datetime import datetime, timezone

from app.db.models import TelemetrySample
from app.rules.engine import RulesEngine


class FakePublisher:
    def __init__(self) -> None:
        self.called = False

    def publish_stop_critico(self, *, zone: str, rack: str, reason: str):
        self.called = True
        return {
            "command_id": "cmd-1",
            "correlation_id": "corr-1",
            "zone": zone,
            "rack": rack,
            "action": "stop_critico",
            "reason": reason,
        }


class FakeDB:
    def __init__(self) -> None:
        self.state = None

    def get(self, model, key):
        return self.state

    def add(self, obj):
        if getattr(obj, "__tablename__", "") == "estado_rack":
            self.state = obj

    def commit(self):
        return None


def test_stop_critico_emitted_on_critical_transition(monkeypatch) -> None:
    import app.rules.engine as module

    events: list[str] = []

    monkeypatch.setattr(module, "resolve_rack_id", lambda db, zone, rack: 7)

    class FakeAuditService:
        def __init__(self, db):
            self.db = db

        def record(self, event_type: str, **kwargs):
            events.append(event_type)

    monkeypatch.setattr(module, "AuditService", FakeAuditService)

    telemetry = TelemetrySample(
        ts=datetime.now(timezone.utc),
        zone="A",
        rack="A1",
        host="h1",
        container_id="c1",
        container_name="svc",
        cpu_pct=10.0,
        ram_mb=128.0,
        temp_c=46.0,
        hum_pct=50.0,
        payload={},
    )

    publisher = FakePublisher()
    engine = RulesEngine(publisher)
    engine.evaluate(db=FakeDB(), telemetry=telemetry)

    assert publisher.called is True
    assert "command_emitted" in events
