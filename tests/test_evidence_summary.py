from __future__ import annotations

import hashlib
import json
from pathlib import Path

from oil_model.evidence_summary import EvidenceRefinery, STATUS_TEXT, generate_evidence_summary, write_evidence_summary


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "website" / "public" / "generated"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_evidence_summary_schema_and_statuses() -> None:
    payload = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 2
    assert payload["statusDefinitions"] == STATUS_TEXT
    required = {
        "us:current-state", "us:regimes", "us:symptoms",
        "us:affordability", "us:food", "us:housing",
        "canada:overview", "canada:current-state", "canada:regimes", "canada:symptoms",
        "canada:affordability", "canada:food", "canada:housing",
        "ontario:indicator-state", "alberta:indicator-state", "global:indicator-state",
        "global:affordability", "global:food", "global:housing",
        "owen-sound:affordability", "owen-sound:food", "owen-sound:housing",
    }
    assert required <= payload["evidence"].keys()
    observed: set[str] = set()
    for key, topic in payload["evidence"].items():
        assert key == topic["evidenceKey"] == f"{topic['geography']}:{topic['topic']}"
        assert topic["interpretation"]
        assert topic["confidence"]
        for status in STATUS_TEXT:
            assert isinstance(topic[status], list)
            for row in topic[status]:
                observed.add(status)
                assert row["status"] == status
                assert row["reason"].startswith(STATUS_TEXT[status])
                assert row["group"]
                if row["indicatorFile"]:
                    assert (GENERATED / row["indicatorFile"]).exists()
    assert observed == set(STATUS_TEXT)


def test_symptom_evidence_preserves_checklist_groups_and_missing_data() -> None:
    payload = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))
    symptom_topics = [value for key, value in payload["evidence"].items() if ":symptom/" in key]
    groups = {row["group"] for topic in symptom_topics for status in STATUS_TEXT for row in topic[status]}
    assert {"Required evidence", "Confirming evidence", "Conflicting evidence", "Missing evidence"} <= groups
    household = payload["evidence"]["canada:symptom/household_stress"]
    assert household["insufficient"]


def test_affordability_summary_uses_documented_categories() -> None:
    payload = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))
    topic = payload["evidence"]["canada:affordability"]
    groups = {row["group"] for status in STATUS_TEXT for row in topic[status]}
    assert {"Absolute affordability", "Population hardship evidence", "Food", "Housing", "Energy"} <= groups


def test_absolute_affordability_is_separate_from_direction() -> None:
    refinery = EvidenceRefinery(ROOT)
    for geography in ("canada", "us"):
        for topic in ("affordability", "food", "housing"):
            result = refinery.generate(geography, topic)
            assert result["absoluteStatus"] in {"pressured", "unaffordable", "severe-shortfall", "unresolved"}
            assert result["direction"] in {"worsening", "stable", "easing", "unclear"}
            assert result["income"]["value"] > 0
            assert result["headlineInputs"]
            assert result["absoluteEvaluation"]["representativeBudgets"]

    assert refinery.generate("canada", "affordability")["absoluteStatus"] == "pressured"
    assert refinery.generate("us", "affordability")["absoluteStatus"] == "unresolved"


def test_global_absolute_affordability_is_insufficient_not_mixed() -> None:
    for topic in ("affordability", "food", "housing"):
        result = generate_evidence_summary("global", topic, ROOT)
        assert result["absoluteStatus"] == "insufficient"
        assert result["direction"] == "unclear"
        assert result["insufficient"]
        assert not result["mixed"]


def test_absolute_distribution_configuration_has_published_provenance() -> None:
    config = json.loads((ROOT / "config" / "absolute_affordability.json").read_text(encoding="utf-8"))
    required = {"label", "definition", "source", "sourceUrl", "observationDate", "limitations", "unit", "value"}
    for geography in ("canada", "us"):
        geography_rule = config["geographies"][geography]
        assert all(required <= measure.keys() for measure in geography_rule["distributionMeasures"].values())
        for topic in ("affordability", "food", "housing"):
            assert geography_rule["topics"][topic]["headlineMeasures"]


