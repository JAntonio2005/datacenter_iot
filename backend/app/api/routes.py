from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@router.get("/racks")
def list_racks() -> list[dict[str, Any]]:
    sql = text("""
        SELECT
            z.codigo AS zone,
            r.codigo AS rack,
            er.estado AS state,
            er.actualizado_en AS updated_at,
            mt.temp_c,
            mt.hum_pct,
            mt.power_w
        FROM estado_rack er
        JOIN racks r ON r.id = er.rack_id
        JOIN zonas z ON z.id = r.zona_id
        LEFT JOIN LATERAL (
            SELECT *
            FROM muestras_telemetria m
            WHERE m.rack_id = r.id
            ORDER BY m.creado_en DESC
            LIMIT 1
        ) mt ON true
        ORDER BY z.codigo, r.codigo
    """)

    with SessionLocal() as db:
        rows = db.execute(sql).mappings().all()
        return [dict(row) for row in rows]


@router.get("/racks/{zone}/{rack}")
def rack_detail(zone: str, rack: str) -> dict[str, Any]:
    zone = zone.upper()
    rack = rack.upper()

    rack_sql = text("""
        SELECT
            z.codigo AS zone,
            r.codigo AS rack,
            r.id AS rack_id,
            er.estado AS state,
            er.actualizado_en AS updated_at
        FROM racks r
        JOIN zonas z ON z.id = r.zona_id
        LEFT JOIN estado_rack er ON er.rack_id = r.id
        WHERE z.codigo = :zone AND r.codigo = :rack
        LIMIT 1
    """)

    latest_env_sql = text("""
        SELECT
            t.creado_en AS created_at,
            t.temp_c,
            t.hum_pct,
            t.power_w
        FROM muestras_telemetria t
        WHERE t.rack_id = :rack_id
        ORDER BY t.creado_en DESC
        LIMIT 1
    """)

    containers_sql = text("""
        SELECT
            c.nombre_contenedor AS container_name,
            c.host,
            c.rol,
            c.es_critico,
            c.estado,
            c.creado_en
        FROM contenedores c
        WHERE c.rack_id = :rack_id
        ORDER BY c.nombre_contenedor
    """)

    events_sql = text("""
        SELECT
            creado_en AS created_at,
            tipo_evento AS event_type,
            detalles AS details
        FROM auditoria
        WHERE rack_id = :rack_id
        ORDER BY creado_en DESC
        LIMIT 20
    """)

    with SessionLocal() as db:
        rack_row = db.execute(rack_sql, {"zone": zone, "rack": rack}).mappings().first()
        if rack_row is None:
            return {
                "zone": zone,
                "rack": rack,
                "state": "Unknown",
                "updated_at": None,
                "latest_metrics": None,
                "containers": [],
                "events": [],
            }

        latest_metrics = db.execute(
            latest_env_sql, {"rack_id": rack_row["rack_id"]}
        ).mappings().first()

        containers = db.execute(
            containers_sql, {"rack_id": rack_row["rack_id"]}
        ).mappings().all()

        events = db.execute(
            events_sql, {"rack_id": rack_row["rack_id"]}
        ).mappings().all()

        return {
            "zone": rack_row["zone"],
            "rack": rack_row["rack"],
            "state": rack_row["state"],
            "updated_at": rack_row["updated_at"],
            "latest_metrics": dict(latest_metrics) if latest_metrics else None,
            "containers": [dict(row) for row in containers],
            "events": [dict(row) for row in events],
        }


@router.get("/inventory/zones")
def inventory_zones() -> list[dict[str, Any]]:
    with SessionLocal() as db:
        return InventoryService(db).list_zones()


@router.get("/inventory/zones/{zone}/racks")
def inventory_racks(zone: str) -> list[dict[str, Any]]:
    with SessionLocal() as db:
        return InventoryService(db).list_racks_by_zone(zone)


@router.get("/inventory/racks/{rack}/containers")
def inventory_containers(rack: str) -> list[dict[str, Any]]:
    with SessionLocal() as db:
        return InventoryService(db).list_containers_by_rack(rack)


@router.get("/audit/recent")
def audit_recent(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    sql = text("""
        SELECT
            a.creado_en AS created_at,
            a.tipo_evento AS event_type,
            z.codigo AS zone,
            r.codigo AS rack,
            a.id_comando AS command_id,
            a.id_correlacion AS correlation_id,
            a.detalles AS details
        FROM auditoria a
        LEFT JOIN racks r ON r.id = a.rack_id
        LEFT JOIN zonas z ON z.id = r.zona_id
        ORDER BY a.creado_en DESC
        LIMIT :limit
    """)

    with SessionLocal() as db:
        rows = db.execute(sql, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]