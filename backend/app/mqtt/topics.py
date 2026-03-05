from __future__ import annotations

from dataclasses import dataclass

TELEMETRY_TOPIC_PATTERN = "dc/telemetria/zona/{zone}/rack/{rack}/host/{host}/contenedor/{container}"
COMMAND_TOPIC_PATTERN = "dc/comandos/zona/{zone}/rack/{rack}"
EVENTS_TOPIC_PATTERN = "dc/eventos/zona/{zone}/rack/{rack}"


@dataclass(frozen=True)
class RackTarget:
    zone: str
    rack: str


def telemetry_topic(zone: str, rack: str, host: str, container: str) -> str:
    return TELEMETRY_TOPIC_PATTERN.format(zone=zone, rack=rack, host=host, container=container)


def command_topic(zone: str, rack: str) -> str:
    return COMMAND_TOPIC_PATTERN.format(zone=zone, rack=rack)


def events_topic(zone: str, rack: str) -> str:
    return EVENTS_TOPIC_PATTERN.format(zone=zone, rack=rack)


def parse_rack_from_topic(topic: str) -> RackTarget | None:
    parts = topic.split("/")
    if len(parts) < 6:
        return None
    if parts[0] != "dc" or parts[1] not in {"comandos", "eventos", "telemetria"}:
        return None
    try:
        zone_index = parts.index("zona")
        rack_index = parts.index("rack")
        return RackTarget(zone=parts[zone_index + 1], rack=parts[rack_index + 1])
    except (ValueError, IndexError):
        return None
