from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BACKFILL = ROOT / "backend" / "app" / "db" / "migrations" / "0003_backfill_normalizacion.sql"


def test_backfill_contains_edge_case_rules() -> None:
    sql = BACKFILL.read_text(encoding="utf-8")

    assert "duplicate_container_name" in sql
    assert "missing_zone_or_rack" in sql