def test_canadian_reference_family_cannot_determine_national_verdict() -> None:
    result = generate_evidence_summary("canada", "affordability", ROOT)
    assert result["absoluteStatus"] == "pressured"
    assert result["income"]["value"] == 75_500
    assert result["income"]["definition"] == "Median after-tax income of economic families and unattached individuals"
    assert all(item.get("value") != 133_900 for item in result["headlineInputs"])
    budgets = result["absoluteEvaluation"]["representativeBudgets"]
    assert any(item.get("incomeReference") == 133_900 for item in budgets)
    cases = result["absoluteEvaluation"]["matchedHouseholdCases"]
    assert any(item["householdType"] == "Two-parent families with children" and item["status"] == "not-evaluated" for item in cases)


def test_national_headlines_use_population_hardship_shares() -> None:
    canada = generate_evidence_summary("canada", "affordability", ROOT)
    us = generate_evidence_summary("us", "affordability", ROOT)
    assert {item["id"] for item in canada["headlineInputs"]} >= {
        "mbm-poverty-rate", "food-insecurity-rate", "shelter-burden-30-rate", "core-housing-need-rate"
    }
    assert {item["id"] for item in us["headlineInputs"]} >= {
        "official-poverty-rate", "food-insecurity-rate", "housing-burden-30-rate", "housing-burden-50-rate"
    }
    assert canada["absoluteStatus"] != "affordable"
    assert us["absoluteStatus"] != "affordable"


def test_one_interface_handles_all_configured_geographies() -> None:
    expected = {
        ("us", "current-state"): "us:current-state",
        ("canada", "current-state"): "canada:current-state",
        ("ontario", "indicator-state"): "ontario:indicator-state",
        ("alberta", "indicator-state"): "alberta:indicator-state",
        ("global", "indicator-state"): "global:indicator-state",
        ("owen-sound", "affordability"): "owen-sound:affordability",
    }
    for arguments, key in expected.items():
        result = generate_evidence_summary(*arguments, ROOT)
        assert result["evidenceKey"] == key


def test_migrated_narratives_remain_unchanged() -> None:
    payload = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))["evidence"]
    assert payload["us:current-state"]["interpretation"] == "Mixed transition: Physical tightening/Energy affordability stress"
    assert payload["canada:current-state"]["interpretation"] == "Consumer affordability stress"
    assert payload["canada:food"]["interpretation"] == "Pressured · stable"


def test_owen_sound_uses_city_csd_and_local_household_incomes() -> None:
    config = json.loads((ROOT / "config" / "absolute_affordability.json").read_text(encoding="utf-8"))
    local = config["geographies"]["owen-sound"]
    assert "2021A00053542059" in local["referencePopulation"]
    assert local["descriptiveIncome"]["value"] == 57_600
    cases = {case["id"]: case for case in local["matchedHouseholdCases"]}
    assert cases["owen-sound-one-person"]["income"] == 31_800
    assert cases["owen-sound-couple-only"]["income"] == 71_000
    assert cases["owen-sound-couple-with-children"]["income"] == 101_000
    assert cases["owen-sound-one-parent"]["income"] == 56_400
    assert all(case["income"] not in {75_500, 133_900} for case in cases.values())


