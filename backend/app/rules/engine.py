from __future__ import annotations

from app.db.models import RackState, TelemetrySample
from app.mqtt.command_publisher import CommandPublisher
from app.rules.state_machine import RackStatus, next_state
from app.services.audit_service import AuditService


class RulesEngine:
    def __init__(self, command_publisher: CommandPublisher) -> None:
        self.command_publisher = command_publisher

    def evaluate(self, *, db, telemetry: TelemetrySample) -> RackStatus:
        rack_key = f"{telemetry.zone}:{telemetry.rack}"
        current = db.get(RackState, rack_key)
        current_state = RackStatus(current.state) if current else RackStatus.NORMAL
        new_state = next_state(current_state, telemetry.temp_c or 0.0)

        if current is None:
            current = RackState(rack_key=rack_key, zone=telemetry.zone, rack=telemetry.rack, state=new_state.value)
            db.add(current)
        else:
            current.state = new_state.value
        db.commit()

        audit = AuditService(db)
        audit.record(
            "rack_state_transition",
            zone=telemetry.zone,
            rack=telemetry.rack,
            details={"from": current_state.value, "to": new_state.value, "temp_c": telemetry.temp_c},
        )

        if new_state == RackStatus.CRITICAL and current_state != RackStatus.CRITICAL:
            command = self.command_publisher.publish_stop_critico(
                zone=telemetry.zone,
                rack=telemetry.rack,
                reason=f"temp_c={telemetry.temp_c} >= 45",
            )
            audit.record(
                "command_emitted",
                zone=telemetry.zone,
                rack=telemetry.rack,
                correlation_id=command["correlation_id"],
                command_id=command["command_id"],
                details=command,
            )

        return new_state
