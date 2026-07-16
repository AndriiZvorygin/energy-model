from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analysis import feature, rolling_predictions
from .storage import Row


SCHEMA_VERSION = "1.1.0"
EVIDENCE_LABELS = {
    "Validated relationship",
    "Supported historical pattern",
    "Contextual indicator",
    "Experimental proxy",
    "Scenario concept",
}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _iso_date(value: object) -> str:
    text = str(value)
    if len(text) == 7:
        return f"{text}-01"
    if len(text) == 10:
        return text
    raise ValueError(f"Website chart date must be YYYY-MM or YYYY-MM-DD, got {text!r}")


def _series(
    key: str,
    label: str,
    unit: str,
    source: str,
    status: str,
    default_visible: bool = True,
    frequency: str | None = None,
    color: str | None = None,
    transformations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "unit": unit,
        "source": source,
        "status": status,
        "defaultVisible": default_visible,
        "frequency": frequency,
        "color": color,
        "transformations": transformations or ["raw", "indexed", "zscore"],
    }


def _dataset(
    dataset_id: str,
    title: str,
    description: str,
    frequency: str,
    series: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    transformations: list[str],
    evidence_label: str,
    methodology: dict[str, Any],
    static_figure: str,
    generated_at: str,
    annotations: list[str] | None = None,
    details: dict[str, Any] | None = None,
    reference_period: tuple[str, str] = ("2007-01-01", "2019-12-01"),
) -> dict[str, Any]:
    observations = sorted(observations, key=lambda row: row["date"])
    present = [row for row in observations if any(row.get(item["key"]) is not None for item in series)]
    final_dates = {
        item["key"]: max((row["date"] for row in observations if row.get(item["key"]) is not None), default=None)
        for item in series
    }
    reference_start, reference_end = reference_period
    statistics: dict[str, dict[str, float | int | None]] = {}
    for item in series:
        values = [
            float(row[item["key"]])
            for row in observations
            if reference_start <= row["date"] <= reference_end and _number(row.get(item["key"])) is not None
        ]
        mean = sum(values) / len(values) if values else None
        std = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) if values and mean is not None else None
        statistics[item["key"]] = {"mean": mean, "standardDeviation": std, "n": len(values)}
    details = details or {}
    sources = list(dict.fromkeys(item["source"] for item in series))
    formula = str(methodology.get("formula", "Values are displayed at their documented observation frequency."))
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "id": dataset_id,
        "title": title,
        "description": description,
        "plainLanguageSummary": details.get("plainLanguageSummary", description),
        "howToRead": details.get("howToRead", "Compare direction, turning points, and sustained divergences. Use the tooltip for exact values and observation dates; visual alignment alone does not establish causation."),
        "calculation": details.get("calculation", {"formula": formula, "explanation": str(methodology.get("notes", "The chart uses the documented project transformation without changing the underlying observations.")), "example": "A value at date t uses only observations dated t or earlier unless the chart explicitly labels a visual shift."}),
        "patternsToWatch": details.get("patternsToWatch", ["Persistent co-movement across several observations", "Turning points or divergences that repeat across historical episodes"]),
        "limitations": details.get("limitations", [str(methodology.get("notes", "Correlation and visual alignment can reflect common macro factors, revisions, or measurement choices."))]),
        "sourceNotes": details.get("sourceNotes", sources),
        "transformation": {"type": "raw", "referenceStart": reference_start, "referenceEnd": reference_end, "mean": None, "standardDeviation": None, "statistics": statistics},
        "frequency": frequency,
        "dateRange": {"start": present[0]["date"] if present else None, "end": present[-1]["date"] if present else None},
        "series": [{**item, "finalObservationDate": final_dates[item["key"]]} for item in series],
        "observations": observations,
        "annotations": annotations or [],
        "availableTransformations": transformations,
        "evidenceLabel": evidence_label,
        "methodology": methodology,
        "staticFigure": static_figure,
        "generatedAt": generated_at,
    }
    validate_chart_dataset(result)
    return result


