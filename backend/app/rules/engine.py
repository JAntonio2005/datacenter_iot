from __future__ import annotations

import logging

from app.db.inventory import resolve_rack_id
from app.db.models import EstadoRack, TelemetrySample
from app.mqtt.command_publisher import CommandPublisher
from app.rules.state_machine import RackStatus, next_state
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class RulesEngine:
    def __init__(self, command_publisher: CommandPublisher) -> None:
        self.command_publisher = command_publisher

    def evaluate(self, *, db, telemetry: TelemetrySample) -> RackStatus:
        rack_key = f"{telemetry.zone}:{telemetry.rack}"
        rack_id = resolve_rack_id(db, telemetry.zone, telemetry.rack)
        if rack_id is None:
            logger.warning(
                "rules evaluation skipped due to missing rack",
                extra={"event": "rack_state_transition", "flow": "rules", "zone": telemetry.zone, "rack": telemetry.rack},
            )
            return RackStatus.NORMAL

        current = db.get(EstadoRack, rack_key)
        current_state = RackStatus(current.estado) if current else RackStatus.NORMAL
        new_state = next_state(current_state, telemetry.temp_c or 0.0)

        state_changed = new_state != current_state

        if current is None:
            current = EstadoRack(
                clave_rack=rack_key,
                rack_id=rack_id,
                estado=new_state.value,
            )
            db.add(current)
            db.commit()
            state_changed = True
        elif state_changed:
            current.estado = new_state.value
            db.commit()

        audit = AuditService(db)

        # Solo auditar transición si realmente cambió
        if state_changed:
            logger.info(
                "rack state transition",
                extra={
                    "event": "rack_state_transition",
                    "flow": "rules",
                    "zone": telemetry.zone,
                    "rack": telemetry.rack,
                    "rack_id": rack_id,
                },
            )
            audit.record(
                "rack_state_transition",
                rack_id=rack_id,
                zone=telemetry.zone,
                rack=telemetry.rack,
                details={
                    "from": current_state.value,
                    "to": new_state.value,
                    "temp_c": telemetry.temp_c,
                },
            )

        # Solo emitir comando en transición real a Critical
        if new_state == RackStatus.CRITICAL and current_state != RackStatus.CRITICAL:
            command = self.command_publisher.publish_stop_critico(
                zone=telemetry.zone,
                rack=telemetry.rack,
                reason=f"temp_c={telemetry.temp_c} >= 45",
            )
            audit.record(
                "command_emitted",
                rack_id=rack_id,
                zone=telemetry.zone,
                rack=telemetry.rack,
                correlation_id=command["correlation_id"],
                command_id=command["command_id"],
                details=command,
            )

        return new_state