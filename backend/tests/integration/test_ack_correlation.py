from __future__ import annotations

import json
from contextlib import AbstractContextManager
from typing import Any

from app.mqtt.ack_consumer import AckConsumer


class FakeSession(AbstractContextManager):
    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_ack_correlation_and_edge_ack_audit(monkeypatch) -> None:
    import app.mqtt.ack_consumer as module

    captured: list[dict[str, Any]] = []

    class FakeAuditService:
        def __init__(self, db: Any) -> None:
            self.db = db

        def record(self, event_type: str, **kwargs: Any) -> None:
            captured.append({"event_type": event_type, **kwargs})

    monkeypatch.setattr(module, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(module, "AuditService", FakeAuditService)
    monkeypatch.setattr(module, "resolve_rack_id", lambda db, zone, rack: 11)

    payload = {
        "command_id": "cmd-001",
        "timestamp": "2026-03-04T12:00:01Z",
        "status": "ok",
        "details": "done",
    }

    AckConsumer().handle_message("dc/eventos/zona/A/rack/A1", json.dumps(payload).encode("utf-8"))

    assert len(captured) == 1
    assert captured[0]["event_type"] == "edge_ack"
    assert captured[0]["command_id"] == "cmd-001"
    assert captured[0]["rack_id"] == 11
