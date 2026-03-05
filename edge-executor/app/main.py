import os
import time

from app.core.idempotency import InMemoryIdempotencyStore
from app.core.logging import configure_logging
from app.docker.docker_client import DockerAdapter
from app.handlers.command_handler import CommandHandler
from app.mqtt.ack_publisher import AckPublisher
from app.mqtt.client import EdgeMqttClient


def main() -> None:
    configure_logging()
    print("SEDCM Edge Executor started")
    mqtt_host = os.getenv("MQTT_HOST", "mosquitto")
    print(f"MQTT_HOST={mqtt_host}")

    mqtt_client = EdgeMqttClient()
    ack_publisher = AckPublisher(mqtt_client)
    handler = CommandHandler(
        docker_adapter=DockerAdapter(),
        ack_publisher=ack_publisher,
        idempotency=InMemoryIdempotencyStore(),
    )

    mqtt_client.connect()
    mqtt_client.loop_start()
    mqtt_client.subscribe("dc/comandos/zona/+/rack/+", handler.handle_message)

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