def test_owen_sound_household_cases_and_distribution_drive_topics() -> None:
    affordability = generate_evidence_summary("owen-sound", "affordability", ROOT)
    food = generate_evidence_summary("owen-sound", "food", ROOT)
    housing = generate_evidence_summary("owen-sound", "housing", ROOT)
    assert affordability["interpretation"] == "Pressured · unclear"
    assert food["interpretation"] == "Pressured · worsening"
    assert housing["interpretation"] == "Pressured · unclear"
    cases = {case["id"]: case for case in affordability["absoluteEvaluation"]["matchedHouseholdCases"]}
    assert cases["owen-sound-one-person"]["status"] == "pressured"
    assert cases["owen-sound-couple-only"]["status"] == "affordable"
    assert cases["owen-sound-couple-with-children"]["status"] == "affordable"
    assert cases["owen-sound-one-parent"]["status"] == "affordable"
    assert affordability["absoluteEvaluation"]["matchedHouseholdSummary"]["nonAffordableShare"] > 0.39
    housing_inputs = {item["id"]: item["value"] for item in housing["headlineInputs"]}
    assert housing_inputs["renter-shelter-burden-30-rate"] == 0.385
    assert housing_inputs["owner-shelter-burden-30-rate"] == 0.14
    assert housing_inputs["core-housing-need-rate"] == 0.114


def test_owen_sound_newer_context_does_not_set_structural_status() -> None:
    result = generate_evidence_summary("owen-sound", "affordability", ROOT)
    cases = result["absoluteEvaluation"]["matchedHouseholdCases"]
    assert all(case["classificationRule"] is not None for case in cases)
    assert all(case["basicNeedsCost"] and case["observationDate"] == "2020-01-01" for case in cases)
    assert all(case["newerFoodCost"] and case["newerRenterHousingCost"] for case in cases)
    assert result["direction"] == "unclear"


def test_temporary_2020_improvement_does_not_create_an_easing_headline() -> None:
    result = generate_evidence_summary("canada", "affordability", ROOT)
    history = result["historicalAffordability"]
    by_year = {row["year"]: row for row in history["historicalSeries"]}
    assert by_year[2020]["lowerDecileAffordabilityRatios"]["lowest"] > by_year[2024]["lowerDecileAffordabilityRatios"]["lowest"]
    assert history["direction"] == "stable"
    assert history["direction"] != "easing"


def test_national_median_cannot_override_lower_decile_hardship() -> None:
    result = generate_evidence_summary("canada", "affordability", ROOT)
    history = result["historicalAffordability"]
    assert history["medianAffordabilityRatio"] > 1.25
    assert history["populationBelowBasicNeeds"] == 0.10
    assert result["absoluteStatus"] == "pressured"


def test_owen_sound_regional_medians_cannot_override_city_hardship() -> None:
    result = generate_evidence_summary("owen-sound", "affordability", ROOT)
    history = result["historicalAffordability"]
    latest = history["historicalSeries"][-1]["medianHouseholdTypeRatios"]
    assert all(ratio and ratio > 1.25 for ratio in latest.values())
    assert history["contextOnly"] is True
    assert result["absoluteStatus"] == "pressured"
    assert result["direction"] == "unclear"


def test_live_affordability_summaries_publish_historical_provenance() -> None:
    for geography in ("canada", "owen-sound"):
        for topic in ("affordability", "food", "housing"):
            result = generate_evidence_summary(geography, topic, ROOT)
            provenance = {item["file"] for item in result["historicalAffordability"]["provenance"]}
            expected = "analysis/canada_absolute_affordability_history.csv" if geography == "canada" else "analysis/owen_sound_absolute_affordability_history.csv"
            assert expected in provenance
            assert "analysis/absolute_affordability_validation_history.csv" in provenance


def test_generation_does_not_modify_classifiers_or_locked_outputs() -> None:
    protected = [
        GENERATED / "current-classification.json",
        GENERATED / "regime-scores.json",
        GENERATED / "canada" / "current-classification.json",
        GENERATED / "canada" / "regime-scores.json",
        ROOT / "analysis" / "rolling_validation_extended.csv",
        ROOT / "analysis" / "final_findings_table.csv",
    ]
    before = {path: _hash(path) for path in protected}
    write_evidence_summary(ROOT)
    assert {path: _hash(path) for path in protected} == before
