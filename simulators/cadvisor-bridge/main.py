from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import requests
import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
CADVISOR_URL = os.getenv("CADVISOR_URL", "http://cadvisor:8080")
INTERVAL_SEC = float(os.getenv("INTERVAL_SEC", "2.0"))

# Prefijo opcional para filtrar contenedores del proyecto
NAME_PREFIX = os.getenv("NAME_PREFIX", "sedcm-")
def is_workload_container(name: str) -> bool:
    return name.startswith("sedcm-critico-") or name.startswith("sedcm-svc-")

TOPIC_FMT = "dc/telemetria/zona/{zone}/rack/{rack}/host/{host}/contenedor/{container}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_get(d: Dict[str, Any], path: Tuple[str, ...], default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def parse_labels(container: Dict[str, Any]) -> Tuple[str, str, bool]:
    labels = container.get("spec", {}).get("labels", {}) or {}
    zone = (labels.get("dc.zone") or "").strip()
    rack = (labels.get("dc.rack") or "").strip()
    critical = str(labels.get("dc.critical", "")).lower() in ("true", "1", "yes")
    return zone, rack, critical


def container_name(container: Dict[str, Any]) -> str:
    # alias suele traer "/name"
    aliases = container.get("aliases") or []
    if aliases:
        return str(aliases[0]).lstrip("/")
    # fallback
    return str(container.get("name", "")).split("/")[-1]


def pick_latest_stats(container: Dict[str, Any]) -> Dict[str, Any] | None:
    stats = container.get("stats") or []
    if not stats:
        return None
    return stats[-1]


def cpu_total_ns(stat: Dict[str, Any]) -> int:
    # cAdvisor: cpu.usage.total (nanoseconds)
    v = safe_get(stat, ("cpu", "usage", "total"), 0)
    return int(v or 0)


def mem_usage_bytes(stat: Dict[str, Any]) -> int:
    v = safe_get(stat, ("memory", "usage"), 0)
    return int(v or 0)


def net_rx_bytes(stat: Dict[str, Any]) -> int:
    # si no hay network, regresamos 0
    v = safe_get(stat, ("network", "rx_bytes"), 0)
    return int(v or 0)


def net_tx_bytes(stat: Dict[str, Any]) -> int:
    v = safe_get(stat, ("network", "tx_bytes"), 0)
    return int(v or 0)


def fetch_subcontainers() -> list[dict[str, Any]]:
    url = f"{CADVISOR_URL}/api/v1.3/subcontainers"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    return []


def main() -> None:
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    # state para calcular deltas de CPU
    prev_cpu: dict[str, int] = {}
    prev_ts: dict[str, float] = {}

    host_name = os.getenv("HOSTNAME", "cadvisor")

    while True:
        try:
            containers = fetch_subcontainers()
            t_now = time.time()

            for c in containers:
                name = container_name(c)
                if not name or not is_workload_container(name):
                 continue

                zone, rack, _crit = parse_labels(c)
                if not zone or not rack:
                    # si no trae labels, lo ignoramos (tu inventario se basa en labels)
                    continue

                st = pick_latest_stats(c)
                if not st:
                    continue

                cid = safe_get(c, ("id",), "") or name

                cpu_ns = cpu_total_ns(st)
                mem_b = mem_usage_bytes(st)
                rx_b = net_rx_bytes(st)
                tx_b = net_tx_bytes(st)

                # CPU% por delta
                prev = prev_cpu.get(cid)
                prev_t = prev_ts.get(cid)
                cpu_pct = 0.0
                if prev is not None and prev_t is not None:
                    dt = max(t_now - prev_t, 1e-6)
                    dcpu = max(cpu_ns - prev, 0)
                    # dcpu está en ns; 1 core full = dt * 1e9 ns
                    cpu_pct = (dcpu / (dt * 1e9)) * 100.0

                prev_cpu[cid] = cpu_ns
                prev_ts[cid] = t_now

                payload = {
                    "timestamp": now_iso(),
                    "zone": zone,
                    "rack": rack,
                    "host": host_name,
                    "container_id": cid,
                    "container_name": name,
                    "cpu_pct": round(cpu_pct, 3),
                    "ram_mb": round(mem_b / (1024 * 1024), 3),
                    "net_rx": float(rx_b),
                    "net_tx": float(tx_b),
                    "io_read": 0.0,
                    "io_write": 0.0,
                    # NO enviamos temp/hum/power aquí; eso lo fusiona TelemetryFusion
                }

                topic = TOPIC_FMT.format(
                    zone=zone, rack=rack, host=host_name, container=name
                )

                client.publish(topic, json.dumps(payload), qos=0, retain=False)

        except Exception as e:
            print(f"[cadvisor-bridge] error: {e}", flush=True)

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()