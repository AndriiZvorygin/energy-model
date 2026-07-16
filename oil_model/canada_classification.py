from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .classification import (
    IndicatorEngine,
    _month_date,
    _month_index,
    _percentile,
    _required_fields,
    _shift_months,
    classify_regimes,
    evaluate_symptom,
)
from .storage import Row, write_csv


CANADIAN_SCOPE = "Canadian energy-economic conditions with global oil-market and global-liquidity inputs."
STATUS_LABELS = {
    "active": "Active",
    "emerging": "Emerging",
    "fading": "Fading",
    "inactive": "Inactive",
    "insufficient_data": "Insufficient data",
}

EPISODES = [
    ("1979-1982 energy, inflation and interest-rate shock", "1979-01", "1982-12", "Oil and inflation shock followed by restrictive monetary conditions.", "Global supply shocks, domestic anti-inflation policy, and structural changes occurred together."),
    ("1981-1982 Canadian recession", "1981-07", "1982-10", "Restrictive rates and weakening demand coincided with recession.", "The U.S. recession, domestic monetary tightening, and sector restructuring also mattered."),
    ("1990-1992 recession and housing stress", "1990-03", "1992-12", "Housing, rates, and weak domestic demand transmitted into output and labour.", "Tax changes, U.S. weakness, and regional housing conditions complicate attribution."),
    ("2007-2009 oil spike and financial crisis", "2007-01", "2009-06", "Oil and affordability pressure preceded financial crisis and demand collapse.", "The global credit crisis dominates causal interpretation after 2008."),
    ("2014-2016 oil-price collapse", "2014-06", "2016-06", "Oil prices and resource investment fell while regional effects diverged.", "Global supply growth, exchange rates, and non-energy domestic demand also shaped outcomes."),
    ("2020 pandemic collapse", "2020-02", "2020-12", "Mobility and demand stopped abruptly before policy-supported recovery.", "Public-health restrictions were an exceptional exogenous shock."),
    ("2021-2023 reopening, inflation and rate increases", "2021-01", "2023-12", "Reopening demand, energy inflation, and rate increases overlapped.", "Supply chains, fiscal support, housing, and geopolitical shocks were material alternatives."),
    ("2003-2005 ordinary expansion control", "2003-01", "2005-12", "Non-event expansion control period.", "Ordinary periods still contain sector and regional variation."),
    ("2017-2019 ordinary late-cycle control", "2017-01", "2019-12", "Non-event late-cycle control period.", "The 2018 oil-price decline affected producing regions without a broad recession."),
]

EPISODE_FIELDS = [
    ("global_oil_conditions", "global_wti_yoy"),
    ("canadian_dollar", "cad_per_usd"),
    ("energy_cpi", "canada_energy_cpi_yoy"),
    ("bank_of_canada_policy_rate", "canada_policy_rate"),
    ("canadian_gdp", "canada_real_gdp_growth"),
    ("manufacturing_gdp", "canada_manufacturing_gdp_growth"),
    ("resource_sector_gdp", "canada_mining_oil_gas_gdp_growth"),
    ("unemployment", "canada_unemployment_rate"),
    ("employment", "canada_employment_rate"),
    ("ontario_labour_conditions", "ontario_employment_rate"),
    ("alberta_production_conditions", "alberta_crude_production_growth"),
]


