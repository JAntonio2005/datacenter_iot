from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_zones(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT z.codigo AS zone, z.nombre
                FROM zonas z
                ORDER BY z.codigo
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def list_racks_by_zone(self, zone: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT z.codigo AS zone, r.codigo AS rack, r.clave_rack
                FROM racks r
                JOIN zonas z ON z.id = r.zona_id
                WHERE UPPER(z.codigo) = UPPER(:zone)
                ORDER BY r.codigo
                """
            ),
            {"zone": zone},
        ).mappings().all()
        return [dict(row) for row in rows]

    def list_containers_by_rack(self, rack: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT r.codigo AS rack, c.nombre_contenedor AS container_name, c.host, c.rol, c.es_critico
                FROM contenedores c
                JOIN racks r ON r.id = c.rack_id
                WHERE UPPER(r.codigo) = UPPER(:rack)
                ORDER BY c.nombre_contenedor
                """
            ),
            {"rack": rack},
        ).mappings().all()
        return [dict(row) for row in rows]


def compute_inventory_coverage(
    *,
    expected_pairs: set[tuple[str, str]],
    observed_pairs: Iterable[tuple[str, str, dict[str, Any]]],
) -> dict[str, Any]:
    observed_valid = 0
    required_valid = 0
    required_total = 0

    required_fields = {"zone", "rack", "containers"}

    for zone, rack, payload in observed_pairs:
        if (zone, rack) in expected_pairs:
            observed_valid += 1
        required_total += len(required_fields)
        required_valid += sum(1 for field in required_fields if field in payload)

    cobertura = (observed_valid / len(expected_pairs)) if expected_pairs else 0.0
    fields_rate = (required_valid / required_total) if required_total else 0.0

    return {
        "pares_esperados": len(expected_pairs),
        "pares_observados_validos": observed_valid,
        "cobertura": round(cobertura, 4),
        "required_fields_rate": round(fields_rate, 4),
        "status": "PASS" if cobertura == 1.0 and fields_rate == 1.0 else "FAIL",
    }
