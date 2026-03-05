from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ProcessedMessage


class IdempotencyRepository:
    def __init__(self, db: Session, source: str) -> None:
        self.db = db
        self.source = source

    def has_seen(self, message_id: str) -> bool:
        stmt = select(ProcessedMessage).where(ProcessedMessage.message_id == message_id)
        return self.db.scalar(stmt) is not None

    def mark_seen(self, message_id: str) -> None:
        if self.has_seen(message_id):
            return
        self.db.add(ProcessedMessage(message_id=message_id, source=self.source))
        self.db.commit()
