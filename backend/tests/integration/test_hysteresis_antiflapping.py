from __future__ import annotations

from app.rules.state_machine import RackStatus, next_state


def test_hysteresis_avoids_flapping() -> None:
    state = RackStatus.NORMAL

    state = next_state(state, 40.2)
    assert state == RackStatus.WARNING

    state = next_state(state, 39.3)
    assert state == RackStatus.WARNING

    state = next_state(state, 38.8)
    assert state == RackStatus.NORMAL
