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
    assert groups == {"Absolute affordability", "Food", "Housing", "Energy"}


def test_absolute_affordability_is_separate_from_direction() -> None:
    refinery = EvidenceRefinery(ROOT)
    for geography in ("canada", "us"):
        for topic in ("affordability", "food", "housing"):
            result = refinery.generate(geography, topic)
            assert result["absoluteStatus"] in {"affordable", "pressured", "unaffordable", "severe-shortfall"}
            assert result["direction"] in {"worsening", "stable", "easing", "unclear"}
            assert result["income"]["value"] > 0
            assert result["essentialCost"]["value"] > 0
            assert result["costShare"] > 0
            assert result["thresholdUsed"]["classification"]["geography"] == geography

    refinery.absolute_rules["geographies"]["canada"]["income"]["value"] = 65_000
    result = refinery.generate("canada", "affordability")
    assert result["absoluteStatus"] == "unaffordable"
    assert result["direction"] == "easing"
    assert result["interpretation"] == "Unaffordable · easing"


def test_global_absolute_affordability_is_insufficient_not_mixed() -> None:
    for topic in ("affordability", "food", "housing"):
        result = generate_evidence_summary("global", topic, ROOT)
        assert result["absoluteStatus"] == "insufficient"
        assert result["direction"] == "unclear"
        assert result["insufficient"]
        assert not result["mixed"]


def test_absolute_threshold_configuration_has_published_provenance() -> None:
    config = json.loads((ROOT / "config" / "absolute_affordability.json").read_text(encoding="utf-8"))
    required = {"geography", "householdType", "definition", "source", "observationDate", "limitations"}
    for geography in ("canada", "us"):
        for topic in ("affordability", "food", "housing"):
            thresholds = config["geographies"][geography]["topics"][topic]["thresholds"]
            assert {item["status"] for item in thresholds} == {"affordable", "pressured", "unaffordable", "severe-shortfall"}
            assert all(required <= item.keys() and ("value" in item or "formula" in item) for item in thresholds)


def test_one_interface_handles_all_configured_geographies() -> None:
    expected = {
        ("us", "current-state"): "us:current-state",
        ("canada", "current-state"): "canada:current-state",
        ("ontario", "indicator-state"): "ontario:indicator-state",
        ("alberta", "indicator-state"): "alberta:indicator-state",
        ("global", "indicator-state"): "global:indicator-state",
    }
    for arguments, key in expected.items():
        result = generate_evidence_summary(*arguments, ROOT)
        assert result["evidenceKey"] == key


def test_migrated_narratives_remain_unchanged() -> None:
    payload = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))["evidence"]
    assert payload["us:current-state"]["interpretation"] == "Mixed transition: Physical tightening/Energy affordability stress"
    assert payload["canada:current-state"]["interpretation"] == "Consumer affordability stress"
    assert payload["canada:food"]["interpretation"] == "Affordable · worsening"


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
