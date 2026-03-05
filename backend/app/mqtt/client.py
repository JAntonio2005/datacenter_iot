from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class BackendMqttClient:
    def __init__(self) -> None:
        self.host = os.getenv("MQTT_HOST", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        logger.info("backend mqtt connected", extra={"extra": {"host": self.host, "port": self.port}})

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        logger.warning("backend mqtt disconnected", extra={"extra": {"reason": str(reason_code)}})

    def connect(self) -> None:
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.connect(self.host, self.port, keepalive=30)

    def loop_start(self) -> None:
        self.client.loop_start()

    def subscribe(self, topic: str, callback: Callable[[str, dict[str, Any]], None]) -> None:
        def _wrapped(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
            except json.JSONDecodeError:
                logger.warning("backend mqtt received invalid json", extra={"extra": {"topic": msg.topic}})
                return

            try:
                callback(msg.topic, payload)
            except Exception as exc:
                logger.exception("backend mqtt callback failed", extra={"extra": {"topic": msg.topic, "error": str(exc)}})

        self.client.message_callback_add(topic, _wrapped)
        self.client.subscribe(topic)

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.client.publish(topic, json.dumps(payload), qos=1)

    def loop_stop(self) -> None:
        self.client.loop_stop()

    def disconnect(self) -> None:
        self.client.disconnect()
