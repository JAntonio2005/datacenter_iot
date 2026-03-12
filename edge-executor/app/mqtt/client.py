from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class EdgeMqttClient:
    def __init__(self) -> None:
        self.host = os.getenv("MQTT_HOST", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Router principal (soporta + y #)
        self.client.on_message = self._on_message
        self._routes: list[tuple[str, Callable[[str, dict[str, Any]], None]]] = []

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        logger.info("edge mqtt connected", extra={"extra": {"host": self.host, "port": self.port}})

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        logger.warning("edge mqtt disconnected", extra={"extra": {"reason": str(reason_code)}})

    def connect(self) -> None:
        # backoff automático si se cae
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

        # Reintento robusto (DNS/broker no listo aún)
        last_err: Exception | None = None
        for attempt in range(1, 61):  # ~2 min máx (60*2s)
            try:
                self.client.connect(self.host, self.port, keepalive=30)
                return
            except Exception as e:
                last_err = e
                logger.warning(
                    "edge mqtt connect failed, retrying",
                    extra={"extra": {"attempt": attempt, "host": self.host, "port": self.port, "error": str(e)}},
                )
                time.sleep(2)

        # si después de reintentos no conecta, ya sí truenas con mensaje claro
        raise RuntimeError(f"edge mqtt could not connect to {self.host}:{self.port}: {last_err}")

    def loop_start(self) -> None:
        self.client.loop_start()

    def subscribe(self, topic_filter: str, callback: Callable[[str, dict[str, Any]], None]) -> None:
        # Suscripción real con wildcard
        self.client.subscribe(topic_filter, qos=1)
        # Registrar handler
        self._routes.append((topic_filter, callback))

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        # Matcheo por filtros (+ y #)
        matched = [cb for flt, cb in self._routes if mqtt.topic_matches_sub(flt, msg.topic)]
        if not matched:
            return

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            logger.warning("edge mqtt received invalid json", extra={"extra": {"topic": msg.topic}})
            return

        for cb in matched:
            try:
                cb(msg.topic, payload)
            except Exception as exc:
                logger.exception(
                    "edge mqtt callback failed",
                    extra={"extra": {"topic": msg.topic, "error": str(exc)}},
                )

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.client.publish(topic, json.dumps(payload), qos=1)

    def loop_stop(self) -> None:
        self.client.loop_stop()

    def disconnect(self) -> None:
        self.client.disconnect()