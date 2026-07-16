from __future__ import annotations

import json
from pathlib import Path

import pytest

from oil_model.affordability import (
    STATCAN_PROPERTY_AUDIT_SPECS,
    STATCAN_PURCHASING_POWER_SPECS,
    _deflate,
    _per_person,
    _quarterly_average,
    _ratio,
)
from oil_model.sources import SourceObservation, SourceSeries


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "website" / "public" / "generated"


def source(values: list[tuple[str, float]], *, frequency: str = "monthly", unit: str = "index") -> SourceSeries:
    return SourceSeries(
        "test", "Test series", unit, "Canada", frequency, "source-defined", "nominal",
        "Statistics Canada", "https://www.statcan.gc.ca", "2026-07-16", "Latest-vintage test series.",
        [SourceObservation(date, value, date) for date, value in values],
    )


def indicator(indicator_id: str) -> dict:
    return json.loads((GENERATED / "canada" / "indicators" / f"{indicator_id}.json").read_text())


def test_verified_statcan_source_mapping() -> None:
    mapping = {row[1]: (row[0], row[-1]) for row in STATCAN_PURCHASING_POWER_SPECS}
    assert mapping["household-disposable-income"] == (62305981, "36-10-0112-01")
    assert mapping["household-saving-rate"] == (62305984, "36-10-0112-01")
    assert mapping["canada-population-quarterly"] == (1, "17-10-0009-01")
    assert mapping["average-hourly-wages"] == (2132579, "14-10-0063-01")
    assert mapping["ontario-average-hourly-wages"] == (2153099, "14-10-0063-01")
    assert any(row[5] == "18-10-0169-01" and "inactive" in row[6] for row in STATCAN_PROPERTY_AUDIT_SPECS)


def test_annualized_income_per_person_is_not_divided_by_four() -> None:
    income = source([("2025-01-01", 1_600_000)], frequency="quarterly", unit="millions CAD at annual rates")
    population = source([("2025-01-01", 40_000_000)], frequency="quarterly", unit="persons")
    result = _per_person(income, population, "per-person", "Per person")
    assert result.observations[0].value == pytest.approx(40_000)
    assert "not divided by four" in result.revision_notes


def test_population_alignment_uses_only_matching_quarters() -> None:
    income = source([("2025-01-01", 1), ("2025-04-01", 2)], frequency="quarterly")
    population = source([("2025-01-01", 10)], frequency="quarterly")
    result = _per_person(income, population, "per-person", "Per person")
    assert [row.date for row in result.observations] == ["2025-01-01"]


def test_quarterly_average_requires_all_three_months() -> None:
    monthly = source([("2025-01-01", 100), ("2025-02-01", 110), ("2025-03-01", 120), ("2025-04-01", 130)])
    quarterly = _quarterly_average(monthly, "quarterly", "Quarterly")
    assert [(row.date, row.value) for row in quarterly.observations] == [("2025-01-01", 110)]


def test_cpi_deflation_and_missing_observations() -> None:
    nominal = source([("2025-01-01", 40_000), ("2025-04-01", 42_000)], frequency="quarterly")
    cpi = source([("2025-01-01", 125)], frequency="quarterly")
    real = _deflate(nominal, cpi, "real", "Real", "real CAD")
    assert [(row.date, row.value) for row in real.observations] == [("2025-01-01", 32_000)]


def test_wage_and_income_measures_remain_distinct() -> None:
    wage = indicator("average-hourly-wages")
    income = indicator("household-disposable-income-per-person")
    assert wage["frequency"] == "monthly"
    assert income["frequency"] == "quarterly"
    assert wage["sourceIdentifier"] != income["sourceIdentifier"]
    assert "employed workers" in (GENERATED / "affordability-canada-food-wages.json").read_text()


@pytest.mark.parametrize(
    ("indicator_id", "components"),
    [
        ("food-to-income", {"food-cpi", "household-disposable-income-per-person"}),
        ("rent-to-income", {"rent-cpi", "household-disposable-income-per-person"}),
        ("shelter-to-income", {"shelter-cpi", "household-disposable-income-per-person"}),
        ("mortgage-interest-to-income", {"mortgage-interest-cost", "household-disposable-income-per-person"}),
        ("nhpi-to-income", {"new-housing-price-index", "household-disposable-income-per-person"}),
    ],
)
def test_affordability_ratio_schema_and_components(indicator_id: str, components: set[str]) -> None:
    payload = indicator(indicator_id)
    assert payload["frequency"] == "quarterly"
    assert set(payload["components"]) == components
    assert payload["referencePeriod"] == "2017-01-01"
    assert payload["futureClassifierMetadata"]["status"] == "Not yet evaluated"
    assert payload["observations"] == sorted(payload["observations"], key=lambda row: row["date"])
    assert all(row["date"][5:7] in {"01", "04", "07", "10"} for row in payload["observations"])
    reference = next(row for row in payload["observations"] if row["date"] == "2017-01-01")
    assert reference["value"] == pytest.approx(100)


def test_generated_income_schema_and_formula_disclosure() -> None:
    required = {"source", "geography", "definition", "frequency", "unit", "seasonalAdjustment", "nominalOrReal", "sourceDate", "retrievalDate", "revisionStatus", "calculation", "components", "referencePeriod", "latest", "observations"}
    for indicator_id in ["household-disposable-income", "real-disposable-income-per-person", "real-wage-index", "food-to-income", "residential-property-price-to-income"]:
        payload = indicator(indicator_id)
        assert not required - payload.keys()
        assert payload["calculation"]["formula"]
        assert payload["observations"]


def test_ratio_uses_only_common_dates() -> None:
    prices = source([("2025-01-01", 100), ("2025-04-01", 110)], frequency="quarterly")
    income = source([("2025-01-01", 100)], frequency="quarterly")
    ratio = _ratio(prices, income, "ratio", "Ratio")
    assert [row.date for row in ratio.observations] == ["2025-01-01"]
