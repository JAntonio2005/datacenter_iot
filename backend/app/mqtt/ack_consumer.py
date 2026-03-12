from __future__ import annotations

import json
from collections.abc import Mapping

from app.db.session import SessionLocal
from app.mqtt.schemas import AckPayload
from app.mqtt.topics import parse_rack_from_topic
from app.services.audit_service import AuditService


class AckConsumer:
    def handle_message(self, topic: str, payload: bytes) -> None:
        raw = json.loads(payload.decode("utf-8"))

        if not isinstance(raw, Mapping):
            raise ValueError("ack payload must be a JSON object")

        parsed = AckPayload.model_validate(raw)
        rack_target = parse_rack_from_topic(topic)

        with SessionLocal() as db:
            AuditService(db).record(
                "edge_ack",
                zone=rack_target.zone if rack_target else None,
                rack=rack_target.rack if rack_target else None,
                command_id=parsed.command_id,
                details={
                    "status": parsed.status,
                    "details": parsed.details,
                    "topic": topic,
                },
            )