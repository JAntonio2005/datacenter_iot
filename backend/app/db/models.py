from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# Legacy tables (coexistence mode)
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


# Normalized tables
class Zona(Base):
    __tablename__ = "zonas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(16), unique=True)
    nombre: Mapped[str] = mapped_column(String(128))


class Rack(Base):
    __tablename__ = "racks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    zona_id: Mapped[int] = mapped_column(ForeignKey("zonas.id", ondelete="RESTRICT"))
    codigo: Mapped[str] = mapped_column(String(16))
    nombre: Mapped[str] = mapped_column(String(128))
    clave_rack: Mapped[str] = mapped_column(String(64), unique=True)


class Contenedor(Base):
    __tablename__ = "contenedores"
    __table_args__ = (UniqueConstraint("rack_id", "nombre_contenedor", name="uq_contenedor_nombre_por_rack"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rack_id: Mapped[int] = mapped_column(ForeignKey("racks.id", ondelete="CASCADE"))
    contenedor_id: Mapped[str | None] = mapped_column(String(128))
    nombre_contenedor: Mapped[str] = mapped_column(String(128))
    host: Mapped[str | None] = mapped_column(String(128))
    rol: Mapped[str | None] = mapped_column(String(32))
    es_critico: Mapped[bool] = mapped_column(default=False)
    estado: Mapped[str | None] = mapped_column(String(32))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EstadoRack(Base):
    __tablename__ = "estado_rack"

    clave_rack: Mapped[str] = mapped_column(String(64), primary_key=True)
    rack_id: Mapped[int] = mapped_column(ForeignKey("racks.id", ondelete="CASCADE"), unique=True)
    estado: Mapped[str] = mapped_column(String(32))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MuestraTelemetria(Base):
    __tablename__ = "muestras_telemetria"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rack_id: Mapped[int] = mapped_column(ForeignKey("racks.id", ondelete="RESTRICT"))
    contenedor_id_ref: Mapped[int | None] = mapped_column(ForeignKey("contenedores.id", ondelete="SET NULL"))
    marca_tiempo: Mapped[datetime]
    host: Mapped[str | None] = mapped_column(String(128))
    cpu_pct: Mapped[float | None] = mapped_column(Float)
    ram_mb: Mapped[float | None] = mapped_column(Float)
    temp_c: Mapped[float | None] = mapped_column(Float)
    hum_pct: Mapped[float | None] = mapped_column(Float)
    power_w: Mapped[float | None] = mapped_column(Float)
    net_rx: Mapped[float | None] = mapped_column(Float)
    net_tx: Mapped[float | None] = mapped_column(Float)
    io_read: Mapped[float | None] = mapped_column(Float)
    io_write: Mapped[float | None] = mapped_column(Float)
    payload: Mapped[dict | None] = mapped_column(JSON)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rack_id: Mapped[int | None] = mapped_column(ForeignKey("racks.id", ondelete="SET NULL"))
    tipo_evento: Mapped[str] = mapped_column(String(64))
    id_correlacion: Mapped[str | None] = mapped_column(String(128))
    id_comando: Mapped[str | None] = mapped_column(String(128))
    detalles: Mapped[dict | None] = mapped_column(JSON)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MensajeProcesado(Base):
    __tablename__ = "mensaje_procesado"

    id_mensaje: Mapped[str] = mapped_column(String(128), primary_key=True)
    fuente: Mapped[str] = mapped_column(String(64))
    visto_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
