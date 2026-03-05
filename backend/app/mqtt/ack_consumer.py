from __future__ import annotations

from app.db.session import SessionLocal
from app.mqtt.schemas import AckPayload
from app.mqtt.topics import parse_rack_from_topic
from app.services.audit_service import AuditService


class AckConsumer:
    def handle_message(self, topic: str, payload: dict) -> None:
        parsed = AckPayload.model_validate(payload)
        rack_target = parse_rack_from_topic(topic)
        with SessionLocal() as db:
            AuditService(db).record(
                "edge_ack",
                zone=rack_target.zone if rack_target else None,
                rack=rack_target.rack if rack_target else None,
                command_id=parsed.command_id,
                details={"status": parsed.status, "details": parsed.details, "topic": topic},
            )
