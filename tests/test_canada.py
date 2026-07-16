from __future__ import annotations

import json
from pathlib import Path

import pytest

from oil_model.canada import population_aligned_employment_rate, real_oil_price_cad
from oil_model.sources.statcan import StatCanAdapter


class FixtureCache:
    def __init__(self, path: Path):
        self.path = path
        self.root = path.parent
        self.refresh = False

    def fetch(self, url: str, name: str | None = None) -> Path:
        return self.path


def test_statcan_vector_preserves_geography_units_and_source_dates(tmp_path: Path) -> None:
    payload = [{"status": "SUCCESS", "object": {"vectorDataPoint": [
        {"refPer": "2025-01-01", "value": 10.0, "releaseTime": "2025-02-07T08:30", "securityLevelCode": 0},
        {"refPer": "2025-02-01", "value": 11.0, "releaseTime": "2025-03-07T08:30", "securityLevelCode": 0},
    ]}}]
    path = tmp_path / "vector.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    series = StatCanAdapter(FixtureCache(path)).fetch_vector(123, label="Ontario test", unit="percent", geography="Ontario", seasonal_adjustment="seasonally adjusted", nominal_real="rate")
    assert series.geography == "Ontario"
    assert series.unit == "percent"
    assert series.observations[-1].date == "2025-02-01"
    assert series.observations[-1].release_date == "2025-03-07"


def test_statcan_schema_change_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "vector.json"
    path.write_text(json.dumps([{"status": "SUCCESS", "object": {"unexpected": []}}]), encoding="utf-8")
    with pytest.raises(ValueError, match="contains no public observations"):
        StatCanAdapter(FixtureCache(path)).fetch_vector(123, label="Test", unit="index", geography="Canada")


def test_cad_conversion_cpi_deflation_and_population_alignment() -> None:
    assert real_oil_price_cad(80.0, 1.35, 150.0) == pytest.approx(72.0)
    assert population_aligned_employment_rate(21_000, 35_000) == pytest.approx(60.0)
    with pytest.raises(ValueError):
        real_oil_price_cad(80.0, 1.35, 0.0)
    with pytest.raises(ValueError):
        population_aligned_employment_rate(100.0, 0.0)


def test_generated_canadian_namespace_is_separate_from_us_classifier() -> None:
    root = Path(__file__).resolve().parents[1] / "website" / "public" / "generated"
    canada = json.loads((root / "canada" / "manifest.json").read_text(encoding="utf-8"))
    us = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert canada["defaultGeography"] == "Canada"
    assert canada["classificationImplemented"] is False
    assert len([item for item in canada["indicators"] if item["core"] and item["geography"] in {"Canada", "Global"}]) == 25
    assert all(not item["file"].startswith("canada/") for item in us["indicators"])
