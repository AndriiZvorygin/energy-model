from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from oil_model.affordability import (
    STATCAN_CPI_SPECS,
    _ratio,
    _transmission_row,
)
from oil_model.sources import SourceObservation, SourceSeries


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "website" / "public" / "generated"


def series(name: str, values: list[float], *, start_year: int = 2000, geography: str = "Canada", frequency: str = "monthly") -> SourceSeries:
    rows = []
    for index, value in enumerate(values):
        year = start_year + index // 12
        month = index % 12 + 1
        rows.append(SourceObservation(f"{year:04d}-{month:02d}-01", value, None))
    return SourceSeries(name, name, "index", geography, frequency, "not seasonally adjusted", "nominal", "test", "https://example.test", "2026-01-01", "test revision note", rows)


def test_statcan_food_category_mapping_is_native_and_unique() -> None:
    ids = [row[0] for row in STATCAN_CPI_SPECS]
    names = [row[4] for row in STATCAN_CPI_SPECS]
    assert len(ids) == len(set(ids))
    assert {"Food purchased from stores", "Food purchased from restaurants", "Dairy products and eggs", "Bakery and cereal products (excluding baby food)"} <= set(names)
    assert all("Owen Sound" not in row[3] for row in STATCAN_CPI_SPECS)


def test_fao_real_and_nominal_are_distinct_and_self_describing() -> None:
    nominal = json.loads((GENERATED / "global/indicators/fao-food-price-index.json").read_text())
    real = json.loads((GENERATED / "global/indicators/fao-food-price-index-real.json").read_text())
    assert nominal["nominalOrReal"] == "nominal"
    assert real["nominalOrReal"] == "real"
    assert nominal["unit"] == "index, 2014-2016=100"
    assert nominal["observations"][-1]["value"] != real["observations"][-1]["value"]
    assert "projected and observed" in nominal["revisionStatus"]


def test_lag_alignment_recovers_predictor_lead_without_future_data() -> None:
    rng = np.random.default_rng(42)
    predictor_values = rng.normal(size=84).tolist()
    target_values = [0.0, 0.0, *predictor_values[:-2]]
    result = _transmission_row("synthetic", series("predictor", predictor_values), series("target", target_values))
    assert result["peak_lag_months"] == 2
    assert result["peak_lag_correlation"] == pytest.approx(1.0)


def test_cpi_deflation_and_price_to_income_rebasing() -> None:
    prices = series("prices", [100, 120, 150])
    cpi = series("cpi", [100, 110, 125])
    real = _ratio(prices, cpi, "real", "real house price")
    assert [row.value for row in real.observations] == pytest.approx([100, 109.090909, 120])
    income = series("income", [50, 55, 75])
    ratio = _ratio(prices, income, "ratio", "price income", rebase=True)
    assert ratio.observations[0].value == pytest.approx(100)
    assert ratio.observations[-1].value == pytest.approx(100)


def test_house_prices_and_shelter_costs_remain_separate() -> None:
    house = json.loads((GENERATED / "canada/indicators/new-housing-price-index.json").read_text())
    shelter = json.loads((GENERATED / "canada/indicators/shelter-cpi.json").read_text())
    rent = json.loads((GENERATED / "canada/indicators/rent-cpi.json").read_text())
    assert house["sourceIdentifier"] != shelter["sourceIdentifier"] != rent["sourceIdentifier"]
    assert "property purchase price" in house["nominalOrReal"]
    assert shelter["nominalOrReal"] == "consumer price index"


def test_country_histories_and_percentiles_are_separate() -> None:
    canada = json.loads((GENERATED / "canada/indicators/grocery-cpi.json").read_text())
    us = json.loads((GENERATED / "us/indicators/us-food-at-home-cpi.json").read_text())
    assert canada["geography"] == "Canada"
    assert us["geography"] == "United States"
    assert canada["sourceIdentifier"] != us["sourceIdentifier"]
    assert canada["latest"]["historicalPercentile"] != us["latest"]["historicalPercentile"]


def test_canadian_income_ratios_use_published_components() -> None:
    ratio = json.loads((GENERATED / "canada/indicators/nhpi-to-income.json").read_text())
    assert ratio["components"] == ["new-housing-price-index", "household-disposable-income-per-person"]
    assert ratio["frequency"] == "quarterly"
    findings = (ROOT / "analysis/food_housing_affordability_findings.md").read_text()
    assert "food-" in findings
    assert "Quarterly income comparisons" in findings


def test_frequency_and_international_comparison_metadata() -> None:
    bis = json.loads((GENERATED / "global/indicators/bis-real-house-prices.json").read_text())
    nhpi = json.loads((GENERATED / "canada/indicators/new-housing-price-index.json").read_text())
    assert bis["frequency"] == "quarterly"
    assert nhpi["frequency"] == "monthly"
    assert bis["directlyComparableAcrossCountries"] is True
    assert "not every dwelling" in bis["definition"]


def test_generated_affordability_schema_and_classifier_separation() -> None:
    required = {"geography", "source", "definition", "unit", "frequency", "seasonalAdjustment", "nominalOrReal", "sourceDate", "retrievalDate", "revisionStatus", "observations", "latest", "transformations", "futureClassifierMetadata"}
    for path in [
        GENERATED / "global/indicators/fao-food-price-index.json",
        GENERATED / "canada/indicators/food-cpi.json",
        GENERATED / "us/indicators/us-fhfa-house-price-index.json",
    ]:
        payload = json.loads(path.read_text())
        assert not required - payload.keys()
        assert payload["futureClassifierMetadata"]["status"] == "metadata_only_not_scored"
    for path in [GENERATED / "current-classification.json", GENERATED / "canada/current-classification.json"]:
        text = path.read_text()
        assert "food_affordability_pressure" not in text
        assert "house_price_to_income" not in text
