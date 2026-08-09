"""Export the versioned systemic-energy contract consumed by Living Region.

This deliberately exports evidence and compatibility metadata separately from
Living Region scenario parameters. A contextual indicator is not silently
converted into a fuel, fertilizer, transport, or purchasing-power coefficient.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_indicator(relative: str) -> dict[str, Any] | None:
    path = ROOT / relative
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def latest_indicator(indicator_id: str, relative: str) -> dict[str, Any]:
    data = load_indicator(relative)
    if not data:
        return {"indicator_id": indicator_id, "status": "missing"}
    latest = data.get("latest") or (data.get("observations") or [{}])[-1]
    return {
        "indicator_id": indicator_id,
        "label": data.get("label"),
        "value": latest.get("value"),
        "unit": data.get("unit"),
        "observation_date": latest.get("date") or data.get("sourceDate"),
        "source_date": latest.get("sourceDate") or data.get("sourceDate"),
        "retrieval_date": data.get("retrievalDate"),
        "source": data.get("source"),
        "source_url": data.get("sourceUrl"),
        "evidence_status": data.get("status"),
        "evidence_label": data.get("evidenceLabel"),
        "confidence": data.get("confidenceLevel"),
        "limitations": data.get("limitations", []),
    }


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def field(field_id: str, unit: str, status: str, description: str, *, value: float | None = None, evidence: list[str] | None = None, notes: str = "") -> dict[str, Any]:
    return {
        "field_id": field_id,
        "value": value,
        "unit": unit,
        "evidence_status": status,
        "description": description,
        "evidence_indicator_ids": evidence or [],
        "notes": notes,
    }


def build_contract() -> dict[str, Any]:
    indicators = [
        latest_indicator("canada-energy-cpi-yoy", "website/public/generated/canada/indicators/canada-energy-cpi-yoy.json"),
        latest_indicator("canada-gasoline-cpi-yoy", "website/public/generated/canada/indicators/canada-gasoline-cpi-yoy.json"),
        latest_indicator("canada-fuel-oil-cpi-yoy", "website/public/generated/canada/indicators/canada-fuel-oil-cpi-yoy.json"),
        latest_indicator("canada-natural-gas-cpi-yoy", "website/public/generated/canada/indicators/canada-natural-gas-cpi-yoy.json"),
        latest_indicator("canada-refinery-input-growth", "website/public/generated/canada/indicators/canada-refinery-input-growth.json"),
        latest_indicator("canada-crude-exports-growth", "website/public/generated/canada/indicators/canada-crude-exports-growth.json"),
        latest_indicator("freight-activity", "website/public/generated/canada/indicators/freight-activity.json"),
        latest_indicator("global-food-price-index", "website/public/generated/global/indicators/fao-food-price-index.json"),
        latest_indicator("canada-real-food-price-index", "website/public/generated/canada/indicators/canada-real-food-price-index.json"),
        latest_indicator("canada-food-inflation-gap", "website/public/generated/canada/indicators/canada-food-inflation-gap.json"),
        latest_indicator("canada-real-wage-index", "website/public/generated/canada/indicators/real-wage-index.json"),
        latest_indicator("canada-real-wage-growth", "website/public/generated/canada/indicators/real-wage-growth.json"),
        latest_indicator("canada-disposable-income-per-person", "website/public/generated/canada/indicators/household-disposable-income-per-person.json"),
        latest_indicator("canada-household-saving-rate", "website/public/generated/canada/indicators/household-saving-rate.json"),
    ]
    global_food_price = next((item.get("value") for item in indicators if item.get("indicator_id") == "global-food-price-index"), None)
    return {
        "contract_id": "living-region.systemic-energy",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "producer": {
            "repository": "https://github.com/AndriiZvorygin/energy-model",
            "git_commit": git_commit(),
            "generator": "scripts/export_living_region_contract.py",
        },
        "scope": {
            "upstream_scale": "global_and_canadian_energy_economic_conditions",
            "downstream_consumer": "Living Region regional metabolism, land, food, labour and transition scenarios",
            "geography": ["global", "Canada", "Ontario context where available"],
        },
        "fields": [
            field("fuelAvailabilityIndex", "index (1 = scenario baseline)", "not_available", "Physical fuel availability or supply-loss parameter.", notes="Energy Model contains price, production, refinery and consumption indicators but no validated fuel-availability index."),
            field("fuelPriceIncreasePct", "percent", "contextual_evidence_only", "Direct fuel price increase parameter for Living Region scenarios.", evidence=["canada-energy-cpi-yoy", "canada-gasoline-cpi-yoy", "canada-fuel-oil-cpi-yoy"], notes="The listed CPI growth series are not a diesel price series and must not be substituted automatically."),
            field("dieselPriceMultiplier", "ratio", "not_available", "Diesel price multiplier relative to a documented baseline.", evidence=["canada-energy-cpi-yoy"], notes="Requires a diesel-specific price series and baseline definition."),
            field("fertilizerAvailabilityIndex", "index (1 = scenario baseline)", "not_available", "Physical fertilizer availability or supply-loss parameter.", notes="No fertilizer supply/availability series is published by the current Energy Model contract."),
            field("fertilizerPriceMultiplier", "ratio", "not_available", "Fertilizer price multiplier relative to a documented baseline.", notes="Do not infer from oil or natural-gas CPI without a fertilizer-specific pass-through model."),
            field("transportCostMultiplier", "ratio", "contextual_evidence_only", "Transport cost multiplier used by local food and freight scenarios.", evidence=["freight-activity", "canada-energy-cpi-yoy", "canada-refinery-input-growth"], notes="Freight activity and energy-price changes are contextual signals, not a calibrated cost multiplier."),
            field("importPricePressureMultiplier", "ratio", "contextual_evidence_only", "Import-price pressure applied to food and essential goods.", evidence=["global-food-price-index", "canada-real-food-price-index", "canada-food-inflation-gap"], notes="Food-price indexes provide upstream pressure evidence; Living Region must retain its scenario multiplier until pass-through is calibrated."),
            field("globalFoodPricePressure", "index or documented scenario value", "measured_contextual", "Global food-price pressure indicator.", value=global_food_price, evidence=["global-food-price-index"]),
            field("lowerSurplusEnergyPurchasingPowerProxy", "index or documented scenario value", "contextual_evidence_only", "Purchasing-power pressure related to energy and essential costs.", evidence=["canada-real-wage-index", "canada-real-wage-growth", "canada-disposable-income-per-person", "canada-household-saving-rate"], notes="These indicators can inform the proxy but cannot be collapsed into the existing coefficient without a documented model."),
            field("tradeCompetitionIndex", "index", "not_available", "Trade competition or export-restriction scenario parameter.", evidence=["global-food-price-index"], notes="No direct trade-competition estimate is produced."),
            field("householdAffordabilityTransmissionShare", "share", "not_available", "Share of upstream pressure transmitted to households.", evidence=["canada-real-wage-index", "canada-disposable-income-per-person"], notes="Requires regional household pass-through calibration."),
        ],
        "indicators": indicators,
        "compatibility": {
            "rule": "Living Region may import measured/contextual indicators, but only values with matching semantics may populate scenario coefficients.",
            "current_living_region_scenario_assumptions": [
                "fuelAvailabilityIndex", "fuelPriceIncreasePct", "dieselPriceMultiplier", "fertilizerAvailabilityIndex", "fertilizerPriceMultiplier", "transportCostMultiplier", "importPricePressureMultiplier", "tradeCompetitionIndex", "householdAffordabilityTransmissionShare", "lowerSurplusEnergyPurchasingPowerProxy"
            ],
            "currently_safe_direct_import": ["globalFoodPricePressure"],
            "requires_local_calibration": ["fuelPriceIncreasePct", "dieselPriceMultiplier", "transportCostMultiplier", "importPricePressureMultiplier", "lowerSurplusEnergyPurchasingPowerProxy", "householdAffordabilityTransmissionShare"],
        },
        "provenance_requirements": ["source dates", "retrieval dates", "source URL", "evidence status", "confidence", "limitations"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "contracts/living-region/systemic-energy-v1.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_contract(), indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
