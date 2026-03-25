from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class InventoryZoneResponse(BaseModel):
    zone: str
    nombre: str


class InventoryRackResponse(BaseModel):
    zone: str
    rack: str
    clave_rack: str


class InventoryContainerResponse(BaseModel):
    rack: str
    container_name: str
    host: str | None = None
    rol: str | None = None
    es_critico: bool


class RackSummaryResponse(BaseModel):
    zone: str
    rack: str
    state: str
    updated_at: datetime | None = None
    temp_c: float | None = None
    hum_pct: float | None = None
    power_w: float | None = None
