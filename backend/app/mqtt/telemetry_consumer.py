from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping

from app.core.idempotency import IdempotencyRepository
from app.db.inventory import resolve_container_id, resolve_rack_id
from app.db.models import MuestraTelemetria, TelemetrySample
from app.db.session import SessionLocal
from app.mqtt.schemas import TelemetryPayload
from app.mqtt.telemetry_fusion import TelemetryFusion
from app.rules.engine import RulesEngine
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class TelemetryConsumer:
    def __init__(self, engine: RulesEngine) -> None:
        self.engine = engine
        self.fusion = TelemetryFusion()

    def handle_message(self, topic: str, payload: bytes) -> None:
        if isinstance(payload, Mapping):
            raw_payload = payload
        else:
            try:
                raw_payload = json.loads(payload.decode("utf-8"))
            except Exception as exc:
                logger.warning(
                    "telemetry payload decode failed",
                    extra={"event": "telemetry_rejected", "flow": "ingestion", "topic": topic, "error": str(exc)},
                )
                with SessionLocal() as db:
                    AuditService(db).record(
                        "telemetry_rejected",
                        details={
                            "topic": topic,
                            "reason": f"invalid json: {exc}",
                            "payload_raw": payload.decode("utf-8", errors="replace"),
                        },
                    )
                return

        if not isinstance(raw_payload, Mapping):
            logger.warning(
                "telemetry payload is not an object",
                extra={"event": "telemetry_rejected", "flow": "ingestion", "topic": topic, "payload_type": type(raw_payload).__name__},
            )
            with SessionLocal() as db:
                AuditService(db).record(
                    "telemetry_rejected",
                    details={
                        "topic": topic,
                        "reason": "payload must be a JSON object",
                        "payload": raw_payload,
                    },
                )
            return

        merged = self.fusion.merge(raw_payload)

        try:
            parsed = TelemetryPayload.model_validate(merged)
        except Exception as exc:
            logger.warning(
                "telemetry payload validation failed",
                extra={"event": "telemetry_rejected", "flow": "ingestion", "topic": topic, "error": str(exc)},
            )
            with SessionLocal() as db:
                AuditService(db).record(
                    "telemetry_rejected",
                    zone=merged.get("zone") if isinstance(merged.get("zone"), str) else None,
                    rack=merged.get("rack") if isinstance(merged.get("rack"), str) else None,
                    details={"topic": topic, "reason": str(exc), "payload": merged},
                )
            return

        with SessionLocal() as db:
            message_id = f"{parsed.timestamp.isoformat()}:{parsed.zone}:{parsed.rack}:{parsed.host}:{parsed.container_id}"
            idempotency = IdempotencyRepository(db, source="telemetry")
            if idempotency.has_seen(message_id):
                AuditService(db).record(
                    "telemetry_duplicate",
                    zone=parsed.zone,
                    rack=parsed.rack,
                    details={"topic": topic, "message_id": message_id},
                )
                return

            rack_id = resolve_rack_id(db, parsed.zone, parsed.rack)
            if rack_id is None:
                logger.warning(
                    "telemetry rack not found",
                    extra={"event": "telemetry_rejected", "flow": "ingestion", "zone": parsed.zone, "rack": parsed.rack},
                )
                AuditService(db).record(
                    "telemetry_rejected",
                    zone=parsed.zone,
                    rack=parsed.rack,
                    details={"topic": topic, "reason": "unknown rack"},
                )
                return

            container_ref = resolve_container_id(
                db,
                rack_id=rack_id,
                container_name=parsed.container_name,
                host=parsed.host,
                container_id=parsed.container_id,
            )

            mode = os.getenv("DB_WRITE_MODE", "dual").lower()

            legacy_row: TelemetrySample | None = None
            if mode in {"legacy", "dual"}:
                legacy_row = TelemetrySample(
                    ts=parsed.timestamp,
                    zone=parsed.zone,
                    rack=parsed.rack,
                    host=parsed.host,
                    container_id=parsed.container_id,
                    container_name=parsed.container_name,
                    cpu_pct=parsed.cpu_pct,
                    ram_mb=parsed.ram_mb,
                    temp_c=parsed.temp_c,
                    hum_pct=parsed.hum_pct,
                    payload=merged,
                )
                db.add(legacy_row)

            if mode in {"normalized", "dual"}:
                normalized_row = MuestraTelemetria(
                    rack_id=rack_id,
                    contenedor_id_ref=container_ref,
                    marca_tiempo=parsed.timestamp,
                    host=parsed.host,
                    cpu_pct=parsed.cpu_pct,
                    ram_mb=parsed.ram_mb,
                    temp_c=parsed.temp_c,
                    hum_pct=parsed.hum_pct,
                    power_w=parsed.power_w,
                    net_rx=parsed.net_rx,
                    net_tx=parsed.net_tx,
                    io_read=parsed.io_read,
                    io_write=parsed.io_write,
                    payload=merged,
                )
                db.add(normalized_row)

            db.commit()
            if legacy_row is not None:
                db.refresh(legacy_row)

            idempotency.mark_seen(message_id)

            logger.info(
                "telemetry ingested",
                extra={
                    "event": "telemetry_ingested",
                    "flow": "ingestion",
                    "zone": parsed.zone,
                    "rack": parsed.rack,
                    "rack_id": rack_id,
                    "message_id": message_id,
                },
            )

            AuditService(db).record(
                "telemetry_ingested",
                rack_id=rack_id,
                zone=parsed.zone,
                rack=parsed.rack,
                details={
                    "topic": topic,
                    "container": parsed.container_name,
                    "temp_c": parsed.temp_c,
                    "message_id": message_id,
                },
            )

            if legacy_row is not None:
                self.engine.evaluate(db=db, telemetry=legacy_row)