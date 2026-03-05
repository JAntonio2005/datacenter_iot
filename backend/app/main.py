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

    mqtt_client = BackendMqttClient()
    publisher = CommandPublisher(mqtt_client)
    telemetry_consumer = TelemetryConsumer(RulesEngine(publisher))
    ack_consumer = AckConsumer()

    mqtt_client.connect()
    mqtt_client.loop_start()
    mqtt_client.subscribe("dc/telemetria/zona/+/rack/+/host/+/contenedor/+", telemetry_consumer.handle_message)
    mqtt_client.subscribe("dc/eventos/zona/+/rack/+", ack_consumer.handle_message)


@app.on_event("shutdown")
def shutdown() -> None:
    global mqtt_client
    if mqtt_client is None:
        return
    mqtt_client.loop_stop()
    mqtt_client.disconnect()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
