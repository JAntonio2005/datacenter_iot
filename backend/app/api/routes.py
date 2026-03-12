from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@router.get("/racks")
def list_racks() -> list[dict[str, Any]]:
    sql = text("""
        SELECT
            rs.zone,
            rs.rack,
            rs.state,
            rs.updated_at,
            ts.temp_c,
            ts.hum_pct,
            COALESCE(ts.power_w, NULLIF(ts.payload->>'power_w', '')::double precision) AS power_w
        FROM rack_state rs
        LEFT JOIN LATERAL (
            SELECT *
            FROM telemetry_samples t
            WHERE t.zone = rs.zone
              AND t.rack = rs.rack
            ORDER BY t.created_at DESC
            LIMIT 1
        ) ts ON true
        ORDER BY rs.zone, rs.rack
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
            rs.zone,
            rs.rack,
            rs.state,
            rs.updated_at
        FROM rack_state rs
        WHERE rs.zone = :zone AND rs.rack = :rack
        LIMIT 1
    """)

    latest_env_sql = text("""
        SELECT
            t.created_at,
            t.temp_c,
            t.hum_pct,
            COALESCE(t.power_w, NULLIF(t.payload->>'power_w', '')::double precision) AS power_w
        FROM telemetry_samples t
        WHERE t.zone = :zone
          AND t.rack = :rack
        ORDER BY t.created_at DESC
        LIMIT 1
    """)

    containers_sql = text("""
        SELECT DISTINCT ON (t.container_name)
            t.container_name,
            t.host,
            t.cpu_pct,
            t.ram_mb,
            t.temp_c,
            t.hum_pct,
            COALESCE(t.power_w, NULLIF(t.payload->>'power_w', '')::double precision) AS power_w,
            t.created_at
        FROM telemetry_samples t
        WHERE t.zone = :zone
          AND t.rack = :rack
          AND t.container_name <> 'environment-simulator'
        ORDER BY t.container_name, t.created_at DESC
    """)

    events_sql = text("""
        SELECT
            created_at,
            event_type,
            zone,
            rack,
            details
        FROM audit_log
        WHERE zone = :zone
          AND rack = :rack
        ORDER BY created_at DESC
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
            latest_env_sql, {"zone": zone, "rack": rack}
        ).mappings().first()

        containers = db.execute(
            containers_sql, {"zone": zone, "rack": rack}
        ).mappings().all()

        events = db.execute(
            events_sql, {"zone": zone, "rack": rack}
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


@router.get("/audit/recent")
def audit_recent(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    sql = text("""
        SELECT
            created_at,
            event_type,
            zone,
            rack,
            command_id,
            correlation_id,
            details
        FROM audit_log
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    with SessionLocal() as db:
        rows = db.execute(sql, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]