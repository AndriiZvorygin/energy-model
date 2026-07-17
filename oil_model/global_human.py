from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

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

CURRENT_HUMAN_OUTCOMES = [
    "undernourishment",
    "moderate_or_severe_food_insecurity",
    "severe_food_insecurity",
    "healthy_diet_unaffordable",
    "child_stunting",
    "child_wasting",
    "anaemia_women",
    "low_birth_weight",
    "nutritional_deficiency_deaths",
    "protein_energy_malnutrition_deaths",
    "nutritional_deficiency_dalys",
    "protein_energy_malnutrition_dalys",
]

FOOD_ACCESS_OUTCOMES = [
    "undernourishment",
    "moderate_or_severe_food_insecurity",
    "severe_food_insecurity",
    "healthy_diet_unaffordable",
]

NUTRITION_OUTCOMES = ["child_stunting", "child_wasting", "anaemia_women", "low_birth_weight"]

MORTALITY_OUTCOMES = [
    "nutritional_deficiency_deaths",
    "protein_energy_malnutrition_deaths",
    "nutritional_deficiency_dalys",
    "protein_energy_malnutrition_dalys",
]


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


def _window_change(rows: list[dict[str, Any]], years: int) -> float | None:
    if not rows:
        return None
    latest_year = int(rows[-1]["year"])
    latest = _primary_value(rows[-1])[0]
    earlier = next((row for row in reversed(rows) if int(row["year"]) == latest_year - years), None)
    previous = _primary_value(earlier)[0] if earlier else None
    return latest - previous if latest is not None and previous is not None else None


def _change_direction(change: float | None, reference: float | None) -> str:
    if change is None:
        return "unclear"
    tolerance = max(abs(reference or 0) * .001, 1e-9)
    return "worsening" if change > tolerance else "improving" if change < -tolerance else "stable"


def _direction_windows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    latest = _primary_value(rows[-1])[0] if rows else None
    windows = {}
    for years, label in ((1, "oneYear"), (3, "threeYear"), (5, "fiveYear")):
        change = _window_change(rows, years)
        windows[label] = {"change": change, "direction": _change_direction(change, latest)}
    return windows


def _direction(rows_by_indicator: dict[str, list[dict[str, Any]]], indicators: list[str], years: int = 3) -> str:
    votes: list[str] = []
    for indicator in indicators:
        rows = rows_by_indicator.get(indicator, [])
        if not rows:
            continue
        vote = _change_direction(_window_change(rows, years), _primary_value(rows[-1])[0])
        if vote != "unclear":
            votes.append(vote)
    if not votes:
        return "unclear"
    if len(set(votes)) == 1:
        return votes[0]
    improving = votes.count("improving")
    worsening = votes.count("worsening")
    return "improving" if improving >= 2 * max(1, worsening) else "worsening" if worsening >= 2 * max(1, improving) else "unclear"


def _human_level(rows_by_indicator: dict[str, list[dict[str, Any]]], rules: dict[str, Any], eligible: set[str]) -> str:
    levels = {"limited": 0, "elevated": 1, "high": 2, "severe": 3}
    result = "limited"
    available = False
    for indicator, thresholds in rules["humanImpactLevel"].items():
        if indicator not in eligible:
            continue
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


def _annual_average(payload: dict[str, Any]) -> dict[int, float]:
    grouped: dict[int, list[float]] = defaultdict(list)
    for observation in payload.get("observations", []):
        value = observation.get("value")
        if value is not None:
            grouped[int(str(observation["date"])[:4])].append(float(value))
    return {year: float(np.mean(values)) for year, values in grouped.items() if values}


def _annual_volatility(payload: dict[str, Any]) -> dict[int, float]:
    observations = sorted(payload.get("observations", []), key=lambda row: row["date"])
    grouped: dict[int, list[float]] = defaultdict(list)
    previous = None
    for observation in observations:
        value = observation.get("value")
        if value is not None and previous not in (None, 0):
            grouped[int(str(observation["date"])[:4])].append(100 * (float(value) / previous - 1))
        previous = float(value) if value is not None else previous
    return {year: float(np.std(values, ddof=1)) for year, values in grouped.items() if len(values) > 1}