def validate_chart_dataset(dataset: dict[str, Any]) -> None:
    required = {"schemaVersion", "id", "title", "description", "plainLanguageSummary", "howToRead", "calculation", "patternsToWatch", "limitations", "sourceNotes", "transformation", "frequency", "dateRange", "series", "observations", "methodology", "generatedAt", "evidenceLabel"}
    missing = sorted(required - dataset.keys())
    if missing:
        raise ValueError(f"Chart dataset {dataset.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if dataset["evidenceLabel"] not in EVIDENCE_LABELS:
        raise ValueError(f"Invalid evidence label for {dataset['id']}: {dataset['evidenceLabel']}")
    for field in ("formula", "explanation", "example"):
        if not dataset["calculation"].get(field):
            raise ValueError(f"Chart dataset {dataset['id']} calculation is missing {field}")
    if not dataset["transformation"].get("referenceStart") or not dataset["transformation"].get("referenceEnd"):
        raise ValueError(f"Chart dataset {dataset['id']} is missing a fixed transformation reference period")
    keys = [item.get("key") for item in dataset["series"]]
    if not keys or len(keys) != len(set(keys)):
        raise ValueError(f"Chart dataset {dataset['id']} has missing or duplicate series keys")
    for item in dataset["series"]:
        for field in ("key", "label", "unit", "source", "status", "defaultVisible", "finalObservationDate"):
            if field not in item:
                raise ValueError(f"Series {item.get('key')} in {dataset['id']} is missing {field}")
    dates = [row.get("date") for row in dataset["observations"]]
    if any(not isinstance(date, str) or len(date) != 10 for date in dates):
        raise ValueError(f"Chart dataset {dataset['id']} contains a non-ISO date")
    if dates != sorted(dates):
        raise ValueError(f"Chart dataset {dataset['id']} dates are not ordered")
    if len(dates) != len(set(dates)):
        raise ValueError(f"Chart dataset {dataset['id']} contains duplicate dates")
    for row in dataset["observations"]:
        for key in keys:
            value = row.get(key)
            if value is not None and not isinstance(value, (int, float)):
                raise ValueError(f"Chart dataset {dataset['id']} has non-numeric value for {key} at {row['date']}")


def _observations(rows: list[Row], mapping: dict[str, str], date_field: str = "month") -> list[dict[str, Any]]:
    return [
        {"date": _iso_date(row[date_field]), **{output: _number(row.get(source)) for output, source in mapping.items()}}
        for row in rows
        if row.get(date_field)
    ]


def _quality_observations(rows: list[Row], indicators: list[str]) -> list[dict[str, Any]]:
    dates = sorted({str(row["date"]) for row in rows if row.get("indicator") in indicators})
    lookup = {(str(row["date"]), str(row["indicator"])): _number(row.get("value")) for row in rows}
    return [{"date": date, **{indicator: lookup.get((date, indicator)) for indicator in indicators}} for date in dates]


def _regimes() -> list[dict[str, Any]]:
    return [
        {"id": "financial_crisis_2008_2009", "label": "Financial crisis", "start": "2008-01-01", "end": "2009-12-01", "color": "#64748b"},
        {"id": "shale_regime_2014_2017", "label": "Shale adjustment", "start": "2014-01-01", "end": "2017-12-01", "color": "#0f766e"},
        {"id": "covid_2020_2021", "label": "Pandemic disruption", "start": "2020-01-01", "end": "2021-12-01", "color": "#7c3aed"},
        {"id": "war_spr_2022_2023", "label": "War / SPR regime", "start": "2022-01-01", "end": "2023-12-01", "color": "#be123c"},
    ]


def _events() -> list[dict[str, Any]]:
    return [
        {"id": "oil_embargo_1973", "name": "Oil embargo", "start": "1973-10-01", "end": "1974-03-01", "category": "oil supply shock", "explanation": "A physical supply disruption and policy response sharply raised oil costs.", "layers": ["physical energy", "affordability", "economic activity"]},
        {"id": "gulf_war_1990", "name": "Gulf War oil shock", "start": "1990-08-01", "end": "1991-02-01", "category": "oil supply shock", "explanation": "Geopolitical supply risk produced a short, sharp oil-price shock.", "layers": ["physical energy", "oil pricing", "affordability"]},
        {"id": "gfc_2008", "name": "Financial crisis and oil collapse", "start": "2008-07-01", "end": "2009-06-01", "category": "financial crisis", "explanation": "An oil-price peak was followed by financial crisis, demand destruction, and price collapse; the overlap does not identify a single cause.", "layers": ["financial conditions", "oil pricing", "economic activity", "labour"]},
        {"id": "shale_2014", "name": "Shale supply adjustment", "start": "2014-06-01", "end": "2016-02-01", "category": "price collapse", "explanation": "Supply growth and changing producer strategy contributed to a prolonged oil-price decline.", "layers": ["physical energy", "oil pricing", "investment"]},
        {"id": "covid_2020", "name": "Pandemic and futures dislocation", "start": "2020-03-01", "end": "2020-06-01", "category": "pandemic disruption", "explanation": "Mobility restrictions collapsed petroleum demand and disrupted futures-linked exposure.", "layers": ["energy demand", "oil pricing", "tradable exposure", "economic activity"]},
        {"id": "reopening_2021", "name": "Demand recovery", "start": "2021-02-01", "end": "2022-06-01", "category": "demand recovery", "explanation": "Reopening demand, constrained supply chains, and geopolitical stress lifted energy prices and burden.", "layers": ["energy demand", "physical energy", "affordability", "inflation"]},
    ]


def _recession_periods(rows: list[Row]) -> list[dict[str, Any]]:
    periods: list[dict[str, Any]] = []
    start: str | None = None
    previous: str | None = None
    for row in rows:
        month = str(row.get("month"))
        active = _number(row.get("recession_dummy")) == 1
        if active and start is None:
            start = month
        if start is not None and not active:
            periods.append({"id": f"recession_{start}", "label": "NBER recession", "start": _iso_date(start), "end": _iso_date(previous or start), "color": "#78716c"})
            start = None
        previous = month
    if start is not None:
        periods.append({"id": f"recession_{start}", "label": "NBER recession", "start": _iso_date(start), "end": _iso_date(previous or start), "color": "#78716c"})
    return periods


def _quantile(values: list[float], probability: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _percentile(values: list[float], value: float) -> float | None:
    if not values:
        return None
    below = sum(item < value for item in values)
    equal = sum(item == value for item in values)
    return 100 * (below + 0.5 * equal) / len(values)


def _source_url(source: str) -> str:
    upper = source.upper()
    if "EIA" in upper:
        return "https://www.eia.gov/opendata/"
    if "BEA" in upper:
        return "https://www.bea.gov/data"
    if "BLS" in upper:
        return "https://www.bls.gov/data/"
    if "FRED" in upper or "FEDERAL RESERVE" in upper:
        return "https://fred.stlouisfed.org/"
    return "https://github.com/AndriiZvorygin/energy-model"


SUPPORTIVE_WHEN_RISING = {
    "petroleum_production_YoY", "real_disposable_income_YoY", "Industrial_production_YoY",
    "manufacturing_output_YoY", "real_consumer_spending_YoY", "business_investment_YoY",
    "Real_GDP_growth", "average_weekly_hours_YoY", "temporary_help_YoY",
    "full_time_employment_share", "prime_age_employment_rate", "real_wage_growth",
    "consumer_sentiment",
}
STRESSFUL_WHEN_RISING = {
    "household_energy_expenditure_share", "energy_expenditure_share_gdp", "energy_CPI_YoY",
    "credit_tightening_pct", "involuntary_part_time_share", "credit_card_delinquency_rate",
    "unemployment_rate",
}
CONTEXT_DEPENDENT = {
    "petroleum_consumption_YoY", "oil_consumption_per_person_mmbtu", "CI_zscore",
    "refinery_utilization_pct", "real_WTI_YoY", "fed_funds_rate", "GM2_YoY",
}

EVIDENCE_REFERENCE_FIELDS = {
    "business investment": "business_investment_YoY",
    "consumer sentiment": "consumer_sentiment",
    "credit conditions": "credit_tightening_pct",
    "credit standards": "credit_tightening_pct",
    "delinquency": "credit_card_delinquency_rate",
    "energy consumption": "petroleum_consumption_YoY",
    "energy cpi": "energy_CPI_YoY",
    "energy use": "petroleum_consumption_YoY",
    "full-time share": "full_time_employment_share",
    "gdp": "Real_GDP_growth",
    "gm2": "GM2_YoY",
    "hours": "average_weekly_hours_YoY",
    "household burden": "household_energy_expenditure_share",
    "income": "real_disposable_income_YoY",
    "industrial output": "Industrial_production_YoY",
    "industrial production": "Industrial_production_YoY",
    "investment": "business_investment_YoY",
    "involuntary part time": "involuntary_part_time_share",
    "manufacturing": "manufacturing_output_YoY",
    "oil burden": "energy_expenditure_share_gdp",
    "oil momentum": "real_WTI_YoY",
    "petroleum consumption": "petroleum_consumption_YoY",
    "prime-age employment": "prime_age_employment_rate",
    "real gdp": "Real_GDP_growth",
    "real income": "real_disposable_income_YoY",
    "real spending": "real_consumer_spending_YoY",
    "real wages": "real_wage_growth",
    "refinery utilization": "refinery_utilization_pct",
    "sentiment": "consumer_sentiment",
    "spending": "real_consumer_spending_YoY",
    "temporary help": "temporary_help_YoY",
    "unemployment": "unemployment_rate",
    "wages": "real_wage_growth",
    "weekly hours": "average_weekly_hours_YoY",
}


def _interpretation_direction(indicator_id: str) -> str:
    if indicator_id in SUPPORTIVE_WHEN_RISING:
        return "higher-generally-supportive"
    if indicator_id in STRESSFUL_WHEN_RISING:
        return "higher-generally-stressful"
    return "context-dependent"


def _interpretation_label(indicator_id: str, percentile: float | None, change: float | None) -> str:
    if percentile is None:
        return "Direction unclear"
    direction = _interpretation_direction(indicator_id)
    if direction == "higher-generally-supportive":
        if percentile >= 75 and (change is None or change >= 0):
            return "Supportive"
        if percentile <= 25 and (change is None or change <= 0):
            return "Stressful"
        return "Mixed" if change is not None else "Neutral"
    if direction == "higher-generally-stressful":
        if percentile >= 75 and (change is None or change >= 0):
            return "Stressful"
        if percentile <= 25 and (change is None or change <= 0):
            return "Supportive"
        return "Mixed" if change is not None else "Neutral"
    if percentile >= 90:
        return "Historically elevated"
    if percentile <= 10:
        return "Historically depressed"
    return "Neutral" if change is None or abs(change) < 1e-12 else "Mixed"


def _anomaly_score(indicator: dict[str, Any]) -> float | None:
    percentile = _number(indicator.get("latest", {}).get("historicalPercentile"))
    return abs(percentile - 50.0) if percentile is not None else None


def _current_state_snapshot(indicators: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    def sort_key(indicator: dict[str, Any]) -> tuple[bool, float, str]:
        score = _anomaly_score(indicator)
        return score is None, -(score or 0.0), str(indicator["label"])

    ordered = sorted(indicators, key=sort_key)

    def entries(labels: set[str]) -> list[dict[str, Any]]:
        return [
            {
                "id": indicator["id"],
                "field": indicator["field"],
                "label": indicator["label"],
                "layer": indicator["layer"],
                "interpretationLabel": indicator["interpretationLabel"],
                "latestDate": indicator["latest"]["date"],
                "historicalPercentile": indicator["latest"]["historicalPercentile"],
                "anomalyScore": _anomaly_score(indicator),
            }
            for indicator in ordered
            if indicator["interpretationLabel"] in labels
        ]

    dates = [str(indicator["latest"]["date"]) for indicator in indicators]
    return {
        "asOf": generated_at,
        "latestObservationDate": max(dates),
        "oldestLatestObservationDate": min(dates),
        "classificationMethod": "Interpretation labels are generated from each indicator's documented direction, full-history percentile, and recent change.",
        "anomalyMethod": "anomalyScore = abs(historicalPercentile - 50); larger values are farther from the indicator's historical midpoint.",
        "groups": {
            "supportive": entries({"Supportive"}),
            "stressful": entries({"Stressful"}),
            "other": entries({"Neutral", "Mixed", "Historically elevated", "Historically depressed", "Direction unclear"}),
        },
        "indicatorOrder": [indicator["field"] for indicator in ordered],
    }


def _attach_evidence_checks(indicators: list[dict[str, Any]]) -> None:
    by_field = {str(indicator["field"]): indicator for indicator in indicators}

    def polarity(indicator: dict[str, Any]) -> str | None:
        label = indicator.get("interpretationLabel")
        if label == "Supportive":
            return "supportive"
        if label == "Stressful":
            return "stressful"
        return None

    for indicator in indicators:
        subject_polarity = polarity(indicator)
        checks = []
        for reference in indicator.get("confirmingIndicators", []):
            field = EVIDENCE_REFERENCE_FIELDS.get(str(reference).strip().lower())
            target = by_field.get(field or "")
            target_polarity = polarity(target) if target else None
            status = "unclear"
            if subject_polarity and target_polarity:
                status = "confirms" if subject_polarity == target_polarity else "conflicts"
            checks.append({
                "label": reference,
                "status": status,
                "targetIndicatorId": target["id"] if target else None,
                "targetInterpretationLabel": target["interpretationLabel"] if target else None,
                "targetLatestDate": target["latest"]["date"] if target else None,
                "explanation": (
                    "The linked indicator has the same directional classification."
                    if status == "confirms"
                    else "The linked indicator has the opposite directional classification."
                    if status == "conflicts"
                    else "The relationship is unavailable or one of the readings is mixed or context-dependent."
                ),
            })
        indicator["evidenceChecks"] = checks


def _indicator_payload(
    indicator: Row,
    catalogue: Row | None,
    system_rows: list[Row],
    generated_at: str,
) -> dict[str, Any]:
    indicator_id = str(indicator["indicator_id"])
    all_observations = [
        {"date": _iso_date(row["month"]), "value": _number(row.get(indicator_id))}
        for row in system_rows
        if row.get("month")
    ]
    non_null = [row for row in all_observations if row["value"] is not None]
    if not non_null:
        raise ValueError(f"Current-state indicator {indicator_id} has no observations")
    start = non_null[0]["date"]
    end = non_null[-1]["date"]
    observations = [row for row in all_observations if start <= row["date"] <= end]
    values = [float(row["value"]) for row in non_null]
    latest = non_null[-1]
    previous = non_null[-2] if len(non_null) > 1 else None
    lookup = {row["date"]: row["value"] for row in non_null}

    def prior_value(months: int) -> float | None:
        year, month = map(int, latest["date"][:7].split("-"))
        index = year * 12 + month - 1 - months
        return _number(lookup.get(f"{index // 12:04d}-{index % 12 + 1:02d}-01"))

    latest_value = float(latest["value"])
    median = _quantile(values, 0.5)
    percentile = _percentile(values, latest_value)
    since_2000 = [float(row["value"]) for row in non_null if row["date"] >= "2000-01-01"]
    change_3m_base = prior_value(3)
    change_12m_base = prior_value(12)
    change_6m_base = prior_value(6)
    change_3m = latest_value - change_3m_base if change_3m_base is not None else None
    change_12m = latest_value - change_12m_base if change_12m_base is not None else None
    previous_3m_change = change_3m_base - change_6m_base if change_3m_base is not None and change_6m_base is not None else None
    momentum = "unavailable"
    if change_3m is not None and previous_3m_change is not None:
        momentum = "accelerating" if change_3m > previous_3m_change else "decelerating" if change_3m < previous_3m_change else "steady"
    source = str((catalogue or {}).get("source") or "Project processed dataset")
    unit = str((catalogue or {}).get("unit") or "index or documented source unit")
    formula = str((catalogue or {}).get("exact_definition") or indicator.get("indicator"))
    interpretation_label = _interpretation_label(indicator_id, percentile, change_3m)
    payload = {
        "schemaVersion": 1,
        "id": indicator_id.replace("_", "-").lower(),
        "field": indicator_id,
        "label": str(indicator["indicator"]),
        "description": formula,
        "unit": unit,
        "frequency": str(indicator.get("update_frequency") or "monthly"),
        "status": str((catalogue or {}).get("status") or "derived"),
        "layer": str(indicator["layer"]),
        "interpretationDirection": _interpretation_direction(indicator_id),
        "interpretationLabel": interpretation_label,
        "interpretation": str(indicator.get("interpretation") or "Interpret with confirming and conflicting evidence."),
        "source": source,
        "sourceUrl": _source_url(source),
        "startDate": start,
        "endDate": end,
        "latest": {
            "date": latest["date"],
            "value": latest_value,
            "previousValue": previous["value"] if previous else None,
            "oneYearChange": change_12m,
            "threeMonthChange": change_3m,
            "fourQuarterChange": change_12m,
            "historicalPercentile": percentile,
            "percentileSince2000": _percentile(since_2000, latest_value),
            "distanceFromMedian": latest_value - median if median is not None else None,
            "momentum": momentum,
        },
        "referenceRanges": {
            "historicalMedian": median,
            "p10": _quantile(values, 0.10),
            "p25": _quantile(values, 0.25),
            "p75": _quantile(values, 0.75),
            "p90": _quantile(values, 0.90),
            "minimum": min(values),
            "maximum": max(values),
        },
        "observations": observations,
        "confirmingIndicators": [item.strip() for item in str(indicator.get("confirming_indicators") or "").split(";") if item.strip()],
        "conflictingIndicators": [item.strip() for item in str(indicator.get("conflicting_indicators") or "").split(";") if item.strip()],
        "evidenceChecks": [],
        "confidenceLevel": str(indicator.get("confidence_level") or "low"),
        "evidenceLabel": str(indicator.get("evidence_label") or "Contextual indicator"),
        "calculation": {"formula": formula, "explanation": formula, "example": f"Latest published observation: {latest_value:.2f} {unit} at {latest['date'][:7]}."},
        "limitations": [str((catalogue or {}).get("data_quality_limitations") or "Latest-vintage data may be revised."), str((catalogue or {}).get("alternative_explanations") or "Interpret alongside other indicators.")],
        "generatedAt": generated_at,
    }
    validate_indicator_dataset(payload)
    return payload


def validate_indicator_dataset(dataset: dict[str, Any]) -> None:
    required = {"schemaVersion", "id", "label", "description", "unit", "frequency", "status", "interpretationDirection", "source", "sourceUrl", "startDate", "endDate", "latest", "referenceRanges", "observations", "evidenceLabel", "evidenceChecks"}
    missing = sorted(required - dataset.keys())
    if missing:
        raise ValueError(f"Indicator dataset {dataset.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if dataset["schemaVersion"] != 1:
        raise ValueError(f"Indicator dataset {dataset['id']} has unsupported schema version")
    dates = [row.get("date") for row in dataset["observations"]]
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        raise ValueError(f"Indicator dataset {dataset['id']} dates must be chronological and unique")
    if any(not isinstance(date, str) or len(date) != 10 for date in dates):
        raise ValueError(f"Indicator dataset {dataset['id']} contains a non-ISO date")
    if any(row.get("value") is not None and not isinstance(row.get("value"), (int, float)) for row in dataset["observations"]):
        raise ValueError(f"Indicator dataset {dataset['id']} contains a non-numeric value")
    checks = dataset["evidenceChecks"]
    if not isinstance(checks, list) or any(
        not check.get("label")
        or check.get("status") not in {"confirms", "conflicts", "unclear"}
        or not check.get("explanation")
        for check in checks
    ):
        raise ValueError(f"Indicator dataset {dataset['id']} has invalid evidence checks")
    ranges = dataset["referenceRanges"]
    ordered = [ranges.get(key) for key in ("minimum", "p10", "p25", "historicalMedian", "p75", "p90", "maximum")]
    available = [value for value in ordered if value is not None]
    if available != sorted(available):
        raise ValueError(f"Indicator dataset {dataset['id']} has invalid historical ranges")


def write_website_chart_data(
    root: Path,
    rows: list[Row],
    lag_rows: list[Row],
    rolling_rows: list[Row],
    equity_lag_rows: list[Row],
    energy_rows: list[Row],
    system_rows: list[Row],
    current_state_rows: list[Row],
    indicator_catalogue_rows: list[Row],
    output_quality_rows: list[Row],
    output_quality_correlations: list[Row],
) -> list[str]:
    out_dir = root / "website" / "public" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_out_dir = out_dir / "charts"
    indicator_out_dir = out_dir / "indicators"
    chart_out_dir.mkdir(exist_ok=True)
    indicator_out_dir.mkdir(exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    regimes = _regimes()
    events = _events()
    locked_performance = next((row for row in rolling_rows if row.get("target") == "WTI_YoY" and row.get("model") == "gm2_only" and row.get("lag_months") == 5 and row.get("window_months") == 60 and row.get("sample") == "all"), {})

    oil_prices = _dataset(
        "oil-price-layers", "Oil price layers", "Benchmark, realised refiner cost, and investor-accessible oil exposure.", "monthly",
        [
            _series("WTI", "WTI", "USD per barrel", "FRED DCOILWTICO", "measured", color="#0f766e", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("Brent", "Brent", "USD per barrel", "FRED DCOILBRENTEU", "measured", color="#2563eb", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("RAC_composite", "RAC composite", "USD per barrel", "EIA R0000____3", "measured", color="#7c3aed", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("USO", "USO adjusted close", "USD per share", "Yahoo-compatible chart data", "measured", color="#d97706", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("first_purchase_price", "Domestic first purchase", "USD per barrel", "EIA Petroleum Marketing Monthly", "measured", False, color="#be123c", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("imported_landed_cost", "Imported landed cost", "USD per barrel", "EIA Petroleum Marketing Monthly", "measured", False, color="#475569", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("real_WTI", "Real WTI", "CPI-base USD per barrel", "FRED WTI / CPIAUCSL", "derived", False, color="#15803d", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("real_Brent", "Real Brent", "CPI-base USD per barrel", "FRED Brent / CPIAUCSL", "derived", False, color="#1d4ed8", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
        ],
        _observations(rows, {"WTI": "WTI", "Brent": "Brent", "RAC_composite": "RAC_composite", "USO": "USO_month_end_adjusted_close", "first_purchase_price": "first_purchase_price", "imported_landed_cost": "imported_landed_cost", "real_WTI": "real_WTI", "real_Brent": "real_Brent"}),
        ["raw", "indexed", "yoy", "zscore", "pct_change"], "Contextual indicator",
        {"formula": "Raw monthly values. Transformations are calculated in-browser within each series; indexed = 100 at first visible observation.", "notes": "USO is a share price and must not be read on a barrel-price axis in raw mode.", "sources": ["FRED", "EIA", "Yahoo-compatible public chart data"]},
        "final_oil_price_layers_time_series.png", generated_at, [event["id"] for event in events],
    )

    gm2_lead = _dataset(
        "gm2-oil-lead", "GM2 leading oil momentum", "Global liquidity growth aligned with later oil-price momentum.", "monthly",
        [
            _series("GM2_YoY", "G4 GM2 YoY", "percent", "Project G4 GM2 aggregate", "derived", color="#d97706"),
            _series("WTI_YoY", "WTI YoY", "percent", "FRED DCOILWTICO", "derived", color="#0f766e"),
            _series("Brent_YoY", "Brent YoY", "percent", "FRED DCOILBRENTEU", "derived", color="#2563eb"),
            _series("RAC_composite_YoY", "RAC composite YoY", "percent", "EIA R0000____3", "derived", color="#7c3aed"),
        ],
        _observations(rows, {"GM2_YoY": "GM2_YoY", "WTI_YoY": "WTI_YoY", "Brent_YoY": "Brent_YoY", "RAC_composite_YoY": "RAC_composite_YoY"}),
        ["raw", "zscore"], "Validated relationship",
        {"formula": "Oil_YoY[t] compared with GM2_YoY[t-lag]. Positive lag means GM2 leads oil.", "lockedLag": 5, "peakSimpleCorrelationLag": 4, "testedLags": [0, 18], "lockedPerformance": {"windowMonths": 60, "rmse": locked_performance.get("rolling_rmse"), "mae": locked_performance.get("rolling_mae"), "r2": locked_performance.get("rolling_r2"), "n": locked_performance.get("n_predictions")}, "notes": "The simple-correlation peak is descriptive; lag 5 remains locked from rolling validation."},
        "final_gm2_leads_oil_time_series.png", generated_at, [event["id"] for event in events],
    )

    wti_pred = rolling_predictions(rows, "WTI_YoY", [feature("GM2_YoY", 5, "GM2_YoY_lag")], 60)
    brent_pred = rolling_predictions(rows, "Brent_YoY", [feature("GM2_YoY", 5, "GM2_YoY_lag")], 60)
    wti_residual = {month: float(actual - pred) for month, actual, pred in zip(wti_pred.get("months", []), wti_pred.get("actuals", []), wti_pred.get("preds", []))}
    brent_residual = {month: float(actual - pred) for month, actual, pred in zip(brent_pred.get("months", []), brent_pred.get("actuals", []), brent_pred.get("preds", []))}
    residual_observations = [
        {"date": _iso_date(row["month"]), "WTI_residual": wti_residual.get(str(row["month"])), "Brent_residual": brent_residual.get(str(row["month"])), "CI_zscore": _number(row.get("CI_zscore")), "USO_tracking_residual": _number(row.get("USO_tracking_residual"))}
        for row in rows
    ]
    residuals = _dataset(
        "oil-residual-ci", "Oil residual and physical state", "Deviations from the locked liquidity-implied path alongside comparative inventory and USO tracking.", "monthly",
        [
            _series("WTI_residual", "WTI model residual", "YoY percentage points", "Project rolling GM2 lag-5 model", "modelled", color="#0f766e"),
            _series("Brent_residual", "Brent model residual", "YoY percentage points", "Project rolling GM2 lag-5 model", "modelled", False, color="#2563eb"),
            _series("CI_zscore", "Comparative inventory z-score", "standard deviations", "Derived from EIA WCESTUS1", "derived", color="#be123c"),
            _series("USO_tracking_residual", "USO minus WTI YoY", "percentage points", "Yahoo-compatible data and FRED WTI", "derived", False, color="#7c3aed"),
        ], residual_observations, ["raw", "zscore"], "Validated relationship",
        {"formula": "Oil residual = actual Oil_YoY - rolling fitted(alpha + beta*GM2_YoY[t-5]); CI uses only the prior five same-month inventory observations.", "windowMonths": 60, "notes": "Different units are shown in synchronized panels in raw mode and may share an axis only after standardization."},
        "final_oil_residual_ci_time_series.png", generated_at, ["gfc_2008", "shale_2014", "covid_2020", "reopening_2021"],
    )

    quarterly = sorted([dict(row) for row in energy_rows if row.get("section") == "time_series" and row.get("frequency") == "quarterly" and row.get("month")], key=lambda row: str(row["month"]))
    for row in quarterly:
        year, month = map(int, str(row["month"]).split("-"))
        quarter = (month - 1) // 3
        values = [_number(item.get("Industrial_production_YoY")) for item in system_rows if int(str(item["month"])[:4]) == year and (int(str(item["month"])[5:7]) - 1) // 3 == quarter]
        available = [item for item in values if item is not None]
        row["Industrial_production_YoY"] = sum(available) / len(available) if available else None
    energy_gdp = _dataset(
        "energy-gdp", "Energy throughput and real activity", "Quarterly growth in total energy, petroleum consumption, real GDP, and industrial production.", "quarterly",
        [
            _series("Energy_consumption_growth", "Total energy consumption growth", "percent", "EIA MER T01.03", "derived", frequency="quarterly", color="#0f766e"),
            _series("Oil_consumption_growth", "Petroleum consumption growth", "percent", "EIA MER T01.03", "derived", frequency="quarterly", color="#d97706"),
            _series("Real_GDP_growth", "Real GDP growth", "percent", "FRED GDPC1", "derived", frequency="quarterly", color="#2563eb"),
            _series("Industrial_production_YoY", "Industrial production growth", "percent", "FRED INDPRO", "derived", frequency="quarterly", color="#7c3aed"),
        ],
        _observations(quarterly, {"Energy_consumption_growth": "Energy_consumption_growth", "Oil_consumption_growth": "Oil_consumption_growth", "Real_GDP_growth": "Real_GDP_growth", "Industrial_production_YoY": "Industrial_production_YoY"}),
        ["raw", "zscore"], "Supported historical pattern",
        {"formula": "Quarterly growth observations aligned to quarter dates.", "notes": "Monthly energy and industrial series are aggregated to quarter; GDP remains at its native quarterly frequency. No monthly interpolation is used."},
        "final_energy_gdp_time_series.png", generated_at, [event["id"] for event in events],
    )

    equities = _dataset(
        "oil-equities", "Oil and S&P 500", "Monthly return and year-over-year macro-cycle comparisons.", "monthly",
        [
            _series("SP500_return", "S&P 500 monthly return", "log percent", "FRED SP500", "derived", color="#475569"),
            _series("WTI_return", "WTI monthly return", "log percent", "FRED DCOILWTICO", "derived", color="#0f766e"),
            _series("Brent_return", "Brent monthly return", "log percent", "FRED DCOILBRENTEU", "derived", False, color="#2563eb"),
            _series("SP500_YoY", "S&P 500 YoY", "percent", "FRED SP500", "derived", False, color="#475569"),
            _series("WTI_YoY", "WTI YoY", "percent", "FRED DCOILWTICO", "derived", False, color="#0f766e"),
            _series("Brent_YoY", "Brent YoY", "percent", "FRED DCOILBRENTEU", "derived", False, color="#2563eb"),
        ],
        _observations(rows, {"SP500_return": "SP500_log_return_1m", "WTI_return": "WTI_log_return_1m", "Brent_return": "Brent_log_return_1m", "SP500_YoY": "SP500_YoY", "WTI_YoY": "WTI_YoY", "Brent_YoY": "Brent_YoY"}),
        ["raw", "zscore"], "Contextual indicator",
        {"formula": "Monthly log return = 100*ln(P[t]/P[t-1]); YoY = 100*(P[t]/P[t-12]-1).", "notes": "YoY lag patterns describe macro stress; monthly returns are more relevant to timing and remain mostly contemporaneous."},
        "sp500_vs_wti_yoy.png", generated_at, [event["id"] for event in events],
    )

    uso = _dataset(
        "uso-tracking", "USO and benchmark oil", "Tradable ETF exposure compared with WTI and Brent benchmarks.", "monthly",
        [
            _series("USO", "USO adjusted close", "USD per share", "Yahoo-compatible chart data", "measured", color="#d97706", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("WTI", "WTI", "USD per barrel", "FRED DCOILWTICO", "measured", color="#0f766e", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("Brent", "Brent", "USD per barrel", "FRED DCOILBRENTEU", "measured", color="#2563eb", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("USO_tracking_residual", "USO minus WTI YoY", "percentage points", "Project derived", "derived", False, color="#7c3aed"),
            _series("CI_zscore", "Comparative inventory z-score", "standard deviations", "Derived from EIA WCESTUS1", "derived", False, color="#be123c"),
        ],
        _observations(rows, {"USO": "USO_month_end_adjusted_close", "WTI": "WTI", "Brent": "Brent", "USO_tracking_residual": "USO_tracking_residual", "CI_zscore": "CI_zscore"}),
        ["raw", "indexed", "yoy", "zscore", "pct_change"], "Contextual indicator",
        {"formula": "USO tracking residual = USO_YoY - WTI_YoY.", "notes": "USO can diverge through roll yield, fees, tracking differences, and ETF structure. Raw USO and barrel prices are not placed on one axis."},
        "uso_vs_wti_yoy.png", generated_at, ["gfc_2008", "shale_2014", "covid_2020", "reopening_2021"],
    )

    headline_keys = ["GDPC1", "A939RX0Q048SBEA", "A261RX1Q020SBEA", "LB0000031Q020SBEA"]
    headline = _dataset(
        "output-quality-headline", "Headline measured output", "Real GDP, GDP per capita, gross domestic income, and final private domestic sales measure related but distinct parts of recorded production and income.", "quarterly",
        [
            _series("GDPC1", "Real GDP", "billions chained 2017 USD", "BEA via FRED GDPC1", "measured", color="#0f766e"),
            _series("A939RX0Q048SBEA", "Real GDP per capita", "chained 2017 USD per person", "BEA via FRED", "measured", color="#2563eb"),
            _series("A261RX1Q020SBEA", "Real gross domestic income", "billions chained 2017 USD", "BEA via FRED", "measured", False, color="#7c3aed"),
            _series("LB0000031Q020SBEA", "Real final private domestic sales", "billions chained 2017 USD", "BEA via FRED", "measured", False, color="#d97706"),
        ], _quality_observations(output_quality_rows, headline_keys), ["raw", "indexed", "zscore"], "Contextual indicator",
        {"formula": "Official inflation-adjusted BEA aggregates at quarterly frequency.", "notes": "GDP measures production rather than total wealth; per-capita and income measures answer different distributional and accounting questions."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-10-01"),
    )
    net_output_keys = ["real_gdp_annual", "A362RX1A020NBEA", "real_ndp_per_capita"]
    net_output = _dataset(
        "output-quality-net-output", "Gross and net output", "Official real net domestic product accounts for capital consumption; per-capita net output asks how much net production remains per resident.", "annual",
        [
            _series("real_gdp_annual", "Real GDP", "billions chained 2017 USD", "BEA GDPC1 annual average", "derived", color="#0f766e"),
            _series("A362RX1A020NBEA", "Official real NDP", "billions chained 2017 USD", "BEA via FRED A362RX1A020NBEA", "measured", color="#2563eb"),
            _series("real_ndp_per_capita", "Real NDP per capita", "chained 2017 USD per person", "BEA / Census project derivation", "derived", color="#d97706"),
        ], _quality_observations(output_quality_rows, net_output_keys), ["raw", "indexed", "zscore"], "Contextual indicator",
        {"formula": "Real NDP is the official BEA chained-dollar series; NDP per capita = real NDP / population.", "notes": "The project does not subtract chained-dollar GDP components because chained measures are not exactly additive."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-01-01"),
    )
    capacity_keys = ["W171RC1Q027SBEA", "A262RX1Q020SBEA", "INDPRO", "IPMAN", "TSIFRGHT"]
    capacity = _dataset(
        "output-quality-capacity", "Productive capacity and net investment", "Net investment, capital consumption, industrial production, manufacturing, and freight provide different views of productive capacity and material throughput.", "quarterly",
        [
            _series("W171RC1Q027SBEA", "Net domestic investment", "billions USD SAAR", "BEA via FRED", "measured", color="#d97706"),
            _series("A262RX1Q020SBEA", "Real capital consumption", "billions chained 2017 USD SAAR", "BEA via FRED", "measured", color="#be123c"),
            _series("INDPRO", "Industrial production", "index", "Federal Reserve via FRED", "measured", color="#0f766e"),
            _series("IPMAN", "Manufacturing output", "index", "Federal Reserve via FRED", "measured", False, color="#2563eb"),
            _series("TSIFRGHT", "Freight activity", "index", "BTS via FRED", "measured", False, color="#7c3aed"),
        ], _quality_observations(output_quality_rows, capacity_keys), ["raw", "indexed", "zscore"], "Supported historical pattern",
        {"formula": "Official investment and output series; monthly physical-output indexes are averaged within genuine quarters.", "notes": "Net investment is nominal while capital consumption is real, so raw mode separates units."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-10-01"),
    )
    household_keys = ["MEHOINUSA672N", "HouseholdCommand", "CXUSHELTERLB0101M", "CXUFOODTOTLLB0101M", "CXUUTILSLB0101M"]
    household = _dataset(
        "output-quality-household", "Household prosperity and essential costs", "The experimental household-command measure subtracts shelter, food, and utilities/fuels costs from real median household income while keeping every component visible.", "annual",
        [
            _series("MEHOINUSA672N", "Real median household income", "2024 USD", "Census via FRED", "measured", color="#0f766e"),
            _series("HouseholdCommand", "Experimental household command", "2024 USD", "Census/BLS project derivation", "experimental", color="#2563eb"),
            _series("CXUSHELTERLB0101M", "Shelter expenditure", "2024 USD per consumer unit", "BLS CE via FRED", "derived", False, color="#d97706"),
            _series("CXUFOODTOTLLB0101M", "Food expenditure", "2024 USD per consumer unit", "BLS CE via FRED", "derived", False, color="#7c3aed"),
            _series("CXUUTILSLB0101M", "Utilities, fuels, public services", "2024 USD per consumer unit", "BLS CE via FRED", "derived", False, color="#be123c"),
        ], _quality_observations(output_quality_rows, household_keys), ["raw", "indexed", "zscore"], "Experimental proxy",
        {"formula": "HouseholdCommand = real median household income - real shelter - real food - real utilities/fuels/public-services expenditure.", "notes": "This combines median income with average consumer-unit costs and is not an official disposable-income statistic."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-01-01"),
    )
    financial_keys = ["VAPGDPFI", "VAPGDPRL", "TDSP", "private_debt_gdp", "DDDM01USA156NWDB"]
    financial = _dataset(
        "output-quality-financial", "Financialization and asset valuation", "Finance, insurance, real estate, debt service, leverage, and equity valuation are shown separately rather than collapsed into a judgmental score.", "quarterly",
        [
            _series("VAPGDPFI", "Finance and insurance value-added", "percent of GDP", "BEA via FRED", "measured", color="#0f766e"),
            _series("VAPGDPRL", "Real estate and rental value-added", "percent of GDP", "BEA via FRED", "measured", color="#2563eb"),
            _series("TDSP", "Household debt-service burden", "percent of disposable income", "Federal Reserve via FRED", "measured", color="#d97706"),
            _series("private_debt_gdp", "Household debt", "percent of GDP", "Federal Reserve / BEA project derivation", "derived", False, color="#be123c"),
            _series("DDDM01USA156NWDB", "Equity-market capitalization", "percent of GDP", "World Bank via FRED", "measured", False, frequency="annual", color="#7c3aed"),
        ], _quality_observations(output_quality_rows, financial_keys), ["raw", "indexed", "zscore"], "Contextual indicator",
        {"formula": "Value-added and balance-sheet measures retain their official definitions; household debt/GDP = CMDEBT / nominal GDP * 100.", "notes": "A larger financial or real-estate share is not, by itself, evidence of low-quality output."}, "", generated_at, [event["id"] for event in events], reference_period=("2005-01-01", "2019-10-01"),
    )
    output_comparison_keys = ["A939RX0Q048SBEA", "INDPRO", "MEHOINUSA672N"]
    output_comparison = _dataset(
        "output-quality-comparison", "Output, production, and household income", "Real GDP per capita, industrial production, and real median household income can follow different paths even when headline output grows.", "quarterly",
        [
            _series("A939RX0Q048SBEA", "Real GDP per capita", "chained 2017 USD per person", "BEA via FRED", "measured", color="#0f766e"),
            _series("INDPRO", "Industrial production", "index", "Federal Reserve via FRED", "measured", color="#2563eb"),
            _series("MEHOINUSA672N", "Real median household income", "2024 USD", "Census via FRED", "measured", color="#d97706", frequency="annual"),
        ], _quality_observations(output_quality_rows, output_comparison_keys), ["raw", "indexed", "zscore"], "Contextual indicator",
        {"formula": "Official real GDP per capita, industrial-production index, and annual real median household income; no monthly or quarterly interpolation is applied to annual income.", "notes": "The measures differ in concept, population adjustment, frequency, and revisions. Indexed paths compare relative growth rather than levels."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-10-01"),
    )

    physical_tightness = _dataset(
        "physical-tightness", "Physical energy conditions", "Inventory, supply, consumption, and refinery utilization provide distinct evidence about physical oil-market tightness.", "monthly",
        [
            _series("CI_zscore", "Comparative inventory", "standard deviations", "EIA WCESTUS1, project derivation", "derived", color="#be123c"),
            _series("petroleum_production_YoY", "Petroleum production growth", "percent", "EIA Monthly Energy Review", "derived", color="#0f766e"),
            _series("petroleum_consumption_YoY", "Petroleum consumption growth", "percent", "EIA Monthly Energy Review", "derived", color="#d97706"),
            _series("refinery_utilization_pct", "Refinery utilization", "percent", "EIA WPULEUS3", "measured", False, color="#2563eb"),
        ],
        _observations(system_rows, {"CI_zscore": "CI_zscore", "petroleum_production_YoY": "petroleum_production_YoY", "petroleum_consumption_YoY": "petroleum_consumption_YoY", "refinery_utilization_pct": "refinery_utilization_pct"}),
        ["raw", "zscore"], "Contextual indicator",
        {"formula": "CI_zscore uses the prior five-year same-month inventory history; growth rates are year-over-year; refinery utilization is the published rate.", "notes": "No single physical indicator defines tightness. Demand weakness can raise inventories even when supply is constrained."},
        "physical_tightness_dashboard.png", generated_at, [event["id"] for event in events], reference_period=("2000-01-01", "2019-12-01"),
    )
    energy_burden = _dataset(
        "energy-burden", "Energy affordability", "Real oil-price momentum and energy costs relative to household income and GDP show whether energy is becoming harder to afford.", "monthly",
        [
            _series("real_WTI_YoY", "Real WTI growth", "percent", "FRED WTI and CPI", "derived", color="#be123c"),
            _series("household_energy_expenditure_share", "Household energy expenditure share", "percent", "BEA via FRED", "derived", color="#d97706"),
            _series("energy_expenditure_share_gdp", "Energy expenditure share of GDP", "percent", "BEA via FRED", "derived", color="#7c3aed"),
            _series("energy_CPI_YoY", "Energy CPI growth", "percent", "BLS via FRED", "derived", False, color="#2563eb"),
            _series("real_disposable_income_YoY", "Real disposable income growth", "percent", "BEA via FRED", "derived", False, color="#0f766e"),
        ],
        _observations(system_rows, {"real_WTI_YoY": "real_WTI_YoY", "household_energy_expenditure_share": "household_energy_expenditure_share", "energy_expenditure_share_gdp": "energy_expenditure_share_gdp", "energy_CPI_YoY": "energy_CPI_YoY", "real_disposable_income_YoY": "real_disposable_income_YoY"}),
        ["raw", "zscore"], "Experimental proxy",
        {"formula": "Burden shares divide energy expenditure by household disposable income or nominal GDP; price and income series use year-over-year change.", "notes": "Aggregate burden can hide household distribution, regional prices, substitution, and policy support."},
        "energy_burden_dashboard.png", generated_at, [event["id"] for event in events], reference_period=("2000-01-01", "2019-12-01"),
    )
    industrial_transmission = _dataset(
        "industrial-transmission", "Energy stress and real activity", "Energy affordability is shown beside production, manufacturing, spending, investment, and GDP growth to inspect transmission rather than assume it.", "monthly",
        [
            _series("energy_expenditure_share_gdp", "Energy expenditure share of GDP", "percent", "BEA via FRED", "derived", color="#be123c"),
            _series("Industrial_production_YoY", "Industrial production growth", "percent", "Federal Reserve via FRED", "derived", color="#0f766e"),
            _series("manufacturing_output_YoY", "Manufacturing output growth", "percent", "Federal Reserve via FRED", "derived", color="#2563eb"),
            _series("real_consumer_spending_YoY", "Real consumer spending growth", "percent", "BEA via FRED", "derived", False, color="#d97706"),
            _series("business_investment_YoY", "Business investment growth", "percent", "BEA via FRED", "derived", False, color="#7c3aed"),
            _series("Real_GDP_growth", "Real GDP growth", "percent", "BEA via FRED", "derived", False, color="#475569"),
        ],
        _observations(system_rows, {"energy_expenditure_share_gdp": "energy_expenditure_share_gdp", "Industrial_production_YoY": "Industrial_production_YoY", "manufacturing_output_YoY": "manufacturing_output_YoY", "real_consumer_spending_YoY": "real_consumer_spending_YoY", "business_investment_YoY": "business_investment_YoY", "Real_GDP_growth": "Real_GDP_growth"}),
        ["raw", "zscore"], "Supported historical pattern",
        {"formula": "Growth rates are year-over-year; energy burden is the expenditure share of nominal GDP.", "notes": "Common recessions, monetary policy, credit, productivity, and supply shocks can drive several series together."},
        "industrial_transmission.png", generated_at, [event["id"] for event in events], reference_period=("2000-01-01", "2019-12-01"),
    )
    labour_warning = _dataset(
        "labour-warning", "Labour and household early warnings", "Hours, temporary-help employment, real wages, unemployment, sentiment, and delinquency show different stages of labour and household strain.", "monthly",
        [
            _series("average_weekly_hours_YoY", "Average weekly hours growth", "percent", "BLS via FRED", "derived", color="#0f766e"),
            _series("temporary_help_YoY", "Temporary-help employment growth", "percent", "BLS via FRED", "derived", color="#2563eb"),
            _series("real_wage_growth", "Real wage growth", "percent", "BLS via FRED", "derived", color="#d97706"),
            _series("unemployment_rate", "Unemployment rate", "percent", "BLS via FRED", "measured", color="#be123c"),
            _series("consumer_sentiment", "Consumer sentiment", "index", "University of Michigan via FRED", "measured", False, color="#7c3aed"),
            _series("credit_card_delinquency_rate", "Credit-card delinquency", "percent", "Federal Reserve via FRED", "measured", False, color="#475569"),
        ],
        _observations(system_rows, {"average_weekly_hours_YoY": "average_weekly_hours_YoY", "temporary_help_YoY": "temporary_help_YoY", "real_wage_growth": "real_wage_growth", "unemployment_rate": "unemployment_rate", "consumer_sentiment": "consumer_sentiment", "credit_card_delinquency_rate": "credit_card_delinquency_rate"}),
        ["raw", "zscore"], "Supported historical pattern",
        {"formula": "Hours, temporary help, and real wages use year-over-year change; unemployment, sentiment, and delinquency retain published levels.", "notes": "Labour indicators have different publication lags and can respond to policy, demographics, sector mix, and non-energy shocks."},
        "labour_early_warning_indicators.png", generated_at, [event["id"] for event in events], reference_period=("2000-01-01", "2019-12-01"),
    )
    demand_destruction = _dataset(
        "demand-destruction", "Demand destruction sequence", "Oil prices can fall while activity, petroleum demand, and employment conditions worsen when falling demand drives the decline.", "monthly",
        [
            _series("WTI_YoY", "WTI growth", "percent", "FRED DCOILWTICO", "derived", color="#be123c"),
            _series("petroleum_consumption_YoY", "Petroleum consumption growth", "percent", "EIA Monthly Energy Review", "derived", color="#d97706"),
            _series("Industrial_production_YoY", "Industrial production growth", "percent", "Federal Reserve via FRED", "derived", color="#0f766e"),
            _series("unemployment_rate", "Unemployment rate", "percent", "BLS via FRED", "measured", color="#475569"),
        ],
        _observations(system_rows, {"WTI_YoY": "WTI_YoY", "petroleum_consumption_YoY": "petroleum_consumption_YoY", "Industrial_production_YoY": "Industrial_production_YoY", "unemployment_rate": "unemployment_rate"}),
        ["raw", "zscore"], "Supported historical pattern",
        {"formula": "WTI, petroleum consumption, and industrial production use year-over-year change; unemployment is a published level.", "notes": "A falling oil price can also reflect supply growth, efficiency, currency moves, or policy rather than demand destruction."},
        "demand_destruction_cycle.png", generated_at, [event["id"] for event in events], reference_period=("2000-01-01", "2019-12-01"),
    )

    datasets = [oil_prices, gm2_lead, residuals, energy_gdp, equities, uso, headline, net_output, capacity, household, financial, output_comparison, physical_tightness, energy_burden, industrial_transmission, labour_warning, demand_destruction]
    files: list[str] = []
    for dataset in datasets:
        filename = f"{dataset['id']}.json"
        payload = json.dumps(dataset, indent=2, allow_nan=False) + "\n"
        (out_dir / filename).write_text(payload, encoding="utf-8")
        (chart_out_dir / filename).write_text(payload, encoding="utf-8")
        files.append(filename)

    catalogue_by_indicator = {str(row.get("indicator")): row for row in indicator_catalogue_rows}
    indicator_payloads = [
        _indicator_payload(row, catalogue_by_indicator.get(str(row.get("indicator"))), system_rows, generated_at)
        for row in current_state_rows
    ]
    _attach_evidence_checks(indicator_payloads)
    current_state_snapshot = _current_state_snapshot(indicator_payloads, generated_at)
    anomaly_order = {field: index for index, field in enumerate(current_state_snapshot["indicatorOrder"])}

    def sort_indicator_fields(fields: list[str]) -> list[str]:
        return sorted(fields, key=lambda field: anomaly_order.get(field, len(anomaly_order)))
    for payload in indicator_payloads:
        validate_indicator_dataset(payload)
        filename = f"{payload['id']}.json"
        (indicator_out_dir / filename).write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        files.append(f"indicators/{filename}")

    lag_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "gm2Oil": [{"target": row.get("target"), "lag": row.get("lag_months"), "correlation": row.get("correlation"), "n": row.get("n")} for row in lag_rows],
        "oilEquityReturns": [{"sample": row.get("sample"), "metric": row.get("metric"), "oilMetric": row.get("oil_metric"), "lag": row.get("lag_periods"), "correlation": row.get("correlation"), "n": row.get("n_obs")} for row in equity_lag_rows],
        "conventions": {"gm2Oil": "positive lag means GM2 leads oil", "oilEquity": "positive lag means stocks lead oil; negative lag means oil leads stocks"},
        "details": {
            "gm2": {"plainLanguageSummary": "This chart compares simple GM2-oil correlations across candidate lead times; the locked five-month model comes from rolling validation, not from choosing the tallest correlation point.", "description": "Lag correlation between GM2 YoY and later WTI or Brent YoY.", "howToRead": "Positive lags mean GM2 is observed before oil. Compare the four-month descriptive peak with the five-month locked benchmark marker.", "calculation": {"formula": "corr(GM2_YoY[t-lag], Oil_YoY[t])", "explanation": "Each point uses the common observations available at that lag.", "example": "Lag 5 compares GM2 in January with oil YoY in June."}, "patternsToWatch": ["A broad correlation plateau rather than a single isolated peak", "Differences between WTI and Brent"], "limitations": ["Overlapping YoY changes are autocorrelated; correlation is not out-of-sample performance or causation."], "sourceNotes": ["Project G4 GM2 aggregate; FRED WTI and Brent"], "transformation": {"type": "yoy", "referenceStart": None, "referenceEnd": None, "mean": None, "standardDeviation": None}},
            "equity": {"plainLanguageSummary": "Monthly-return lag correlations are a market-timing robustness check; the relationship is mostly contemporaneous and does not support a general oil-led equity timing rule.", "description": "Lag correlation between monthly S&P 500 and oil log returns.", "howToRead": "Positive lags mean stocks lead oil; negative lags mean oil leads stocks; zero is contemporaneous.", "calculation": {"formula": "corr(SP500_return[t-lag], Oil_return[t])", "explanation": "Returns use non-overlapping one-month log changes.", "example": "Lag -1 asks whether this month's oil return aligns with next month's equity return."}, "patternsToWatch": ["Whether correlations away from zero remain meaningful", "Agreement between WTI and Brent"], "limitations": ["Return correlations can vary by shock regime and do not establish a tradable or causal rule."], "sourceNotes": ["FRED SP500, DCOILWTICO, and DCOILBRENTEU"], "transformation": {"type": "raw", "referenceStart": None, "referenceEnd": None, "mean": None, "standardDeviation": None}},
        },
    }
    correlation_details = {
        "plainLanguageSummary": "This comparison asks whether energy-consumption growth moves more closely with productive and household measures than with broader financial or headline aggregates.",
        "description": "Contemporaneous correlations between total energy-consumption growth and each economic measure's growth rate.",
        "howToRead": "Bars farther from zero indicate stronger co-movement, not greater economic value or causal importance. Inspect coverage and out-of-sample columns before treating a relationship as stable.",
        "calculation": {"formula": "correlation = corr(Energy_growth[t], Economic_measure_growth[t])", "explanation": "Quarterly series use year-over-year growth and genuine common quarter dates. Separate table fields report lags, rolling stability, distributed lags, recession splits, and expanding out-of-sample errors.", "example": "A correlation of 0.60 means the two growth rates tended to move together in the covered sample; it does not mean energy caused 60% of the outcome."},
        "patternsToWatch": ["Whether material-output measures cluster above financial valuation measures", "Whether a full-sample relationship weakens in rolling or out-of-sample tests"],
        "limitations": ["Latest-vintage bivariate correlations are exposed to revisions, common business-cycle drivers, and differing date coverage.", "Correlation, predictive improvement, and causal interpretation are separate claims."],
        "sourceNotes": ["EIA Monthly Energy Review total energy consumption", "BEA, BLS, Federal Reserve, BTS, Census, and World Bank series distributed through FRED"],
        "transformation": {"type": "yoy", "referenceStart": None, "referenceEnd": None, "mean": None, "standardDeviation": None},
    }
    recession_periods = _recession_periods(system_rows)
    rolling_performance = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "title": "Rolling oil-model performance",
        "evidenceLabel": "Validated relationship",
        "rows": [
            {"target": row.get("target"), "model": row.get("model"), "lagMonths": row.get("lag_months"), "windowMonths": row.get("window_months"), "sample": row.get("sample"), "n": row.get("n_predictions"), "rmse": row.get("rolling_rmse"), "mae": row.get("rolling_mae"), "r2": row.get("rolling_r2"), "directionalAccuracy": row.get("directional_accuracy"), "signAccuracy": row.get("sign_accuracy")}
            for row in rolling_rows
            if row.get("target") == "WTI_YoY" and row.get("sample") == "all" and row.get("window_months") in {60, 84, 120} and row.get("lag_months") == 5
        ],
    }
    shared = {"lag-results.json": lag_payload, "rolling-performance.json": rolling_performance, "regimes.json": {"schemaVersion": SCHEMA_VERSION, "regimes": regimes, "recessions": recession_periods}, "recessions.json": {"schemaVersion": 1, "recessions": recession_periods}, "events.json": {"schemaVersion": SCHEMA_VERSION, "events": events}, "output-quality-correlations.json": {"schemaVersion": SCHEMA_VERSION, "generatedAt": generated_at, "evidenceLabel": "Experimental proxy", "details": correlation_details, "rows": output_quality_correlations}}
    cross_mapping = {"GM2_YoY": "GM2_YoY", "WTI_YoY": "WTI_YoY", "CI_zscore": "CI_zscore", "household_energy_burden": "household_energy_expenditure_share", "industrial_production": "Industrial_production_YoY", "weekly_hours": "average_weekly_hours_YoY", "temporary_help": "temporary_help_YoY"}
    shared["cross-layer.json"] = {"schemaVersion": SCHEMA_VERSION, "frequency": "monthly", "fields": cross_mapping, "observations": _observations(system_rows, cross_mapping)}
    for filename, payload in shared.items():
        (out_dir / filename).write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        files.append(filename)

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "indicatorSchemaVersion": 1,
        "generatedAt": generated_at,
        "currentState": current_state_snapshot,
        "datasets": [{"id": item["id"], "file": f"charts/{item['id']}.json", "legacyFile": f"{item['id']}.json", "title": item["title"], "frequency": item["frequency"], "dateRange": item["dateRange"], "evidenceLabel": item["evidenceLabel"]} for item in datasets],
        "indicators": [{"id": item["id"], "file": f"indicators/{item['id']}.json", "label": item["label"], "layer": item["layer"], "latestDate": item["latest"]["date"], "evidenceLabel": item["evidenceLabel"]} for item in indicator_payloads],
        "layers": [
            {"id": "liquidity-financial", "label": "Liquidity and financial conditions", "indicatorFields": sort_indicator_fields(["GM2_YoY", "fed_funds_rate", "credit_tightening_pct", "credit_card_delinquency_rate"]), "interpretation": "Liquidity support is mixed with the cost and availability of credit; higher GM2 does not automatically mean lower stress.", "confidence": "Moderate"},
            {"id": "physical-energy", "label": "Physical energy conditions", "indicatorFields": sort_indicator_fields(["petroleum_production_YoY", "petroleum_consumption_YoY", "oil_consumption_per_person_mmbtu", "CI_zscore", "refinery_utilization_pct"]), "interpretation": "Supply, demand, inventories, and refinery utilization must confirm one another before physical tightness is inferred.", "confidence": "Moderate"},
            {"id": "energy-affordability", "label": "Energy affordability", "indicatorFields": sort_indicator_fields(["real_WTI_YoY", "household_energy_expenditure_share", "energy_expenditure_share_gdp", "energy_CPI_YoY", "real_disposable_income_YoY"]), "interpretation": "Energy stress depends on costs relative to real household income and economic capacity, not on nominal oil alone.", "confidence": "Moderate"},
            {"id": "production-activity", "label": "Production and economic activity", "indicatorFields": sort_indicator_fields(["Industrial_production_YoY", "manufacturing_output_YoY", "real_consumer_spending_YoY", "business_investment_YoY", "Real_GDP_growth"]), "interpretation": "Production, spending, investment, and GDP indicate whether energy and financial conditions are transmitting into measured activity.", "confidence": "Moderate"},
            {"id": "labour-households", "label": "Labour and household conditions", "indicatorFields": sort_indicator_fields(["average_weekly_hours_YoY", "temporary_help_YoY", "full_time_employment_share", "involuntary_part_time_share", "prime_age_employment_rate", "real_wage_growth", "consumer_sentiment", "unemployment_rate"]), "interpretation": "Hours, job composition, wages, sentiment, and unemployment often move at different stages of household stress.", "confidence": "Moderate"},
        ],
        "shared": ["lag-results.json", "rolling-performance.json", "regimes.json", "recessions.json", "events.json", "cross-layer.json", "output-quality-correlations.json"],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    files.append("manifest.json")
    return files
