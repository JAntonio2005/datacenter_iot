from __future__ import annotations

import json
import logging

from app.core.logging import JsonFormatter


def test_structured_logging_required_fields() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="event",
        args=(),
        exc_info=None,
    )
    record.event = "telemetry_ingested"
    record.flow = "ingestion"
    record.zone = "A"
    record.rack = "A1"
    record.message_id = "m-1"
    record.command_id = "c-1"
    record.correlation_id = "corr-1"

    payload = json.loads(formatter.format(record))

    assert payload["event"] == "telemetry_ingested"
    assert payload["flow"] == "ingestion"
    assert payload["zone"] == "A"
    assert payload["rack"] == "A1"
    assert payload["message_id"] == "m-1"
    assert payload["command_id"] == "c-1"
    assert payload["correlation_id"] == "corr-1"
