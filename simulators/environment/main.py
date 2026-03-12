import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

ZONES = ["A", "B"]
RACKS_BY_ZONE = {"A": ["A1", "A2", "A3"], "B": ["B1", "B2", "B3"]}

HOST = "env-sim"

BASE_TEMP = 24.0
BASE_HUM = 55.0

PIKE_TEMP = 45.0

SPIKE_EVERY_SEC = 15  # fuerza CRITICAL en pruebas (A/A1)


def now_iso():
    # Pydantic acepta ISO con timezone
    return datetime.now(timezone.utc).isoformat()


def topic(zone: str, rack: str) -> str:
    # Tu backend consume con wildcard en telemetria; este formato es consistente
    return f"dc/telemetria/zona/{zone}/rack/{rack}/host/{HOST}/contenedor/environment-simulator"


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()

    temps = {(z, r): BASE_TEMP + random.uniform(-0.8, 0.8) for z in ZONES for r in RACKS_BY_ZONE[z]}
    hums = {(z, r): BASE_HUM + random.uniform(-2.0, 2.0) for z in ZONES for r in RACKS_BY_ZONE[z]}

    t0 = time.time()
    tick = 0

    while True:
        tick += 1
        elapsed = int(time.time() - t0)
        do_spike = (elapsed > 0 and elapsed % SPIKE_EVERY_SEC == 0)

        for z in ZONES:
            for r in RACKS_BY_ZONE[z]:
                temps[(z, r)] += random.uniform(-0.4, 0.4)
                hums[(z, r)] += random.uniform(-1.2, 1.2)

                temps[(z, r)] = max(16.0, min(45.0, temps[(z, r)]))
                hums[(z, r)] = max(20.0, min(90.0, hums[(z, r)]))

                temp_out = SPIKE_TEMP if do_spike and (z == "A" and r == "A1") else temps[(z, r)]

                # Payload PLANO = TelemetryPayload (backend/schemas.py)
                payload = {
                    "timestamp": now_iso(),
                    "zone": z,
                    "rack": r,
                    "host": HOST,
                    "container_id": f"env-{z}-{r}",
                    "container_name": "environment-simulator",
                    "cpu_pct": round(random.uniform(0.5, 8.0), 2),
                    "ram_mb": round(random.uniform(40.0, 180.0), 2),
                    "net_rx": round(random.uniform(0.0, 3000.0), 2),
                    "net_tx": round(random.uniform(0.0, 3000.0), 2),
                    "io_read": round(random.uniform(0.0, 5000.0), 2),
                    "io_write": round(random.uniform(0.0, 5000.0), 2),
                    "temp_c": round(temp_out, 2),
                    "hum_pct": round(hums[(z, r)], 2),
                    "power_w": round(random.uniform(20.0, 120.0), 2),
                }

                client.publish(topic(z, r), json.dumps(payload), qos=1)

        print(f"[env] tick={tick} spike={do_spike} published")
        time.sleep(2)


if __name__ == "__main__":
    main()