from __future__ import annotations

import csv
import json
from pathlib import Path

from oil_model.evidence_summary import generate_evidence_summary


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "website" / "public" / "generated"


def _rows(name: str) -> list[dict[str, str]]:
    with (ROOT / "analysis" / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_global_human_histories_keep_rates_and_official_counts_together() -> None:
    rows = _rows("global_food_security_history.csv")
    latest = next(row for row in rows if row["indicator"] == "moderate_or_severe_food_insecurity" and row["year"] == "2024")
    assert float(latest["prevalence_or_rate"]) == 28.0
    assert float(latest["affected_person_count"]) == 2284.8
    assert latest["uncertainty_lower"] == "27.5"
    assert latest["uncertainty_upper"] == "28.5"


def test_global_human_topics_use_the_unified_refinery_interface() -> None:
    for topic in ("food-security", "nutrition", "human-impact", "demography"):
        result = generate_evidence_summary("global", topic, ROOT)
        assert result["evidenceKey"] == f"global:{topic}"
        assert result["scope"].startswith("Global upstream conditions")
        assert result["coverage"] > 0


def test_population_growth_is_exposure_not_hardship() -> None:
    result = generate_evidence_summary("global", "demography", ROOT)
    assert result["demographicExposure"] == "growing"
    assert "not human hardship" in result["interpretation"]
    assert not result["supporting"]


def test_global_clocks_do_not_align_stale_mortality_with_current_prices() -> None:
    result = generate_evidence_summary("global", "human-impact", ROOT)
    assert result["latestUpstreamYear"].startswith("2026")
    assert result["latestFoodAccessYear"] == 2024
    assert result["latestNutritionYear"] == 2024
    assert result["latestMortalityYear"] == 2021
    assert any("not aligned" in warning for warning in result["staleDataWarnings"])


def test_direct_mortality_is_distinct_from_attributable_burden() -> None:
    payload = json.loads((GENERATED / "global" / "indicators" / "global-nutritional-deficiency-deaths.json").read_text(encoding="utf-8"))
    assert any("do not capture" in limitation for limitation in payload["limitations"])
    assert payload["humanOutcomeMetadata"]["estimateType"] == "WHO modelled estimate"
