from __future__ import annotations

import logging

from app.db.models import TelemetrySample
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

    def handle_message(self, topic: str, payload: dict) -> None:
        merged = self.fusion.merge(payload)
        try:
            parsed = TelemetryPayload.model_validate(merged)
        except Exception as exc:
            logger.warning("telemetry payload validation failed", extra={"extra": {"topic": topic, "error": str(exc)}})
            with SessionLocal() as db:
                AuditService(db).record(
                    "telemetry_rejected",
                    zone=merged.get("zone") if isinstance(merged.get("zone"), str) else None,
                    rack=merged.get("rack") if isinstance(merged.get("rack"), str) else None,
                    details={"topic": topic, "reason": str(exc), "payload": merged},
                )
            return

        with SessionLocal() as db:
            row = TelemetrySample(
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
            db.add(row)
            db.commit()
            db.refresh(row)

            AuditService(db).record(
                "telemetry_ingested",
                zone=parsed.zone,
                rack=parsed.rack,
                details={"topic": topic, "container": parsed.container_name, "temp_c": parsed.temp_c},
            )

            self.engine.evaluate(db=db, telemetry=row)
