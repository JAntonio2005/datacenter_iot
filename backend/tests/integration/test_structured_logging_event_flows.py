from __future__ import annotations

import json
import logging

from app.core.logging import JsonFormatter


FLOW_EVENTS = [
    ("ingestion", "telemetry_ingested"),
    ("rules", "rack_state_transition"),
    ("command", "command_emitted"),
    ("ack", "edge_ack"),
]


def test_structured_logging_per_flow() -> None:
    formatter = JsonFormatter()

    for flow, event in FLOW_EVENTS:
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="event",
            args=(),
            exc_info=None,
        )
        record.flow = flow
        record.event = event
        record.zone = "A"
        record.rack = "A1"

        payload = json.loads(formatter.format(record))
        assert payload["flow"] == flow
        assert payload["event"] == event
        assert payload["zone"] == "A"
        assert payload["rack"] == "A1"
