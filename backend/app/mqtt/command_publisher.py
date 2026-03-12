from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.mqtt.client import BackendMqttClient
from app.mqtt.topics import command_topic


class CommandPublisher:
    def __init__(self, mqtt_client: BackendMqttClient) -> None:
        self.mqtt_client = mqtt_client

    def publish_stop_critico(
        self,
        *,
        zone: str,
        rack: str,
        reason: str,
        correlation_id: str | None = None,
    ) -> dict:
        command = {
            "command_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone": zone,
            "rack": rack,
            "action": "stop_critico",
            "reason": reason,
            "correlation_id": correlation_id or str(uuid4()),
        }
        self.mqtt_client.publish(command_topic(zone, rack), json.dumps(command))
        return command