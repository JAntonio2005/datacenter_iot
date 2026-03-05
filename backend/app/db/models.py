from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime]
    zone: Mapped[str] = mapped_column(String(16))
    rack: Mapped[str] = mapped_column(String(16))
    host: Mapped[str | None] = mapped_column(String(64))
    container_id: Mapped[str | None] = mapped_column(String(128))
    container_name: Mapped[str | None] = mapped_column(String(128))
    cpu_pct: Mapped[float | None] = mapped_column(Float)
    ram_mb: Mapped[float | None] = mapped_column(Float)
    temp_c: Mapped[float | None] = mapped_column(Float)
    hum_pct: Mapped[float | None] = mapped_column(Float)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RackState(Base):
    __tablename__ = "rack_state"

    rack_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone: Mapped[str] = mapped_column(String(16))
    rack: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(32))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64))
    correlation_id: Mapped[str | None] = mapped_column(String(128))
    command_id: Mapped[str | None] = mapped_column(String(128))
    zone: Mapped[str | None] = mapped_column(String(16))
    rack: Mapped[str | None] = mapped_column(String(16))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedMessage(Base):
    __tablename__ = "processed_message"

    message_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source: Mapped[str] = mapped_column(String(64))
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
