from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    RackAmbientResponse,
    RackContainerResponse,
    RackDetailResponse,
    RackSummaryResponse,
)
from app.db.models import RackState, TelemetrySample
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@router.get("/racks", response_model=list[RackSummaryResponse])
def get_racks(db: Session = Depends(get_db)) -> list[RackSummaryResponse]:
    racks = db.execute(
        select(RackState).order_by(RackState.zone, RackState.rack)
    ).scalars().all()

    result: list[RackSummaryResponse] = []

    for rack in racks:
        latest_any = db.execute(
            select(TelemetrySample)
            .where(
                TelemetrySample.zone == rack.zone,
                TelemetrySample.rack == rack.rack,
            )
            .order_by(TelemetrySample.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        latest_temp = db.execute(
            select(TelemetrySample)
            .where(
                TelemetrySample.zone == rack.zone,
                TelemetrySample.rack == rack.rack,
                TelemetrySample.temp_c.is_not(None),
            )
            .order_by(TelemetrySample.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        latest_hum = db.execute(
            select(TelemetrySample)
            .where(
                TelemetrySample.zone == rack.zone,
                TelemetrySample.rack == rack.rack,
                TelemetrySample.hum_pct.is_not(None),
            )
            .order_by(TelemetrySample.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        latest_power = db.execute(
            select(TelemetrySample)
            .where(
                TelemetrySample.zone == rack.zone,
                TelemetrySample.rack == rack.rack,
            )
            .order_by(TelemetrySample.created_at.desc())
        ).scalars().all()

        power_w = None
        for sample in latest_power:
            if sample.payload and isinstance(sample.payload, dict):
                raw_power = sample.payload.get("power_w")
                if raw_power is not None:
                    try:
                        power_w = float(raw_power)
                        break
                    except (TypeError, ValueError):
                        pass

        result.append(
            RackSummaryResponse(
                zone=rack.zone,
                rack=rack.rack,
                state=rack.state,
                updated_at=latest_any.created_at if latest_any else rack.updated_at,
                temp_c=latest_temp.temp_c if latest_temp else None,
                hum_pct=latest_hum.hum_pct if latest_hum else None,
                power_w=power_w,
            )
        )

    return result


@router.get("/racks/{zone}/{rack}", response_model=RackDetailResponse)
def get_rack_detail(zone: str, rack: str, db: Session = Depends(get_db)) -> RackDetailResponse:
    rack_row = db.execute(
        select(RackState).where(
            RackState.zone == zone,
            RackState.rack == rack,
        )
    ).scalar_one_or_none()

    if rack_row is None:
        raise HTTPException(status_code=404, detail="Rack not found")

    samples = db.execute(
        select(TelemetrySample)
        .where(
            TelemetrySample.zone == zone,
            TelemetrySample.rack == rack,
        )
        .order_by(TelemetrySample.created_at.desc())
    ).scalars().all()

    if not samples:
        return RackDetailResponse(
            zone=zone,
            rack=rack,
            state=rack_row.state,
            updated_at=rack_row.updated_at,
            ambient=RackAmbientResponse(
                temp_c=None,
                hum_pct=None,
                power_w=None,
            ),
            containers=[],
        )

    latest_temp = next((s for s in samples if s.temp_c is not None), None)
    latest_hum = next((s for s in samples if s.hum_pct is not None), None)

    power_w = None
    for s in samples:
        payload = s.payload if isinstance(s.payload, dict) else {}
        raw_power = payload.get("power_w")
        if raw_power is not None:
            try:
                power_w = float(raw_power)
                break
            except (TypeError, ValueError):
                continue

    latest_by_container: dict[str, TelemetrySample] = {}
    for sample in samples:
        cname = sample.container_name or "unknown"
        if cname not in latest_by_container:
            latest_by_container[cname] = sample

    def safe_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    rack_lower = rack.lower()
    allowed_names = {
        f"sedcm-critico-{rack_lower}",
        f"sedcm-svc-{rack_lower}-a",
        f"sedcm-svc-{rack_lower}-b",
    }

    containers: list[RackContainerResponse] = []

    for cname, sample in latest_by_container.items():
        if cname not in allowed_names:
            continue

        payload = sample.payload if isinstance(sample.payload, dict) else {}

        containers.append(
            RackContainerResponse(
                container_name=cname,
                host=sample.host,
                cpu_pct=sample.cpu_pct,
                ram_mb=sample.ram_mb,
                net_rx=safe_float(payload.get("net_rx")),
                net_tx=safe_float(payload.get("net_tx")),
                io_read=safe_float(payload.get("io_read")),
                io_write=safe_float(payload.get("io_write")),
                temp_c=sample.temp_c,
                hum_pct=sample.hum_pct,
                power_w=safe_float(payload.get("power_w")),
                ts=sample.ts,
            )
        )

    containers = sorted(containers, key=lambda c: c.container_name)

    return RackDetailResponse(
        zone=zone,
        rack=rack,
        state=rack_row.state,
        updated_at=rack_row.updated_at,
        ambient=RackAmbientResponse(
            temp_c=latest_temp.temp_c if latest_temp else None,
            hum_pct=latest_hum.hum_pct if latest_hum else None,
            power_w=power_w,
        ),
        containers=containers,
    )