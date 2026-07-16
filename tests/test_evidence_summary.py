from __future__ import annotations

import hashlib
import json
from pathlib import Path

from oil_model.evidence_summary import STATUS_TEXT, write_evidence_summary


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "website" / "public" / "generated"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_evidence_summary_schema_and_statuses() -> None:
    payload = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    assert payload["statusDefinitions"] == STATUS_TEXT
    required = {
        "current_state_us", "current_state_canada", "regimes_us", "regimes_canada",
        "symptoms_us", "symptoms_canada", "affordability", "food", "housing", "canada",
    }
    assert required <= payload["topics"].keys()
    observed: set[str] = set()
    for topic in payload["topics"].values():
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
    symptom_topics = [value for key, value in payload["topics"].items() if key.startswith("symptom_")]
    groups = {row["group"] for topic in symptom_topics for status in STATUS_TEXT for row in topic[status]}
    assert {"Required evidence", "Confirming evidence", "Conflicting evidence", "Missing evidence"} <= groups
    household = payload["topics"]["symptom_canada_household_stress"]
    assert household["insufficient"]


def test_affordability_summary_uses_documented_categories() -> None:
    payload = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))
    topic = payload["topics"]["affordability"]
    groups = {row["group"] for status in STATUS_TEXT for row in topic[status]}
    assert groups == {"Food", "Housing", "Energy"}


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
