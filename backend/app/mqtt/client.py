from __future__ import annotations

import time

import paho.mqtt.client as mqtt

from app.core.logging import get_logger

logger = get_logger(__name__)


class BackendMqttClient:
    def __init__(self, host: str, port: int, on_telemetry, on_event) -> None:
        self.host = host
        self.port = port
        self.on_telemetry = on_telemetry
        self.on_event = on_event

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def connect(self) -> None:
        attempts = 0
        while True:
            try:
                attempts += 1
                logger.info(
                    "backend mqtt connecting",
                    extra={"host": self.host, "port": self.port, "attempt": attempts},
                )
                self.client.connect(self.host, self.port, keepalive=30)
                self.client.loop_start()
                return
            except Exception as e:
                logger.warning(
                    "backend mqtt connect failed; retrying",
                    extra={
                        "host": self.host,
                        "port": self.port,
                        "attempt": attempts,
                        "error": str(e),
                    },
                )
                time.sleep(3)

    def disconnect(self) -> None:
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    def publish(self, topic: str, payload: str) -> None:
        self.client.publish(topic, payload)

    def _on_connect(self, client, userdata, flags, rc):
        logger.info(
            "backend mqtt connected",
            extra={"host": self.host, "port": self.port, "rc": rc},
        )
        client.subscribe("dc/telemetria/#")
        client.subscribe("dc/eventos/#")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning("backend mqtt disconnected", extra={"reason": rc})

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            if mqtt.topic_matches_sub("dc/telemetria/#", topic):
                self.on_telemetry(topic, msg.payload)
            elif mqtt.topic_matches_sub("dc/eventos/#", topic):
                self.on_event(topic, msg.payload)
        except Exception as e:
            logger.error(
                "backend mqtt callback failed",
                extra={"topic": topic, "error": str(e)},
            )