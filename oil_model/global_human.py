from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .cache import RawCache
from .sources import GlobalHumanImpactAdapter
from .storage import write_csv


TOPIC_INDICATORS = {
    "food-security": [
        "undernourishment", "moderate_or_severe_food_insecurity", "severe_food_insecurity",
        "healthy_diet_unaffordable", "cost_of_healthy_diet", "dietary_energy_supply",
    ],
    "nutrition": ["child_stunting", "child_wasting", "anaemia_women", "low_birth_weight"],
    "human-impact": [
        "undernourishment", "moderate_or_severe_food_insecurity", "severe_food_insecurity",
        "healthy_diet_unaffordable", "child_stunting", "child_wasting", "anaemia_women",
        "low_birth_weight", "nutritional_deficiency_deaths", "protein_energy_malnutrition_deaths",
        "nutritional_deficiency_dalys", "protein_energy_malnutrition_dalys",
    ],
    "demography": [
        "total_population", "annual_population_growth_rate", "annual_population_increase",
        "births", "under_five", "working_age",
    ],
}

TOPIC_TITLES = {
    "food-security": "Global food access and affordability",
    "nutrition": "Global biological nutrition outcomes",
    "human-impact": "Global human impact of food and nutrition insecurity",
    "demography": "Global demographic exposure",
}

LABELS = {
    "total_population": "World population",
    "annual_population_growth_rate": "World population growth rate",
    "annual_population_increase": "Annual world population increase",
    "births": "Annual births",
    "under_five": "Population under age five",
    "working_age": "Working-age population",
}


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def _percentile(values: list[float], current: float) -> float:
    return 100 * (sum(value < current for value in values) + .5 * sum(value == current for value in values)) / len(values)


def _primary_value(row: dict[str, Any]) -> tuple[float | None, str | None]:
    if row.get("prevalence_or_rate") is not None:
        return float(row["prevalence_or_rate"]), row.get("rate_unit")
    if row.get("affected_person_count") is not None:
        return float(row["affected_person_count"]), row.get("count_unit")
    return None, None


def _momentum(rows: list[dict[str, Any]]) -> str:
    if len(rows) < 2:
        return "unclear"
    latest, previous = _primary_value(rows[-1])[0], _primary_value(rows[-2])[0]
    if latest is None or previous is None:
        return "unclear"
    tolerance = max(abs(previous) * .001, 1e-9)
    return "rising" if latest > previous + tolerance else "falling" if latest < previous - tolerance else "steady"


