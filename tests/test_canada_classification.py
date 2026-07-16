from __future__ import annotations

import json
from pathlib import Path

import pytest

from oil_model.canada_classification import (
    CANADIAN_SCOPE,
    _classification,
    _clock,
    _evaluate_symptoms,
    _quarterly_date,
    _summary,
    load_canadian_rules,
    regional_divergence,
)
from oil_model.classification import IndicatorEngine


ROOT = Path(__file__).resolve().parents[1]


def indicator(field: str, values: list[float], *, geography: str = "Canada", dates: list[str] | None = None, frequency: str = "monthly") -> dict:
    dates = dates or [f"2024-{month:02d}-01" for month in range(1, len(values) + 1)]
    observations = [{"date": date, "value": value, "sourceDate": date} for date, value in zip(dates, values)]
    return {
        "id": field.replace("_", "-"), "field": field, "label": field.replace("_", " ").title(),
        "unit": "percent", "frequency": frequency, "geography": geography,
        "inputType": "external" if geography == "Global" else "domestic", "confidenceLevel": "high",
        "observations": observations, "latest": {"date": observations[-1]["date"], "value": observations[-1]["value"]},
    }


def test_canadian_percentiles_use_only_supplied_canadian_history() -> None:
    engine = IndicatorEngine([indicator("canada_test", [1, 2, 3, 4])], {"monthlyMaximumAgeMonths": 6})
    point = engine.point("canada_test", "2024-04-01")
    assert point is not None
    assert point["historicalPercentile"] == pytest.approx(87.5)
    assert "us_test" not in engine.fields()


def test_regional_divergence_preserves_ontario_and_alberta_sides() -> None:
    high = [0, 1, 2, 10]
    low = [10, 2, 1, 0]
    rows = [
        indicator("ontario_energy_cpi_yoy", high, geography="Ontario"),
        indicator("ontario_gasoline_cpi_yoy", high, geography="Ontario"),
        indicator("ontario_employment_rate", low, geography="Ontario"),
        indicator("ontario_unemployment_rate", high, geography="Ontario"),
        indicator("ontario_prime_age_employment_rate", low, geography="Ontario"),
        indicator("alberta_crude_production_growth", high, geography="Alberta"),
        indicator("canada_mining_oil_gas_gdp_growth", high),
        indicator("canada_crude_exports_growth", high),
        indicator("global_wti_yoy", high, geography="Global"),
    ]
    result = regional_divergence(IndicatorEngine(rows, {"monthlyMaximumAgeMonths": 6}), "2024-04-01", {"low": 25, "high": 75})
    assert result["active"] is True
    assert result["status"] == "Regional divergence"
    assert result["ontarioTransmission"]["score"] >= 0.60
    assert result["albertaProducerConditions"]["score"] >= 0.60


def test_household_symptom_is_always_insufficient_without_required_series() -> None:
    symptoms, _ = load_canadian_rules(ROOT)
    engine = IndicatorEngine([indicator("canada_household_debt_service_ratio", [10, 11, 12, 13])], symptoms["settings"])
    result = _evaluate_symptoms(engine, symptoms, "2024-04-01", 1, "25_75")
    household = next(item for item in result if item["id"] == "household_stress")
    assert household["statusLabel"] == "Insufficient data"
    assert household["score"] == 0
    assert household["missingEvidence"]


def test_canadian_classifier_can_return_mixed_transition() -> None:
    symptoms = {
        "settings": {"thresholdSets": {"25_75": {"low": 25, "high": 75}}},
        "symptoms": [],
    }
    evidence = [{"indicator": "canada_test", "expectedDirection": "high", "layer": "national"}]
    regimes = {
        "settings": {"minimumEvidenceCoverage": 0.70, "minimumTopRegimeScore": 0.60, "minimumMargin": 0.10},
        "regimes": [
            {"id": "X", "name": "First Canadian state", "requiredLayers": ["national"], "indicatorEvidence": evidence, "expectedSymptoms": [], "conflictingSymptoms": []},
            {"id": "Y", "name": "Second Canadian state", "requiredLayers": ["national"], "indicatorEvidence": evidence, "expectedSymptoms": [], "conflictingSymptoms": []},
        ],
    }
    _, result = _classification(IndicatorEngine([indicator("canada_test", [0, 1, 2, 10])], {"monthlyMaximumAgeMonths": 6}), symptoms, regimes, "2024-04-01", 1, "25_75")
    assert result["classification"].startswith("Mixed transition:")


def test_quarterly_alignment_staleness_and_future_data_safety() -> None:
    dates = ["2026-03-01", "2026-06-01", "2026-07-01"]
    fresh = indicator("fresh", [1, 2, 3], dates=dates)
    old = indicator("old", [1], dates=["2025-01-01"])
    engine = IndicatorEngine([fresh, old], {"monthlyMaximumAgeMonths": 4, "quarterlyMaximumAgeMonths": 9})
    assert _quarterly_date(engine, {"fresh"}, 0.70) == "2026-06-01"
    point = engine.point("fresh", "2026-06-01")
    assert point is not None and point["value"] == 2
    metadata = _clock(engine, {"fresh", "old"}, "2026-06-01", "quarterly_aligned", "2026-07-16T00:00:00+00:00")
    assert metadata["staleIndicators"][0]["indicator"] == "old"
    assert metadata["dataVintageStatus"] == "retrospective_revised_data"
    assert "revised data" in metadata["revisedDataWarning"]


def test_generated_canadian_classification_schemas() -> None:
    base = ROOT / "website" / "public" / "generated" / "canada"
    current = json.loads((base / "current-classification.json").read_text())
    symptoms = json.loads((base / "symptom-evaluations.json").read_text())
    scores = json.loads((base / "regime-scores.json").read_text())
    assert current["scope"] == CANADIAN_SCOPE
    assert current["provisionalClassification"]["requiredIndicatorAvailability"] >= 0.70
    assert current["quarterlyAlignedClassification"]["classificationDate"].endswith(("03-01", "06-01", "09-01", "12-01"))
    assert len(symptoms["evaluations"]) == 6
    assert len(scores["scores"]) == 8
    assert next(item for item in symptoms["evaluations"] if item["id"] == "household_stress")["statusLabel"] == "Insufficient data"


def test_diagnostic_summary_only_reports_currently_relevant_symptoms() -> None:
    symptoms = [
        {"name": "Affordability pressure", "status": "active", "statusLabel": "Active", "plainLanguageMeaning": "Essential costs are elevated."},
        {"name": "Physical tightening", "status": "inactive", "statusLabel": "Inactive", "plainLanguageMeaning": "Inventories and prices are tightening."},
        {"name": "Household stress", "status": "insufficient_data", "statusLabel": "Insufficient data", "plainLanguageMeaning": "Household evidence is incomplete."},
    ]
    summary = _summary(symptoms, {"active": False}, "Consumer affordability stress")
    assert "Current Canadian state: Consumer affordability stress" in summary
    assert "Affordability pressure is active" in summary
    assert "Physical tightening" not in summary
    assert "Household stress" not in summary
    assert "insufficient" not in summary.lower()
