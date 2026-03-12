from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TelemetryPayload(BaseModel):
    timestamp: datetime
    zone: str
    rack: str
    host: str
    container_id: str
    container_name: str

    cpu_pct: float = Field(ge=0)
    ram_mb: float = Field(ge=0)
    net_rx: float = Field(ge=0)
    net_tx: float = Field(ge=0)
    io_read: float = Field(ge=0)
    io_write: float = Field(ge=0)

    # Ambientales opcionales (cAdvisor real no los trae)
    temp_c: float | None = None
    hum_pct: float | None = None
    power_w: float | None = None


class CommandPayload(BaseModel):
    command_id: str
    timestamp: datetime
    zone: str
    rack: str
    action: Literal["stop_critico"]
    reason: str
    correlation_id: str


class AckPayload(BaseModel):
    command_id: str
    timestamp: datetime
    status: Literal["ok", "fail"]
    details: str