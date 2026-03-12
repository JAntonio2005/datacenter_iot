from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RackSummaryResponse(BaseModel):
    zone: str
    rack: str
    state: str
    updated_at: datetime | None = None
    temp_c: float | None = None
    hum_pct: float | None = None
    power_w: float | None = None


class RackAmbientResponse(BaseModel):
    temp_c: float | None = None
    hum_pct: float | None = None
    power_w: float | None = None


class RackContainerResponse(BaseModel):
    container_name: str
    host: str | None = None
    cpu_pct: float | None = None
    ram_mb: float | None = None
    net_rx: float | None = None
    net_tx: float | None = None
    io_read: float | None = None
    io_write: float | None = None
    temp_c: float | None = None
    hum_pct: float | None = None
    power_w: float | None = None
    ts: datetime | None = None


class RackDetailResponse(BaseModel):
    zone: str
    rack: str
    state: str
    updated_at: datetime | None = None
    ambient: RackAmbientResponse
    containers: list[RackContainerResponse]