from __future__ import annotations

import logging

from app.core.idempotency import InMemoryIdempotencyStore
from app.docker.docker_client import DockerAdapter
from app.mqtt.ack_publisher import AckPublisher

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, *, docker_adapter: DockerAdapter, ack_publisher: AckPublisher, idempotency: InMemoryIdempotencyStore) -> None:
        self.docker_adapter = docker_adapter
        self.ack_publisher = ack_publisher
        self.idempotency = idempotency

    def handle_message(self, topic: str, payload: dict) -> None:
        command_id = payload.get("command_id")
        zone = payload.get("zone")
        rack = payload.get("rack")
        action = payload.get("action")

        if not isinstance(command_id, str) or not isinstance(zone, str) or not isinstance(rack, str):
            logger.error("invalid command payload", extra={"extra": {"topic": topic, "payload": payload}})
            return

        if not isinstance(action, str):
            self.ack_publisher.publish(zone=zone, rack=rack, command_id=command_id, status="fail", details="missing action")
            return

        if self.idempotency.has_seen(command_id):
            self.ack_publisher.publish(zone=zone, rack=rack, command_id=command_id, status="ok", details="duplicate command ignored")
            return

        self.idempotency.mark_seen(command_id)

        if action != "stop_critico":
            self.ack_publisher.publish(zone=zone, rack=rack, command_id=command_id, status="fail", details="unsupported action")
            return

        ok, details = self.docker_adapter.stop_critical_container(zone=zone, rack=rack)
        self.ack_publisher.publish(zone=zone, rack=rack, command_id=command_id, status="ok" if ok else "fail", details=details)