def _indicator_payload(indicator: str, rows: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    rows = sorted(rows, key=lambda row: row["year"])
    latest = rows[-1]
    previous = rows[-2] if len(rows) > 1 else None
    values = [value for row in rows if (value := _primary_value(row)[0]) is not None and math.isfinite(value)]
    latest_value, unit = _primary_value(latest)
    previous_value = _primary_value(previous)[0] if previous else None
    stressful = indicator not in {
        "total_population", "annual_population_growth_rate", "annual_population_increase", "births",
        "under_five", "working_age", "dietary_energy_supply",
    }
    demographic = indicator in TOPIC_INDICATORS["demography"]
    observation_date = lambda row: f"{row['year']}-07-01" if demographic else f"{row['year']}-12-31"
    momentum = _momentum(rows)
    if demographic:
        interpretation_label = "Neutral"
        interpretation = "Demographic exposure changes the number of people exposed to conditions but does not establish hardship by itself."
    elif stressful:
        interpretation_label = "Stressful" if latest_value is not None and _percentile(values, latest_value) >= 60 else "Mixed"
        interpretation = "Higher prevalence, affected-person counts, mortality, or disability burden generally indicates greater human impact."
    else:
        interpretation_label = "Mixed"
        interpretation = "This supply or cost measure provides context and must be read alongside access and biological outcomes."
    source_date = observation_date(latest)
    return {
        "schemaVersion": 1,
        "id": f"global-{indicator.replace('_', '-')}",
        "field": f"global_{indicator}",
        "label": latest.get("label") or LABELS.get(indicator, indicator.replace("_", " ").title()),
        "description": interpretation,
        "definition": latest.get("label") or indicator.replace("_", " "),
        "unit": unit or "not available",
        "frequency": "annual",
        "status": "modelled" if "model" in str(latest.get("estimate_type", "")).lower() else "measured",
        "layer": "Demographic exposure" if demographic else "Food access" if indicator in TOPIC_INDICATORS["food-security"] else "Nutrition outcomes" if indicator in TOPIC_INDICATORS["nutrition"] else "Mortality and health burden",
        "geography": "Global",
        "geographyLevel": "global",
        "domesticOrExternal": "external",
        "directlyComparableAcrossCountries": False,
        "comparisonLimitations": latest["limitations"],
        "interpretationDirection": "context-dependent" if demographic else "higher-generally-stressful" if stressful else "context-dependent",
        "interpretationLabel": interpretation_label,
        "interpretation": interpretation,
        "source": latest["source"],
        "sourceUrl": latest["source_url"],
        "sourceIdentifier": indicator,
        "sourceDate": source_date,
        "retrievalDate": generated_at,
        "revisionStatus": latest["revision"],
        "seasonalAdjustment": "not applicable",
        "nominalOrReal": "population estimate" if demographic else "prevalence, count, rate, or burden estimate",
        "startDate": observation_date(rows[0]),
        "endDate": source_date,
        "latest": {
            "date": source_date,
            "sourceDate": source_date,
            "value": latest_value,
            "previousValue": previous_value,
            "oneYearChange": latest_value - previous_value if latest_value is not None and previous_value is not None and latest["year"] - previous["year"] == 1 else None,
            "threeMonthChange": None,
            "fourQuarterChange": latest_value - previous_value if latest_value is not None and previous_value is not None and latest["year"] - previous["year"] == 1 else None,
            "historicalPercentile": _percentile(values, latest_value) if latest_value is not None else None,
            "percentileSince2000": _percentile([_primary_value(row)[0] for row in rows if row["year"] >= 2000 and _primary_value(row)[0] is not None], latest_value) if latest_value is not None else None,
            "distanceFromMedian": latest_value - _quantile(values, .5) if latest_value is not None else None,
            "momentum": momentum,
        },
        "referenceRanges": {
            "historicalMedian": _quantile(values, .5), "p10": _quantile(values, .1), "p25": _quantile(values, .25),
            "p75": _quantile(values, .75), "p90": _quantile(values, .9), "minimum": min(values), "maximum": max(values),
        },
        "observations": [{
            "date": observation_date(row), "value": _primary_value(row)[0], "sourceDate": observation_date(row),
            "prevalenceOrRate": row.get("prevalence_or_rate"), "rateUnit": row.get("rate_unit"),
            "affectedPersonCount": row.get("affected_person_count"), "countUnit": row.get("count_unit"),
            "denominatorPopulation": row.get("denominator_population"), "ageGroup": row.get("age_group"),
            "sex": row.get("sex"), "estimateType": row.get("estimate_type"),
            "uncertaintyLower": row.get("uncertainty_lower"), "uncertaintyUpper": row.get("uncertainty_upper"),
        } for row in rows],
        "transformations": ["raw", "indexed", "pct_change", "zscore"],
        "confirmingIndicators": [], "conflictingIndicators": [], "evidenceChecks": [],
        "confidenceLevel": "medium", "evidenceLabel": "Contextual indicator" if demographic else "Supported historical pattern",
        "calculation": {
            "formula": "Official global aggregate; rates and affected-person counts are retained together.",
            "explanation": "The refinery uses the official published rate and count rather than multiplying a rounded percentage by population.",
            "example": f"Latest observation: {latest_value:.2f} {unit} in {latest['year']}." if latest_value is not None else "No current value.",
        },
        "limitations": [latest["limitations"], latest["revision"]],
        "humanOutcomeMetadata": {
            "ageGroup": latest.get("age_group"), "sex": latest.get("sex"), "estimateType": latest.get("estimate_type"),
            "affectedPersonCount": latest.get("affected_person_count"), "countUnit": latest.get("count_unit"),
            "uncertaintyInterval": [latest.get("uncertainty_lower"), latest.get("uncertainty_upper")],
        },
        "futureClassifierMetadata": {
            "status": "metadata_only_not_scored",
            "candidateSymptoms": ["global food-access or nutrition outcome deterioration"] if not demographic else [],
        },
        "generatedAt": generated_at,
    }


def _direction(rows_by_indicator: dict[str, list[dict[str, Any]]], indicators: list[str]) -> str:
    votes = []
    for indicator in indicators:
        rows = rows_by_indicator.get(indicator, [])
        momentum = _momentum(rows)
        if momentum == "falling":
            votes.append("improving")
        elif momentum == "rising":
            votes.append("worsening")
        elif momentum == "steady":
            votes.append("stable")
    if not votes:
        return "unclear"
    if len(set(votes)) == 1:
        return votes[0]
    improving = votes.count("improving")
    worsening = votes.count("worsening")
    return "improving" if improving >= 2 * max(1, worsening) else "worsening" if worsening >= 2 * max(1, improving) else "unclear"


def _human_level(rows_by_indicator: dict[str, list[dict[str, Any]]], rules: dict[str, Any]) -> str:
    levels = {"limited": 0, "elevated": 1, "high": 2, "severe": 3}
    result = "limited"
    available = False
    for indicator, thresholds in rules["humanImpactLevel"].items():
        rows = rows_by_indicator.get(indicator, [])
        if not rows:
            continue
        value = _primary_value(rows[-1])[0]
        if value is None:
            continue
        available = True
        candidate = "severe" if value >= thresholds["severe"] else "high" if value >= thresholds["high"] else "elevated" if value >= thresholds["elevated"] else "limited"
        if levels[candidate] > levels[result]:
            result = candidate
    return result if available else "insufficient"


def build_global_human_outputs(root: Path, cache: RawCache) -> dict[str, Any]:
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    histories = GlobalHumanImpactAdapter(cache).fetch()
    files = {
        "food_security": "global_food_security_history.csv",
        "nutrition": "global_nutrition_history.csv",
        "human_impact": "global_human_impact_history.csv",
        "demography": "global_demography_history.csv",
    }
    for key, filename in files.items():
        write_csv(root / "analysis" / filename, histories[key])

    all_rows = [row for rows in histories.values() for row in rows]
    rows_by_indicator: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_rows:
        rows_by_indicator[row["indicator"]].append(row)
    for rows in rows_by_indicator.values():
        rows.sort(key=lambda row: row["year"])

    indicator_dir = root / "website" / "public" / "generated" / "global" / "indicators"
    indicator_dir.mkdir(parents=True, exist_ok=True)
    payloads = {}
    for indicator, rows in rows_by_indicator.items():
        payload = _indicator_payload(indicator, rows, generated_at)
        payloads[indicator] = payload
        (indicator_dir / f"{payload['id']}.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    rules = json.loads((root / "config" / "global_human_impact.json").read_text(encoding="utf-8"))
    food_direction = _direction(rows_by_indicator, ["undernourishment", "moderate_or_severe_food_insecurity", "severe_food_insecurity", "healthy_diet_unaffordable"])
    nutrition_direction = _direction(rows_by_indicator, TOPIC_INDICATORS["nutrition"])
    mortality_direction = _direction(rows_by_indicator, ["nutritional_deficiency_deaths", "protein_energy_malnutrition_deaths", "nutritional_deficiency_dalys"])
    directions = [food_direction, nutrition_direction, mortality_direction]
    human_direction = directions[0] if len(set(directions)) == 1 else "unclear"
    population_growth = _primary_value(rows_by_indicator["annual_population_growth_rate"][-1])[0]
    demographic_exposure = "growing" if population_growth and population_growth > rules["demography"]["growingAbove"] else "declining" if population_growth and population_growth < rules["demography"]["decliningBelow"] else "stable"
    ffpi_path = root / "website" / "public" / "generated" / "global" / "indicators" / "fao-food-price-index.json"
    upstream = "unclear"
    latest_upstream_year = None
    if ffpi_path.exists():
        ffpi = json.loads(ffpi_path.read_text(encoding="utf-8"))
        latest_upstream_year = ffpi["latest"]["date"]
        change = ffpi["latest"].get("yearOverYearPercentChange")
        upstream = "worsening" if change is not None and change > 1 else "easing" if change is not None and change < -1 else "stable"
    latest_years = {
        "latestUpstreamYear": latest_upstream_year,
        "latestFoodAccessYear": max(row["year"] for row in histories["food_security"]),
        "latestNutritionYear": max(row["year"] for row in histories["nutrition"]),
        "latestMortalityYear": max(row["year"] for row in histories["human_impact"]),
        "latestDemographyYear": max(row["year"] for row in histories["demography"]),
    }
    context = {
        "schemaVersion": 1, "generatedAt": generated_at,
        "scope": "Global human conditions assembled from official country-aggregated and inter-agency estimates.",
        "upstreamPressure": upstream,
        "humanImpactDirection": human_direction,
        "humanImpactLevel": _human_level(rows_by_indicator, rules),
        "demographicExposure": demographic_exposure,
        "componentDirections": {"foodAccess": food_direction, "nutrition": nutrition_direction, "mortality": mortality_direction},
        **latest_years,
        "staleDataWarnings": [
            f"WHO mortality and DALY evidence ends in {latest_years['latestMortalityYear']}; it is not aligned as a current observation with {latest_upstream_year} commodity prices.",
            "Nutrition outcomes are annual modelled estimates and may be revised after country-source and methodology updates.",
        ],
        "topicIndicators": {topic: [f"global-{indicator.replace('_', '-')}" for indicator in indicators if indicator in payloads] for topic, indicators in TOPIC_INDICATORS.items()},
        "missingIndicators": {
            "demography": ["urban population", "rural population"],
            "nutrition": ["severe wasting", "child underweight"],
            "human-impact": ["nutrition-attributable mortality distinct from direct cause-coded mortality", "uncertainty intervals for WHO GHE workbook summaries"],
        },
        "provenance": [
            "analysis/global_food_security_history.csv", "analysis/global_nutrition_history.csv",
            "analysis/global_human_impact_history.csv", "analysis/global_demography_history.csv",
        ],
    }
    global_dir = root / "website" / "public" / "generated" / "global"
    (global_dir / "human-impact-context.json").write_text(json.dumps(context, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    manifest_path = global_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    managed = {payload["id"] for payload in payloads.values()}
    manifest["indicators"] = [item for item in manifest.get("indicators", []) if item["id"] not in managed]
    manifest["indicators"].extend({
        "id": payload["id"], "file": f"indicators/{payload['id']}.json", "label": payload["label"],
        "layer": payload["layer"], "latestDate": payload["latest"]["date"],
    } for payload in payloads.values())
    manifest["humanImpact"] = {key: context[key] for key in ("upstreamPressure", "humanImpactDirection", "humanImpactLevel", "demographicExposure", *latest_years.keys())}
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return context
