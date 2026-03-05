from __future__ import annotations


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def has_seen(self, message_id: str) -> bool:
        return message_id in self._seen

    def mark_seen(self, message_id: str) -> None:
        self._seen.add(message_id)
