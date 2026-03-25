from __future__ import annotations

import json
import logging
from collections.abc import Mapping

from app.db.inventory import resolve_rack_id
from app.db.session import SessionLocal
from app.mqtt.schemas import AckPayload
from app.mqtt.topics import parse_rack_from_topic
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AckConsumer:
    def handle_message(self, topic: str, payload: bytes) -> None:
        raw = json.loads(payload.decode("utf-8"))

        if not isinstance(raw, Mapping):
            raise ValueError("ack payload must be a JSON object")

        parsed = AckPayload.model_validate(raw)
        rack_target = parse_rack_from_topic(topic)

        with SessionLocal() as db:
            rack_id = (
                resolve_rack_id(db, rack_target.zone, rack_target.rack)
                if rack_target is not None
                else None
            )

            logger.info(
                "edge ack received",
                extra={
                    "event": "edge_ack",
                    "flow": "ack",
                    "zone": rack_target.zone if rack_target else None,
                    "rack": rack_target.rack if rack_target else None,
                    "rack_id": rack_id,
                    "command_id": parsed.command_id,
                },
            )

            AuditService(db).record(
                "edge_ack",
                rack_id=rack_id,
                zone=rack_target.zone if rack_target else None,
                rack=rack_target.rack if rack_target else None,
                command_id=parsed.command_id,
                details={
                    "status": parsed.status,
                    "details": parsed.details,
                    "topic": topic,
                },
            )