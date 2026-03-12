from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime
from threading import Lock
from typing import Any


class TelemetryFusion:
    def __init__(self) -> None:
        # cache por rack (zone,rack) -> {"temp_c":..,"hum_pct":..,"power_w":..}
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
            # 1) Extraer SOLO ambiente válido (sin None)
            ambient_payload = self._extract_ambient(merged)

            # 2) Actualizar cache solo con métricas ambientales (sin timestamp)
            if ambient_payload:
                self._ambient_by_rack[rack_key].update(ambient_payload)

            last_ambient = self._ambient_by_rack.get(rack_key) or {}

            # 3) Rellenar si falta o viene None
            for key in ("temp_c", "hum_pct", "power_w"):
                if (key not in merged or merged.get(key) is None) and key in last_ambient:
                    merged[key] = last_ambient[key]

        return merged

    @staticmethod
    def _extract_ambient(payload: Mapping[str, Any]) -> dict[str, Any]:
        """
        Devuelve un dict SOLO con temp_c/hum_pct/power_w cuando existan y NO sean None.
        Soporta formato plano y anidado en payload["ambient"].
        """
        ambient: dict[str, Any] = {}

        # plano
        for key in ("temp_c", "hum_pct", "power_w"):
            if key in payload and payload[key] is not None:
                ambient[key] = payload[key]

        # anidado
        nested = payload.get("ambient")
        if isinstance(nested, Mapping):
            for key in ("temp_c", "hum_pct", "power_w"):
                if key in nested and nested[key] is not None:
                    ambient[key] = nested[key]

        return ambient

    @staticmethod
    def _normalize_ts(value: Any) -> str | None:
        # Lo dejo por compatibilidad si lo usas en otro lado
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return None