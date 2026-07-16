from __future__ import annotations

import csv
import json
from pathlib import Path

from oil_model.historical_affordability import _metrics, _status


ROOT = Path(__file__).resolve().parents[1]


def test_absolute_status_uses_matched_income_to_threshold() -> None:
    assert _status(0.70) == "severe-shortfall"
    assert _status(0.90) == "unaffordable"
    assert _status(1.10) == "pressured"
    assert _status(1.30) == "affordable"
    assert _status(None) == "insufficient"


def test_budget_metrics_publish_components_and_residual() -> None:
    result = _metrics(income=50_000, threshold=40_000, food=10_000, shelter=15_000)
    assert result["income_relative_to_basic_needs"] == 1.25
    assert result["housing_cost_share_income"] == 0.30
    assert result["food_cost_share_income"] == 0.20
    assert result["food_plus_housing_share_income"] == 0.50
    assert result["residual_income_after_essential_costs"] == 10_000
    assert result["absolute_affordability_status"] == "affordable"


def test_generated_histories_keep_geographies_and_mbm_bases_separate() -> None:
    canada = list(csv.DictReader((ROOT / "analysis" / "canada_absolute_affordability_history.csv").open(encoding="utf-8")))
    owen = list(csv.DictReader((ROOT / "analysis" / "owen_sound_absolute_affordability_history.csv").open(encoding="utf-8")))
    assert {row["scope"] for row in canada} == {"Canada national distribution", "Canada matched urban-region household types"}
    assert {row["geography_level"] for row in owen} == {"census agglomeration", "census subdivision"}
    assert {row["year"] for row in owen if row["geography_level"] == "census subdivision"} == {"2015", "2020"}
    assert {row["threshold_base"] for row in canada} >= {"2000 base", "2008 base", "2018 base", "2023 base"}
    assert all(row["household_size"] in {"", "1", "2", "3", "4"} for row in canada)


def test_generated_history_json_is_annual_and_self_describing() -> None:
    for geography in ("canada", "owen-sound"):
        payload = json.loads((ROOT / "website" / "public" / "generated" / geography / "absolute-affordability-history.json").read_text(encoding="utf-8"))
        assert payload["schemaVersion"] == 1
        assert payload["frequency"] == "annual"
        assert payload["dateRange"]["start"] <= payload["dateRange"]["end"]
        assert payload["observations"]
        assert "unaffordable" in payload["statusDefinition"]
