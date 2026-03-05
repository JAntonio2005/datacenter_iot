from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime
from threading import Lock
from typing import Any


class TelemetryFusion:
    def __init__(self) -> None:
        self._ambient_by_rack: dict[tuple[str, str], dict[str, Any]] = defaultdict(dict)
        self._lock = Lock()

    def merge(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        merged = dict(payload)
        zone = str(merged.get("zone", "")).strip()
        rack = str(merged.get("rack", "")).strip()
        if not zone or not rack:
            return merged

        rack_key = (zone, rack)
        with self._lock:
            ambient_payload = self._extract_ambient(merged)
            if ambient_payload:
                self._ambient_by_rack[rack_key].update(ambient_payload)

            last_ambient = self._ambient_by_rack.get(rack_key) or {}
            for key in ("temp_c", "hum_pct", "power_w"):
                if key not in merged and key in last_ambient:
                    merged[key] = last_ambient[key]

        return merged

    @staticmethod
    def _extract_ambient(payload: Mapping[str, Any]) -> dict[str, Any]:
        ambient: dict[str, Any] = {}
        for key in ("temp_c", "hum_pct", "power_w"):
            if key in payload:
                ambient[key] = payload[key]

        nested = payload.get("ambient")
        if isinstance(nested, Mapping):
            for key in ("temp_c", "hum_pct", "power_w"):
                if key in nested:
                    ambient[key] = nested[key]

        timestamp = payload.get("timestamp")
        if timestamp is not None:
            ambient["timestamp"] = TelemetryFusion._normalize_ts(timestamp)
        return ambient

    @staticmethod
    def _normalize_ts(value: Any) -> str | None:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return None
