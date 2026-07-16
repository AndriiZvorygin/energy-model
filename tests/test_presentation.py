from __future__ import annotations

import json
from pathlib import Path

from oil_model.presentation import write_presentation_contract


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "website" / "public" / "generated"


def test_presentation_contract_resolves_routes_to_generated_evidence() -> None:
    payload = write_presentation_contract(ROOT)
    evidence = json.loads((GENERATED / "evidence-summary.json").read_text(encoding="utf-8"))
    for route, presentation in payload["routes"].items():
        topic = evidence["topics"][presentation["evidenceTopic"]]
        assert presentation["route"] == route
        assert presentation["interpretation"] == topic["interpretation"]
        assert presentation["confidence"] == topic["confidence"]
        assert presentation["provenance"] == ["website/public/generated/evidence-summary.json"]


def test_presentation_contract_carries_provenance_and_regeneration_command() -> None:
    payload = json.loads((GENERATED / "presentation-manifest.json").read_text(encoding="utf-8"))
    assert payload["regenerationCommand"] == "python -m oil_model.pipeline --root . --refresh"
    assert payload["policy"]["excludeStatusesFromDiagnosticSummary"] == ["insufficient"]
    assert payload["policy"]["symptomStatusesInDiagnosticSummary"] == ["active", "emerging", "fading"]
    assert all(len(item["sha256"]) == 64 for item in payload["inputs"])


def test_canadian_presentation_contains_no_inactive_or_missing_summary_prose() -> None:
    payload = json.loads((GENERATED / "presentation-manifest.json").read_text(encoding="utf-8"))
    summary = payload["routes"]["/canada"]["interpretation"].lower()
    assert "inactive" not in summary
    assert "insufficient" not in summary
    assert "missing" not in summary


def test_live_diagnostic_pages_resolve_topics_from_route_contract() -> None:
    pages = [
        "Affordability.tsx", "FoodAffordability.tsx", "HousingAffordability.tsx",
        "Canada.tsx", "CanadaCurrentState.tsx", "CanadaRegimes.tsx", "CanadaSymptoms.tsx",
        "CurrentState.tsx", "Regimes.tsx", "Symptoms.tsx",
    ]
    for filename in pages:
        source = (ROOT / "website" / "src" / "pages" / filename).read_text(encoding="utf-8")
        assert "GeneratedRouteEvidenceSummary" in source, filename
    aggregate_topics = ["current_state_us", "current_state_canada", "regimes_us", "regimes_canada", "symptoms_us", "symptoms_canada", "affordability", "food", "housing", "canada"]
    combined = "\n".join((ROOT / "website" / "src" / "pages" / filename).read_text(encoding="utf-8") for filename in pages)
    assert not any(f'topic="{topic}"' in combined for topic in aggregate_topics)
