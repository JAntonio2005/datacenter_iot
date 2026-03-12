from __future__ import annotations

import os

from fastapi import FastAPI

from app.core.logging import configure_logging
from app.mqtt.ack_consumer import AckConsumer
from app.mqtt.client import BackendMqttClient
from app.mqtt.command_publisher import CommandPublisher
from app.mqtt.telemetry_consumer import TelemetryConsumer
from app.rules.engine import RulesEngine

app = FastAPI(title="SEDCM Backend", version="0.1.0")

mqtt_client: BackendMqttClient | None = None


@app.on_event("startup")
def startup() -> None:
    global mqtt_client
    configure_logging()

    mqtt_host = os.getenv("MQTT_HOST", "mosquitto")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))

    ack_consumer = AckConsumer()
    publisher = CommandPublisher(None)  # placeholder temporal
    telemetry_consumer = TelemetryConsumer(RulesEngine(publisher))

    mqtt_client = BackendMqttClient(
        host=mqtt_host,
        port=mqtt_port,
        on_telemetry=telemetry_consumer.handle_message,
        on_event=ack_consumer.handle_message,
    )

    # ya con el cliente real, lo inyectamos al publisher
    publisher.mqtt_client = mqtt_client

    mqtt_client.connect()


@app.on_event("shutdown")
def shutdown() -> None:
    global mqtt_client
    if mqtt_client is None:
        return
    mqtt_client.disconnect()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}