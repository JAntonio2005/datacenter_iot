from __future__ import annotations
from fastapi.middleware.cors import CORSMiddleware
import os

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.logging import configure_logging
from app.mqtt.ack_consumer import AckConsumer
from app.mqtt.client import BackendMqttClient
from app.mqtt.command_publisher import CommandPublisher
from app.mqtt.telemetry_consumer import TelemetryConsumer
from app.rules.engine import RulesEngine

app = FastAPI(title="SEDCM Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    publisher.mqtt_client = mqtt_client
    mqtt_client.connect()


@app.on_event("shutdown")
def shutdown() -> None:
    global mqtt_client
    if mqtt_client is None:
        return
    mqtt_client.disconnect()


app.include_router(api_router)