def _processed_annual_average(root: Path, field: str) -> dict[int, float]:
    grouped: dict[int, list[float]] = defaultdict(list)
    with (root / "data" / "processed" / "monthly_dataset.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get(field) not in (None, ""):
                grouped[int(row["month"][:4])].append(float(row[field]))
    return {year: float(np.mean(values)) for year, values in grouped.items() if values}


def _expanding_lag_test(
    outcome: dict[int, float], predictor: dict[int, float], lag: int, population: dict[int, float] | None = None,
) -> dict[str, Any] | None:
    years = sorted(
        year for year in outcome
        if year - lag in predictor and year - 1 in outcome and (population is None or year in population)
    )
    if len(years) < 12:
        return None
    predictions: list[float] = []
    actuals: list[float] = []
    previous_baseline: list[float] = []
    trend_baseline: list[float] = []
    population_baseline: list[float] = []
    evaluation_years: list[int] = []
    for index in range(8, len(years)):
        year = years[index]
        training_years = years[:index]
        x = np.asarray([predictor[item - lag] for item in training_years], dtype=float)
        y = np.asarray([outcome[item] for item in training_years], dtype=float)
        pandemic = np.asarray([1.0 if item in {2020, 2021} else 0.0 for item in training_years])
        design = np.column_stack([np.ones(len(x)), x, pandemic])
        coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
        predictions.append(float(coefficients[0] + coefficients[1] * predictor[year - lag] + coefficients[2] * (year in {2020, 2021})))
        actuals.append(outcome[year])
        previous_baseline.append(outcome[year - 1])
        prior = sorted(item for item in outcome if item < year)[-3:]
        if len(prior) >= 2:
            slope, intercept = np.polyfit(np.asarray(prior, dtype=float), np.asarray([outcome[item] for item in prior]), 1)
            trend_baseline.append(float(intercept + slope * year))
        else:
            trend_baseline.append(outcome[year - 1])
        if population:
            pop_training = [item for item in training_years if item in population]
            pop_x = np.asarray([population[item] for item in pop_training], dtype=float)
            pop_y = np.asarray([outcome[item] for item in pop_training], dtype=float)
            pop_design = np.column_stack([np.ones(len(pop_x)), pop_x])
            pop_coefficients = np.linalg.lstsq(pop_design, pop_y, rcond=None)[0]
            population_baseline.append(float(pop_coefficients[0] + pop_coefficients[1] * population[year]))
        else:
            population_baseline.append(outcome[year - 1])
        evaluation_years.append(year)
    if len(actuals) < 4:
        return None
    actual = np.asarray(actuals)
    model_error = actual - np.asarray(predictions)
    previous_error = actual - np.asarray(previous_baseline)
    trend_error = actual - np.asarray(trend_baseline)
    population_error = actual - np.asarray(population_baseline)
    rmse = lambda values: float(np.sqrt(np.mean(np.square(values))))
    model_rmse, previous_rmse, trend_rmse, population_rmse = rmse(model_error), rmse(previous_error), rmse(trend_error), rmse(population_error)
    best_baseline = min(previous_rmse, trend_rmse, population_rmse)
    return {
        "lag_years": lag,
        "observations": len(actuals),
        "first_oos_year": evaluation_years[0],
        "last_oos_year": evaluation_years[-1],
        "model_rmse": model_rmse,
        "previous_year_rmse": previous_rmse,
        "recent_trend_rmse": trend_rmse,
        "population_only_rmse": population_rmse,
        "improvement_vs_best_baseline_pct": 100 * (best_baseline - model_rmse) / best_baseline if best_baseline else None,
    }


def _write_nowcast_validation(
    root: Path,
    payloads: dict[str, dict[str, Any]],
    rows_by_indicator: dict[str, list[dict[str, Any]]],
    eligible: set[str],
) -> dict[str, Any]:
    predictor_files = {
        "fao_food_price_index": "fao-food-price-index.json",
        "fao_cereals_price_index": "fao-cereals-price-index.json",
        "fao_vegetable_oils_price_index": "fao-vegetable-oils-price-index.json",
    }
    indicator_dir = root / "website" / "public" / "generated" / "global" / "indicators"
    predictors = {
        name: _annual_average(json.loads((indicator_dir / filename).read_text(encoding="utf-8")))
        for name, filename in predictor_files.items() if (indicator_dir / filename).exists()
    }
    if (indicator_dir / "fao-food-price-index.json").exists():
        ffpi_payload = json.loads((indicator_dir / "fao-food-price-index.json").read_text(encoding="utf-8"))
        predictors["fao_food_price_volatility"] = _annual_volatility(ffpi_payload)
    predictors["wti_oil_price"] = _processed_annual_average(root, "WTI")
    population_rows = rows_by_indicator.get("annual_population_growth_rate", [])
    population = {
        int(row["year"]): float(_primary_value(row)[0]) for row in population_rows if _primary_value(row)[0] is not None
    }
    predictors["population_growth_exposure"] = population
    validation_rows: list[dict[str, Any]] = []
    for indicator in sorted(eligible):
        outcome = {
            int(row["year"]): float(_primary_value(row)[0])
            for row in rows_by_indicator.get(indicator, []) if _primary_value(row)[0] is not None
        }
        for predictor_name, predictor in predictors.items():
            for lag in range(4):
                result = _expanding_lag_test(outcome, predictor, lag, population)
                if result:
                    validation_rows.append({"outcome": indicator, "predictor": predictor_name, **result})
    write_csv(root / "analysis" / "global_human_nowcast_validation.csv", validation_rows)
    best = sorted(validation_rows, key=lambda row: row["improvement_vs_best_baseline_pct"] or -math.inf, reverse=True)
    passing = [row for row in validation_rows if row["observations"] >= 8 and (row["improvement_vs_best_baseline_pct"] or 0) >= 5]
    assessment = {
        "status": "unavailable_until_validated",
        "conclusion": None,
        "label": "Human-impact nowcast unavailable until validated",
        "testedLags": [0, 1, 2, 3],
        "validationMethod": "Expanding-window global-aggregate regressions at annual lags 0–3, with a 2020–2021 pandemic indicator, compared with previous-year, recent-trend, and population-only baselines.",
        "structuralBreakControls": ["pandemic indicator (2020–2021)"],
        "candidateModelsPassingInitialRmseRule": len(passing),
        "publicationReady": False,
        "reason": "A single revised global aggregate provides too few independent annual observations, does not resolve country heterogeneity, and cannot adequately control pandemic, conflict, income, displacement, and methodology breaks.",
        "availableCandidates": list(predictors),
        "missingCandidates": ["fertilizer prices", "broader energy-price index", "regional or country-panel outcome histories", "income and displacement controls", "real-time vintages"],
        "bestExploratoryResults": best[:5],
        "futureOutputRequirements": [
            "nowcastYear", "predicted outcome", "prediction interval", "upstream observation window",
            "selected lag", "validation performance", "baseline performance", "model version", "confidence",
            "explicit label: modelled estimate, not observed data",
        ],
    }
    lines = [
        "# Global Human-Impact Nowcast Validation", "",
        "No human-impact nowcast is published in this release.", "",
        "Annual lags 0 through 3 were tested with expanding-window validation against previous-year, recent-trend, and population-only baselines. A pandemic indicator covers 2020–2021. Population growth was treated as exposure, not hardship. The available global aggregates are too short and heterogeneous for a defensible current nowcast, even where an exploratory specification beats a baseline.", "",
        f"Exploratory specifications tested: {len(validation_rows)}. Initial 5% RMSE passes: {len(passing)}.", "",
        "Regional or country-panel validation, structural-break controls, prediction intervals, and real-time-vintage testing remain required before publication.", "",
    ]
    (root / "analysis" / "global_human_nowcast_assessment.md").write_text("\n".join(lines), encoding="utf-8")
    nowcast_path = root / "website" / "public" / "generated" / "global" / "human-impact-nowcast-validation.json"
    nowcast_path.write_text(json.dumps({
        "schemaVersion": 1,
        "assessment": assessment,
        "validationResults": validation_rows,
    }, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return assessment


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

    rules = json.loads((root / "config" / "global_human_impact.json").read_text(encoding="utf-8"))
    latest_observed_human_year = max(
        int(rows_by_indicator[indicator][-1]["year"])
        for indicator in CURRENT_HUMAN_OUTCOMES if rows_by_indicator.get(indicator)
    )
    max_current_lag = int(rules["policy"]["currentEligibilityMaxLagYears"])
    eligible = {
        indicator for indicator in CURRENT_HUMAN_OUTCOMES
        if rows_by_indicator.get(indicator)
        and int(rows_by_indicator[indicator][-1]["year"]) >= latest_observed_human_year - max_current_lag
    }
    maintained_series = [{
        "id": f"global-{indicator.replace('_', '-')}",
        "indicator": indicator,
        "latestYear": int(rows_by_indicator[indicator][-1]["year"]),
        "currentWeight": 1,
        "directionWindows": _direction_windows(rows_by_indicator[indicator]),
    } for indicator in CURRENT_HUMAN_OUTCOMES if indicator in eligible]
    stale_historical_series = [{
        "id": f"global-{indicator.replace('_', '-')}",
        "indicator": indicator,
        "latestYear": int(rows_by_indicator[indicator][-1]["year"]),
        "currentWeight": 0,
        "reason": f"Latest observation is more than {max_current_lag} year behind the {latest_observed_human_year} observed-human clock.",
        "directionWindows": _direction_windows(rows_by_indicator[indicator]),
    } for indicator in CURRENT_HUMAN_OUTCOMES if rows_by_indicator.get(indicator) and indicator not in eligible]

    indicator_dir = root / "website" / "public" / "generated" / "global" / "indicators"
    indicator_dir.mkdir(parents=True, exist_ok=True)
    payloads = {}
    for indicator, rows in rows_by_indicator.items():
        payload = _indicator_payload(indicator, rows, generated_at)
        if indicator in CURRENT_HUMAN_OUTCOMES:
            payload["currentAssessment"] = {
                "eligible": indicator in eligible,
                "currentWeight": 1 if indicator in eligible else 0,
                "latestObservedHumanYear": latest_observed_human_year,
                "directionWindows": _direction_windows(rows),
                "role": "maintained human outcome" if indicator in eligible else "historical supporting evidence",
            }
        payloads[indicator] = payload
        (indicator_dir / f"{payload['id']}.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    eligible_food = [indicator for indicator in FOOD_ACCESS_OUTCOMES if indicator in eligible]
    eligible_nutrition = [indicator for indicator in NUTRITION_OUTCOMES if indicator in eligible]
    eligible_human = [indicator for indicator in CURRENT_HUMAN_OUTCOMES if indicator in eligible]
    food_direction = _direction(rows_by_indicator, eligible_food, 3)
    nutrition_direction = _direction(rows_by_indicator, eligible_nutrition, 3)
    human_direction = _direction(rows_by_indicator, eligible_human, 3)
    recent_momentum = _direction(rows_by_indicator, eligible_human, 1)
    structural_context = _direction(rows_by_indicator, eligible_human, 5)
    mortality_direction = _direction(rows_by_indicator, MORTALITY_OUTCOMES, 3)
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
        "latestObservedHumanYear": latest_observed_human_year,
        "latestFoodAccessYear": max(row["year"] for row in histories["food_security"]),
        "latestNutritionYear": max(row["year"] for row in histories["nutrition"]),
        "latestIndicatorYear": max(int(rows_by_indicator[indicator][-1]["year"]) for indicator in CURRENT_HUMAN_OUTCOMES if rows_by_indicator.get(indicator)),
        "latestMortalityYear": max(row["year"] for row in histories["human_impact"]),
        "latestDemographyYear": max(row["year"] for row in histories["demography"]),
    }
    nowcast = _write_nowcast_validation(root, payloads, rows_by_indicator, eligible)
    context = {
        "schemaVersion": 2, "generatedAt": generated_at,
        "scope": "Global human conditions assembled from official country-aggregated and inter-agency estimates.",
        "upstreamPressure": upstream,
        "humanImpactDirection": human_direction,
        "humanImpactLevel": _human_level(rows_by_indicator, rules, eligible),
        "demographicExposure": demographic_exposure,
        "componentDirections": {
            "foodAccess": food_direction,
            "nutrition": nutrition_direction,
            "historicalDirectCauseCodedNutritionMortalityThrough2021": mortality_direction,
        },
        "observedHumanAssessment": {
            "throughYear": latest_observed_human_year,
            "level": _human_level(rows_by_indicator, rules, eligible),
            "direction": human_direction,
            "recentMomentumOneYear": recent_momentum,
            "primaryDirectionThreeYears": human_direction,
            "structuralContextFiveYears": structural_context,
            "humanEffectsAfterLatestYear": "not yet observed",
        },
        "historicalMortalityAssessment": {
            "label": "Historical direct cause-coded nutrition mortality trend through 2021",
            "throughYear": latest_years["latestMortalityYear"],
            "direction": mortality_direction,
            "currentWeight": 0,
        },
        "maintainedSeries": maintained_series,
        "staleHistoricalSeries": stale_historical_series,
        "currentUpstreamDate": latest_upstream_year,
        "unobservedPeriodStart": f"{latest_observed_human_year + 1}-01-01",
        "humanImpactNowcast": nowcast,
        **latest_years,
        "staleDataWarnings": [
            f"Human effects after {latest_observed_human_year} are not yet observed; {latest_upstream_year} commodity prices describe upstream pressure only.",
            f"WHO mortality and DALY evidence ends in {latest_years['latestMortalityYear']} and has zero weight in the latest human-impact headline.",
            "Low birth weight ends in 2020 and remains historical supporting evidence with zero current weight.",
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
            "analysis/global_human_nowcast_validation.csv", "analysis/global_human_nowcast_assessment.md",
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
    manifest["humanImpact"] = {key: context[key] for key in (
        "upstreamPressure", "humanImpactDirection", "humanImpactLevel", "demographicExposure",
        "currentUpstreamDate", "unobservedPeriodStart", *latest_years.keys(),
    )}
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return context
