from __future__ import annotations

from app.services.inventory_service import compute_inventory_coverage


def test_inventory_sc004_coverage_formula() -> None:
    expected = {("A", "A1"), ("A", "A2")}
    observed = [
        ("A", "A1", {"zone": "A", "rack": "A1", "containers": []}),
        ("A", "A2", {"zone": "A", "rack": "A2", "containers": ["svc"]}),
    ]

    report = compute_inventory_coverage(expected_pairs=expected, observed_pairs=observed)

    assert report["cobertura"] == 1.0
    assert report["required_fields_rate"] == 1.0
    assert report["status"] == "PASS"
