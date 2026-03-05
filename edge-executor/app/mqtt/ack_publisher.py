from __future__ import annotations

from datetime import datetime, timezone

from app.mqtt.client import EdgeMqttClient


class AckPublisher:
    def __init__(self, mqtt_client: EdgeMqttClient) -> None:
        self.mqtt_client = mqtt_client

    def publish(self, *, zone: str, rack: str, command_id: str, status: str, details: str) -> None:
        topic = f"dc/eventos/zona/{zone}/rack/{rack}"
        payload = {
            "command_id": command_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "details": details,
        }
        self.mqtt_client.publish(topic, payload)
