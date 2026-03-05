from __future__ import annotations

from enum import Enum


class RackStatus(str, Enum):
    NORMAL = "Normal"
    WARNING = "Warning"
    CRITICAL = "Critical"
    RECOVERY = "Recovery"


class Thresholds:
    T1 = 40.0
    T2 = 45.0
    TRESET = 42.0
    MARGIN_HIST = 1.0


def next_state(current: RackStatus, temp_c: float) -> RackStatus:
    if temp_c >= Thresholds.T2:
        return RackStatus.CRITICAL

    if current == RackStatus.CRITICAL:
        if temp_c <= Thresholds.TRESET:
            return RackStatus.RECOVERY
        return RackStatus.CRITICAL

    if current == RackStatus.WARNING and temp_c >= (Thresholds.T1 - Thresholds.MARGIN_HIST):
        return RackStatus.WARNING

    if temp_c >= Thresholds.T1:
        return RackStatus.WARNING

    if current == RackStatus.RECOVERY and temp_c < (Thresholds.T1 - Thresholds.MARGIN_HIST):
        return RackStatus.NORMAL

    return RackStatus.NORMAL
