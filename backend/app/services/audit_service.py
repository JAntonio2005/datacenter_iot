from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import AuditLog


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        event_type: str,
        *,
        zone: str | None = None,
        rack: str | None = None,
        correlation_id: str | None = None,
        command_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        row = AuditLog(
            event_type=event_type,
            zone=zone,
            rack=rack,
            correlation_id=correlation_id,
            command_id=command_id,
            details=details or {},
        )
        self.db.add(row)
        self.db.commit()
