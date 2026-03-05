from __future__ import annotations

import docker
from docker.errors import DockerException


class DockerAdapter:
    def __init__(self) -> None:
        self._client = docker.from_env()

    def stop_critical_container(self, *, zone: str, rack: str) -> tuple[bool, str]:
        filters = {
            "label": [
                f"dc.zone={zone}",
                f"dc.rack={rack}",
                "dc.critical=true",
            ]
        }
        try:
            containers = self._client.containers.list(all=True, filters=filters)
            if not containers:
                return False, "no critical container found"
            target = containers[0]
            target.stop(timeout=10)
            return True, f"stopped container {target.name}"
        except DockerException as exc:
            return False, f"docker error: {exc}"