def load_canadian_rules(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config_root = root / "config"
    symptom_path = config_root / "canada_symptom_rules.yaml"
    regime_path = config_root / "canada_regime_rules.yaml"
    symptoms = json.loads(symptom_path.read_text(encoding="utf-8"))
    regimes = json.loads(regime_path.read_text(encoding="utf-8"))
    if symptoms.get("scope") != CANADIAN_SCOPE or regimes.get("scope") != CANADIAN_SCOPE:
        raise ValueError("Canadian classification rule scope must match the formal Canadian scope")
    return symptoms, regimes


def _decorate_condition(engine: IndicatorEngine, condition: dict[str, Any]) -> dict[str, Any]:
    indicator = engine.indicators.get(str(condition["indicator"]), {})
    return {
        **condition,
        "geography": indicator.get("geography"),
        "evidenceScope": _evidence_scope(str(indicator.get("geography", "")), str(indicator.get("inputType", ""))),
        "indicatorId": indicator.get("id"),
    }


def _evidence_scope(geography: str, input_type: str = "") -> str:
    if geography == "Global" or input_type == "external":
        return "Global upstream inputs"
    if geography == "Ontario":
        return "Ontario consumer and manufacturing conditions"
    if geography == "Alberta":
        return "Alberta producing-region conditions"
    return "Canadian national conditions"


def _regional_contribution(engine: IndicatorEngine, rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        decorated = _decorate_condition(engine, row)
        grouped.setdefault(str(decorated["evidenceScope"]), []).append(decorated)
    return {
        scope: {
            "available": sum(item["available"] for item in items),
            "supporting": [item for item in items if item["available"] and item["met"]],
            "conflicting": [item for item in items if item["available"] and not item["met"]],
            "missing": [item for item in items if not item["available"]],
        }
        for scope, items in grouped.items()
    }


def _evaluate_symptoms(
    engine: IndicatorEngine,
    symptom_config: dict[str, Any],
    date: str,
    step_months: int,
    threshold_key: str,
) -> list[dict[str, Any]]:
    thresholds = symptom_config["settings"]["thresholdSets"][threshold_key]
    output = []
    for rule in symptom_config["symptoms"]:
        result = evaluate_symptom(engine, rule, date, thresholds, step_months)
        if rule.get("forceInsufficientData"):
            result.update({"status": "insufficient_data", "score": 0.0, "confidence": "low"})
        elif rule.get("confidenceCap") == "moderate" and result["confidence"] == "high":
            result["confidence"] = "moderate"
        all_rows = [*result["requiredConditionResults"], *result["confirmingEvidence"], *result["conflictingEvidence"], *result["missingEvidence"]]
        result.update({
            "scope": CANADIAN_SCOPE,
            "date": date,
            "statusLabel": STATUS_LABELS[result["status"]],
            "regionalContribution": _regional_contribution(engine, all_rows),
            "limitations": [
                "Latest-vintage histories are used; this is not a real-time-vintage reconstruction.",
                *( ["Wages and actual hours are unavailable, so labour confidence is capped at moderate."] if rule.get("incomplete") else []),
                *( ["Disposable income, household expenditure burden, and insolvency evidence are unavailable."] if rule.get("forceInsufficientData") else []),
            ],
        })
        for key in ("requiredConditionResults", "confirmingEvidence", "conflictingEvidence", "missingEvidence"):
            result[key] = [_decorate_condition(engine, item) for item in result[key]]
        output.append(result)
    return output


def _classification(
    engine: IndicatorEngine,
    symptom_config: dict[str, Any],
    regime_config: dict[str, Any],
    date: str,
    step_months: int,
    threshold_key: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    symptoms = _evaluate_symptoms(engine, symptom_config, date, step_months, threshold_key)
    thresholds = symptom_config["settings"]["thresholdSets"][threshold_key]
    regimes = classify_regimes(engine, regime_config, symptoms, date, thresholds)
    if regimes["primaryRegime"]["coverage"] < float(regime_config["settings"]["minimumEvidenceCoverage"]):
        regimes["classification"] = "Insufficient evidence"
        regimes["confidence"] = "low"
    for regime in regimes["allRegimeScores"]:
        for key in ("indicatorEvidence", "supportingEvidence", "conflictingEvidence", "missingEvidence"):
            regime[key] = [_decorate_condition(engine, item) for item in regime[key]]
        regime["scope"] = CANADIAN_SCOPE
        regime["date"] = date
        regime["status"] = "candidate"
        regime["regionalContribution"] = _regional_contribution(engine, regime["indicatorEvidence"])
        regime["historicalAnalogues"] = _regime_analogues(regime["id"])
        regime["limitations"] = ["Provisional rule score using Canadian-series historical distributions and latest-vintage data."]
    ordered = regimes["allRegimeScores"]
    regimes["primaryRegime"] = ordered[0]
    regimes["secondaryRegime"] = ordered[1]
    return symptoms, regimes


def _regime_analogues(regime_id: str) -> list[str]:
    mapping = {
        "A": ["2003-2005 ordinary expansion control"],
        "B": ["2007-2009 oil spike and financial crisis"],
        "C": ["2021-2023 reopening, inflation and rate increases"],
        "D": ["1990-1992 recession and housing stress"],
        "E": ["2021-2023 reopening, inflation and rate increases"],
        "F": ["2014-2016 oil-price collapse"],
        "G": ["2020 pandemic collapse"],
        "H": ["2021-2023 reopening, inflation and rate increases"],
    }
    return mapping.get(regime_id, [])


def _point_condition(engine: IndicatorEngine, field: str, direction: str, group: str, date: str, thresholds: dict[str, float]) -> dict[str, Any]:
    return engine.condition({"indicator": field, "expectedDirection": direction, "transformation": "full_history_percentile", "group": group}, date, thresholds)


def _side_score(rows: list[dict[str, Any]]) -> tuple[float, float]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row["group"]), []).append(row)
    group_scores = []
    for items in groups.values():
        available = [item for item in items if item["available"]]
        if available:
            group_scores.append(max(float(item.get("weightedStrength", 0.0)) for item in available))
    coverage = sum(item["available"] for item in rows) / len(rows) if rows else 0.0
    return (sum(group_scores) / len(group_scores) if group_scores else 0.0), coverage


def regional_divergence(engine: IndicatorEngine, date: str, thresholds: dict[str, float]) -> dict[str, Any]:
    ontario_rules = [
        ("ontario_energy_cpi_yoy", "high", "consumer"),
        ("ontario_gasoline_cpi_yoy", "high", "consumer"),
        ("ontario_employment_rate", "low", "labour"),
        ("ontario_unemployment_rate", "high", "labour"),
        ("ontario_prime_age_employment_rate", "low", "labour"),
    ]
    alberta_expansion_rules = [
        ("alberta_crude_production_growth", "high", "producer"),
        ("canada_mining_oil_gas_gdp_growth", "high", "resource"),
        ("canada_crude_exports_growth", "high", "external"),
        ("global_wti_yoy", "high", "external"),
    ]
    alberta_contraction_rules = [(field, "low", group) for field, _, group in alberta_expansion_rules]
    ontario = [_decorate_condition(engine, _point_condition(engine, *rule, date, thresholds)) for rule in ontario_rules]
    alberta_expansion = [_decorate_condition(engine, _point_condition(engine, *rule, date, thresholds)) for rule in alberta_expansion_rules]
    alberta_contraction = [_decorate_condition(engine, _point_condition(engine, *rule, date, thresholds)) for rule in alberta_contraction_rules]
    ontario_score, ontario_coverage = _side_score(ontario)
    alberta_expansion_score, alberta_coverage = _side_score(alberta_expansion)
    alberta_contraction_score, _ = _side_score(alberta_contraction)
    reverse = ontario_score <= 0.30 and alberta_contraction_score >= 0.60
    divergence = ontario_score >= 0.60 and alberta_expansion_score >= 0.60 or reverse
    return {
        "status": "Regional divergence" if divergence else "No classified regional divergence",
        "active": divergence,
        "date": date,
        "ontarioTransmission": {
            "score": ontario_score, "coverage": ontario_coverage,
            "evidence": [item for item in ontario if item["met"]],
            "conflicts": [item for item in ontario if item["available"] and not item["met"]],
            "missing": [
                {"indicator": "ontario_manufacturing_output", "label": "Ontario manufacturing output", "reason": "Not implemented at native frequency."}
            ],
        },
        "albertaProducerConditions": {
            "score": alberta_expansion_score, "contractionScore": alberta_contraction_score, "coverage": alberta_coverage,
            "evidence": [item for item in alberta_expansion if item["met"]],
            "conflicts": [item for item in alberta_expansion if item["available"] and not item["met"]],
            "missing": [],
        },
        "explanation": "Ontario consumer/labour stress and Alberta producer expansion are reported separately; their scores are not averaged into a national neutral.",
    }


def _clock(engine: IndicatorEngine, fields: set[str], date: str, status: str, generated_at: str) -> dict[str, Any]:
    available = []
    stale = []
    missing = []
    partial = []
    for field in sorted(fields):
        point = engine.point(field, date)
        if point:
            available.append(point)
            if int(point["ageMonths"]) > 0:
                partial.append({"indicator": field, "label": point["label"], "observationDate": point["sourceDate"], "ageMonths": point["ageMonths"]})
            continue
        history = [item for item in engine.histories.get(field, []) if item[0] <= date]
        target = {"indicator": field, "label": engine.indicators.get(field, {}).get("label", field)}
        if history:
            stale.append({**target, "lastAvailableDate": history[-1][0]})
        else:
            missing.append(target)
    dates = [str(item["sourceDate"]) for item in available]
    availability = len(available) / len(fields) if fields else 0.0
    freshness = sum(float(item["freshnessWeight"]) * float(item["reliabilityWeight"]) for item in available) / len(fields) if fields else 0.0
    return {
        "classificationDate": date,
        "generationDate": generated_at,
        "status": status,
        "requiredIndicatorAvailability": availability,
        "freshnessAdjustedCoverage": freshness,
        "coverage": availability,
        "newestObservationDate": max(dates) if dates else None,
        "oldestRequiredObservationDate": min(dates) if dates else None,
        "observationRange": {"oldest": min(dates) if dates else None, "newest": max(dates) if dates else None},
        "staleIndicators": stale,
        "missingIndicators": missing,
        "partialPeriodIndicators": partial,
        "revisedDataWarning": "Retrospective Canadian classification using revised data. Complete real-time vintage histories are not available.",
        "dataVintageStatus": "retrospective_revised_data",
    }


def _quarterly_date(engine: IndicatorEngine, fields: set[str], minimum: float) -> str:
    latest = _month_index(engine.latest_date())
    year, month_zero = divmod(latest, 12)
    month = month_zero + 1
    quarter_end = 12 if month <= 3 else 3 if month <= 6 else 6 if month <= 9 else 9
    year = year - 1 if month <= 3 else year
    candidate = f"{year:04d}-{quarter_end:02d}-01"
    for _ in range(40):
        coverage = sum(engine.point(field, candidate) is not None for field in fields) / len(fields)
        if coverage >= minimum:
            return candidate
        candidate = _shift_months(candidate, -3)
    return candidate


def _episode_rows(engine: IndicatorEngine) -> list[Row]:
    rows: list[Row] = []
    for name, start, end, sequence, alternatives in EPISODES:
        values: dict[str, Any] = {}
        covered = 0
        for column, field in EPISODE_FIELDS:
            observations = [(date, value) for date, value in engine.histories.get(field, []) if f"{start}-01" <= date <= f"{end}-01"]
            if observations:
                covered += 1
                date, value = observations[-1]
                values[column] = value
                values[f"{column}_date"] = date
            else:
                values[column] = None
                values[f"{column}_date"] = None
        rows.append({
            "episode": name, "start": start, "end": end, **values,
            "approximate_sequence": sequence, "alternative_explanations": alternatives,
            "available_data_coverage": covered / len(EPISODE_FIELDS),
            "coverage_note": f"{covered} of {len(EPISODE_FIELDS)} requested evidence fields have observations within the episode; blank fields are not estimated.",
            "control_period": "control" in name,
        })
    return rows


def _episode_markdown(rows: list[Row]) -> str:
    lines = [
        "# Canadian Historical Episodes",
        "",
        f"**Scope:** {CANADIAN_SCOPE}",
        "",
        "This episode library records observed Canadian evidence where the implemented histories overlap each episode. Blank CSV fields mean that the source series does not cover that period; no values are backfilled or manufactured.",
        "",
    ]
    for row in rows:
        lines.extend([
            f"## {row['episode']}",
            "",
            f"- Window: {row['start']} to {row['end']}",
            f"- Approximate sequence: {row['approximate_sequence']}",
            f"- Alternative explanations: {row['alternative_explanations']}",
            f"- Available coverage: {100 * float(row['available_data_coverage']):.0f}% ({row['coverage_note']})",
            "",
        ])
    lines.extend([
        "## Vintage Limitation",
        "",
        "These are retrospective episode summaries using current revised histories. They are calibration references, not causal labels or reconstructions of information available to analysts at each historical date.",
        "",
    ])
    return "\n".join(lines)


def _analogues(engine: IndicatorEngine, rows: list[Row], date: str, fields: set[str]) -> list[dict[str, Any]]:
    current = {field: engine.point(field, date) for field in fields}
    matches = []
    for episode in rows:
        end = f"{episode['end']}-01"
        distances = []
        for field in fields:
            now = current.get(field)
            history = [(d, v) for d, v in engine.histories.get(field, []) if d <= end]
            if not now or not history:
                continue
            past_values = [v for d, v in engine.histories[field] if d <= history[-1][0]]
            past_percentile = _percentile(past_values, history[-1][1])
            if now["historicalPercentile"] is not None and past_percentile is not None:
                distances.append(abs(float(now["historicalPercentile"]) - past_percentile) / 100)
        if distances:
            matches.append({"episode": episode["episode"], "similarity": 1 - sum(distances) / len(distances), "commonIndicators": len(distances), "comparisonDate": end})
    return sorted(matches, key=lambda item: (-item["similarity"], item["episode"]))[:3]


def _summary(symptoms: list[dict[str, Any]], divergence: dict[str, Any], classification: str) -> str:
    clauses = [f"Current Canadian state: {classification}."]
    relevant = [item for item in symptoms if item["status"] in {"active", "emerging", "fading"}]
    for symptom in relevant:
        clauses.append(f"{symptom['name']} is {symptom['statusLabel'].lower()}: {symptom['plainLanguageMeaning']}")
    if divergence["active"]:
        clauses.append("Ontario-facing stress and Alberta producer conditions currently meet the configured regional-divergence rule.")
    if not relevant:
        clauses.append("No documented symptom is currently active, emerging, or fading.")
    return " ".join(clauses)


def build_canadian_classification_outputs(
    root: Path,
    indicators: list[dict[str, Any]],
    generated_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[Row]]:
    generated_at = generated_at or datetime.now(UTC).isoformat(timespec="seconds")
    symptom_config, regime_config = load_canadian_rules(root)
    engine = IndicatorEngine(indicators, symptom_config["settings"])
    fields = _required_fields(symptom_config, regime_config)
    threshold_key = str(symptom_config["settings"]["primaryThresholdSet"])
    nowcast_date = engine.latest_date()
    quarterly_date = _quarterly_date(engine, fields, float(regime_config["settings"]["minimumEvidenceCoverage"]))
    monthly_symptoms, monthly_regimes = _classification(engine, symptom_config, regime_config, nowcast_date, 1, threshold_key)
    quarterly_symptoms, quarterly_regimes = _classification(engine, symptom_config, regime_config, quarterly_date, 3, threshold_key)
    del quarterly_symptoms
    thresholds = symptom_config["settings"]["thresholdSets"][threshold_key]
    divergence = regional_divergence(engine, nowcast_date, thresholds)
    episodes = _episode_rows(engine)
    analogues = _analogues(engine, episodes, nowcast_date, fields)
    monthly_clock = _clock(engine, fields, nowcast_date, "provisional_monthly", generated_at)
    quarterly_clock = _clock(engine, fields, quarterly_date, "quarterly_aligned", generated_at)
    if divergence["active"]:
        monthly_regimes["classification"] = "Regional divergence"
        monthly_regimes["confidence"] = "moderate"
    for clock, regimes in ((monthly_clock, monthly_regimes), (quarterly_clock, quarterly_regimes)):
        if clock["freshnessAdjustedCoverage"] < 0.60:
            regimes["confidence"] = "low"
        clock.update(regimes)
    current = {
        "schemaVersion": 1,
        "scope": CANADIAN_SCOPE,
        "evidenceScopes": symptom_config["evidenceScopes"],
        "date": nowcast_date,
        "asOfDate": generated_at,
        "status": monthly_regimes["classification"],
        "score": monthly_regimes["primaryRegime"]["score"],
        "summary": _summary(monthly_symptoms, divergence, monthly_regimes["classification"]),
        "provisionalClassification": monthly_clock,
        "quarterlyAlignedClassification": quarterly_clock,
        "primaryState": monthly_regimes["primaryRegime"],
        "secondaryState": monthly_regimes["secondaryRegime"],
        "confidence": monthly_regimes["confidence"],
        "coverage": monthly_clock["requiredIndicatorAvailability"],
        "freshnessAdjustedCoverage": monthly_clock["freshnessAdjustedCoverage"],
        "supportingEvidence": monthly_regimes["primaryRegime"]["supportingEvidence"],
        "conflictingEvidence": monthly_regimes["primaryRegime"]["conflictingEvidence"],
        "missingEvidence": monthly_regimes["primaryRegime"]["missingEvidence"],
        "activeSymptoms": [item for item in monthly_symptoms if item["status"] == "active"],
        "emergingSymptoms": [item for item in monthly_symptoms if item["status"] == "emerging"],
        "regionalDivergence": divergence,
        "regionalContribution": divergence,
        "historicalAnalogues": analogues,
        "limitations": [
            monthly_clock["revisedDataWarning"],
            "Labour evidence is incomplete without wages and actual hours.",
            "Household stress is not classified without income, expenditure-burden, or insolvency evidence.",
            "Ontario manufacturing output is unavailable, and Alberta is represented by a compact producer evidence set.",
        ],
        "ruleVersion": {"symptoms": symptom_config["version"], "regimes": regime_config["version"]},
    }
    sensitivity = {}
    for key in symptom_config["settings"]["thresholdSets"]:
        symptoms, regimes = _classification(engine, symptom_config, regime_config, nowcast_date, 1, key)
        sensitivity[key] = {"classification": regimes["classification"], "topScore": regimes["primaryRegime"]["score"], "symptoms": {item["id"]: item["statusLabel"] for item in symptoms}}
    for symptom in monthly_symptoms:
        symptom["sensitivity"] = {key: value["symptoms"][symptom["id"]] for key, value in sensitivity.items()}
    symptom_output = {
        "schemaVersion": 1, "scope": CANADIAN_SCOPE, "date": nowcast_date, "status": "provisional",
        "score": sum(item["score"] for item in monthly_symptoms) / len(monthly_symptoms),
        "coverage": monthly_clock["requiredIndicatorAvailability"], "generationDate": generated_at,
        "clock": monthly_clock, "evaluations": monthly_symptoms, "sensitivity": sensitivity,
        "supportingEvidence": [item for symptom in monthly_symptoms for item in symptom["confirmingEvidence"]],
        "conflictingEvidence": [item for symptom in monthly_symptoms for item in symptom["conflictingEvidence"]],
        "missingEvidence": [item for symptom in monthly_symptoms for item in symptom["missingEvidence"]],
        "regionalContribution": divergence, "historicalAnalogues": analogues,
        "limitations": current["limitations"],
    }
    score_output = {
        "schemaVersion": 1, "scope": CANADIAN_SCOPE, "date": nowcast_date, "status": monthly_regimes["classification"],
        "score": monthly_regimes["primaryRegime"]["score"], "coverage": monthly_clock["requiredIndicatorAvailability"],
        "freshnessAdjustedCoverage": monthly_clock["freshnessAdjustedCoverage"], "generationDate": generated_at,
        "scores": monthly_regimes["allRegimeScores"],
        "decision": {key: monthly_regimes[key] for key in ("classification", "confidence", "coverage", "margin", "decisionRules")},
        "supportingEvidence": monthly_regimes["primaryRegime"]["supportingEvidence"],
        "conflictingEvidence": monthly_regimes["primaryRegime"]["conflictingEvidence"],
        "missingEvidence": monthly_regimes["primaryRegime"]["missingEvidence"],
        "regionalContribution": divergence, "historicalAnalogues": analogues,
        "limitations": current["limitations"], "sensitivity": sensitivity,
    }
    output_root = root / "website" / "public" / "generated" / "canada"
    output_root.mkdir(parents=True, exist_ok=True)
    for filename, payload in (("current-classification.json", current), ("symptom-evaluations.json", symptom_output), ("regime-scores.json", score_output)):
        (output_root / filename).write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_csv(root / "analysis" / "canadian_historical_episodes.csv", episodes)
    (root / "analysis" / "canadian_historical_episodes.md").write_text(_episode_markdown(episodes), encoding="utf-8")
    return current, symptom_output, score_output, episodes
