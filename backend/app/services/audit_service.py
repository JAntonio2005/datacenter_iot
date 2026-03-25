from __future__ import annotations

import os

from sqlalchemy.orm import Session

from app.db.models import AuditLog, Auditoria


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        event_type: str,
        *,
        rack_id: int | None = None,
        zone: str | None = None,
        rack: str | None = None,
        correlation_id: str | None = None,
        command_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        payload = details or {}
        mode = os.getenv("DB_WRITE_MODE", "dual").lower()

        if mode in {"legacy", "dual"}:
            legacy_row = AuditLog(
                event_type=event_type,
                zone=zone,
                rack=rack,
                correlation_id=correlation_id,
                command_id=command_id,
                details=payload,
            )
            self.db.add(legacy_row)

        if mode in {"normalized", "dual"}:
            normalized_row = Auditoria(
                rack_id=rack_id,
                tipo_evento=event_type,
                id_correlacion=correlation_id,
                id_comando=command_id,
                detalles=payload,
            )
            self.db.add(normalized_row)

        self.db.commit()
