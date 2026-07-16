from __future__ import annotations

import json
import math
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import Row


SCOPE = "United States energy-economic conditions with global oil-market and global-liquidity inputs."
STATUS_STRENGTH = {"active": 1.0, "emerging": 0.7, "fading": 0.35, "inactive": 0.0, "insufficient_data": 0.0}
QUARTERLY_SOURCE_SERIES = {
    "business_investment_YoY": "PNFIC1",
    "Real_GDP_growth": "GDPC1",
    "credit_tightening_pct": "DRTSCILM",
    "credit_card_delinquency_rate": "DRCCLACBS",
}


def load_rules(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config_root = root / "config"
    if not (config_root / "symptom_rules.json").exists():
        config_root = Path(__file__).resolve().parents[1] / "config"
    symptom_rules = json.loads((config_root / "symptom_rules.json").read_text(encoding="utf-8"))
    regime_rules = json.loads((config_root / "regime_rules.json").read_text(encoding="utf-8"))
    if symptom_rules.get("scope") != SCOPE or regime_rules.get("scope") != SCOPE:
        raise ValueError("Classification rule scope must match the published formal scope")
    return symptom_rules, regime_rules


def _month_index(date: str) -> int:
    year, month = map(int, date[:7].split("-"))
    return year * 12 + month - 1


def _month_date(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}-01"


def _shift_months(date: str, months: int) -> str:
    return _month_date(_month_index(date) + months)


def _percentile(values: list[float], current: float) -> float | None:
    if not values:
        return None
    below = sum(value < current for value in values)
    equal = sum(value == current for value in values)
    return 100.0 * (below + 0.5 * equal) / len(values)


def _finite(value: object) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def classification_indicators(root: Path, indicators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep carried quarterly histories visible, but classify only on true source-quarter dates."""
    output = []
    for indicator in indicators:
        field = str(indicator["field"])
        series_id = QUARTERLY_SOURCE_SERIES.get(field)
        source_path = root / "data" / "raw" / "fred" / f"{series_id}.csv" if series_id else None
        if not source_path or not source_path.exists():
            output.append(indicator)
            continue
        with source_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        source_dates = set()
        for row in rows:
            raw_date = row.get("observation_date") or row.get("DATE") or row.get("date")
            raw_value = row.get(series_id) or row.get("value")
            if raw_date and raw_value not in {None, "", "."}:
                source_dates.add(f"{str(raw_date)[:7]}-01")
        filtered = [row for row in indicator["observations"] if str(row["date"]) in source_dates]
        output.append({**indicator, "observations": filtered, "latest": {**indicator["latest"], "date": filtered[-1]["date"], "value": filtered[-1]["value"]}} if filtered else indicator)
    return output


class IndicatorEngine:
    def __init__(self, indicators: list[dict[str, Any]], settings: dict[str, Any]):
        self.indicators = {str(indicator["field"]): indicator for indicator in indicators}
        self.settings = settings
        self.histories = {
            field: [(str(row["date"]), float(row["value"])) for row in indicator["observations"] if _finite(row.get("value")) is not None]
            for field, indicator in self.indicators.items()
        }

    def fields(self) -> set[str]:
        return set(self.indicators)

    def latest_date(self) -> str:
        return max(str(indicator["latest"]["date"]) for indicator in self.indicators.values())

    def _maximum_age(self, field: str) -> int:
        frequency = str(self.indicators[field].get("frequency", "monthly")).lower()
        if "annual" in frequency:
            return 18
        if "quarter" in frequency:
            return int(self.settings.get("quarterlyMaximumAgeMonths", 9))
        return int(self.settings.get("monthlyMaximumAgeMonths", 6))

    def point(self, field: str, evaluation_date: str) -> dict[str, Any] | None:
        history = self.histories.get(field, [])
        available = [(date, value) for date, value in history if date <= evaluation_date]
        if not available:
            return None
        source_date, value = available[-1]
        age = max(0, _month_index(evaluation_date) - _month_index(source_date))
        maximum_age = self._maximum_age(field)
        if age > maximum_age:
            return None
        values = [item[1] for item in available]
        since_2000 = [item[1] for item in available if item[0] >= "2000-01-01"]

        def prior(months: int) -> float | None:
            cutoff = _shift_months(source_date, -months)
            candidates = [item for item in available if item[0] <= cutoff]
            return candidates[-1][1] if candidates else None

        prior_3, prior_6 = prior(3), prior(6)
        indicator = self.indicators[field]
        confidence = str(indicator.get("confidenceLevel", "medium")).lower()
        reliability = {"high": 1.0, "medium": 0.85, "low": 0.65}.get(confidence, 0.75)
        freshness = max(0.15, 1.0 - age / (maximum_age + 1))
        return {
            "indicator": field,
            "label": indicator["label"],
            "value": value,
            "unit": indicator["unit"],
            "sourceDate": source_date,
            "frequency": indicator["frequency"],
            "ageMonths": age,
            "maximumAgeMonths": maximum_age,
            "freshnessWeight": freshness,
            "reliabilityWeight": reliability,
            "historicalPercentile": _percentile(values, value),
            "post2000Percentile": _percentile(since_2000, value),
            "momentum3m": value - prior_3 if prior_3 is not None else None,
            "momentum6m": value - prior_6 if prior_6 is not None else None,
            "revisedData": True,
        }

    def recent_max_percentile(self, field: str, evaluation_date: str, months: int) -> tuple[float | None, str | None]:
        start = _shift_months(evaluation_date, -months)
        candidates = [(date, value) for date, value in self.histories.get(field, []) if start <= date <= evaluation_date]
        best: tuple[float, str] | None = None
        for date, value in candidates:
            past = [item_value for item_date, item_value in self.histories[field] if item_date <= date]
            percentile = _percentile(past, value)
            if percentile is not None and (best is None or percentile > best[0]):
                best = percentile, date
        return best if best else (None, None)

    def condition(self, rule: dict[str, Any], evaluation_date: str, thresholds: dict[str, float]) -> dict[str, Any]:
        field = str(rule["indicator"])
        point = self.point(field, evaluation_date)
        result = {
            "indicator": field,
            "label": self.indicators.get(field, {}).get("label", field),
            "transformation": rule.get("transformation", "full_history_percentile"),
            "expectedDirection": rule["expectedDirection"],
            "group": rule.get("group", field),
            "available": point is not None,
            "met": False,
            "strength": 0.0,
            "value": point.get("value") if point else None,
            "unit": point.get("unit") if point else None,
            "historicalPercentile": point.get("historicalPercentile") if point else None,
            "sourceDate": point.get("sourceDate") if point else None,
            "frequency": point.get("frequency") if point else self.indicators.get(field, {}).get("frequency"),
            "ageMonths": point.get("ageMonths") if point else None,
            "freshnessWeight": point.get("freshnessWeight") if point else 0.0,
            "reliabilityWeight": point.get("reliabilityWeight") if point else 0.0,
        }
        if point is None:
            return result
        direction = str(rule["expectedDirection"])
        transformation = str(rule.get("transformation", "full_history_percentile"))
        metric: float | None
        threshold: float | None = None
        if transformation == "recent_max_percentile":
            metric, metric_date = self.recent_max_percentile(field, evaluation_date, int(rule.get("trendWindow", 6)))
            result["metricDate"] = metric_date
        elif transformation == "post_2000_percentile":
            metric = _finite(point.get("post2000Percentile"))
        elif transformation == "momentum":
            window = int(rule.get("trendWindow", 3))
            metric = _finite(point.get("momentum6m" if window >= 6 else "momentum3m"))
        else:
            metric = _finite(point.get("historicalPercentile"))
        result["metricValue"] = metric
        if metric is None:
            result["available"] = False
            return result
        if direction in {"high", "low"}:
            threshold = float(thresholds[direction])
            result["met"] = metric >= threshold if direction == "high" else metric <= threshold
            denominator = max(1.0, abs(threshold - 50.0))
            result["strength"] = _clamp((metric - 50.0) / denominator) if direction == "high" else _clamp((50.0 - metric) / denominator)
        elif direction in {"rising", "falling"}:
            result["met"] = metric > 0 if direction == "rising" else metric < 0
            result["strength"] = 1.0 if result["met"] else 0.0
        result["threshold"] = threshold
        result["weightedStrength"] = result["strength"] * point["freshnessWeight"] * point["reliabilityWeight"]
        return result


def _raw_symptom(
    engine: IndicatorEngine,
    rule: dict[str, Any],
    evaluation_date: str,
    thresholds: dict[str, float],
) -> dict[str, Any]:
    required = [engine.condition(item, evaluation_date, thresholds) for item in rule["requiredIndicators"]]
    confirming = [engine.condition(item, evaluation_date, thresholds) for item in rule.get("confirmingIndicators", [])]
    conflicting = [engine.condition(item, evaluation_date, thresholds) for item in rule.get("conflictingIndicators", [])]
    required_groups = sorted({str(item["group"]) for item in required})
    group_results = []
    for group in required_groups:
        members = [item for item in required if item["group"] == group]
        available = [item for item in members if item["available"]]
        group_results.append({
            "group": group,
            "available": bool(available),
            "met": any(item["met"] for item in available),
            "strength": max((float(item.get("weightedStrength", 0.0)) for item in available), default=0.0),
        })
    coverage = sum(item["available"] for item in required) / len(required) if required else 0.0
    group_coverage = sum(item["available"] for item in group_results) / len(group_results) if group_results else 0.0
    required_strength = sum(item["strength"] for item in group_results) / len(group_results) if group_results else 0.0
    confirm_available = [item for item in confirming if item["available"]]
    confirm_strength = sum(float(item.get("weightedStrength", 0.0)) for item in confirm_available) / len(confirm_available) if confirm_available else 0.0
    conflicts_met = [item for item in conflicting if item["available"] and item["met"]]
    conflict_penalty = 0.15 * (sum(float(item.get("weightedStrength", 0.0)) for item in conflicts_met) / len(conflicts_met) if conflicts_met else 0.0)
    score = _clamp(0.80 * required_strength + 0.20 * confirm_strength - conflict_penalty)
    minimum_coverage = float(rule.get("minimumCoverage", 0.70))
    active = coverage >= minimum_coverage and group_coverage >= minimum_coverage and all(item["met"] for item in group_results)
    return {
        "score": score,
        "coverage": coverage,
        "groupCoverage": group_coverage,
        "rawActive": active,
        "requiredConditionResults": required,
        "requiredGroupResults": group_results,
        "confirmingEvidence": [item for item in confirming if item["met"]],
        "conflictingEvidence": conflicts_met,
        "missingEvidence": [item for item in [*required, *confirming, *conflicting] if not item["available"]],
    }


def evaluate_symptom(
    engine: IndicatorEngine,
    rule: dict[str, Any],
    evaluation_date: str,
    thresholds: dict[str, float],
    step_months: int,
) -> dict[str, Any]:
    current = _raw_symptom(engine, rule, evaluation_date, thresholds)
    prior_results = [_raw_symptom(engine, rule, _shift_months(evaluation_date, -step_months * offset), thresholds) for offset in (1, 2)]
    persistence = 0
    for result in [current, *prior_results]:
        if result["rawActive"]:
            persistence += 1
        else:
            break
    minimum_coverage = float(rule.get("minimumCoverage", 0.70))
    if current["coverage"] < minimum_coverage or current["groupCoverage"] < minimum_coverage:
        status = "insufficient_data"
    elif current["rawActive"]:
        status = "active" if persistence >= int(rule.get("persistenceRequirement", 2)) else "emerging"
    elif prior_results[0]["rawActive"]:
        status = "fading"
    else:
        status = "inactive"
    confidence = "high" if current["coverage"] >= 0.90 and status in {"active", "inactive"} else "moderate" if current["coverage"] >= minimum_coverage else "low"
    return {
        "id": rule["id"],
        "name": rule["name"],
        "plainLanguageMeaning": rule["meaning"],
        "status": status,
        "score": current["score"],
        "evaluationDate": evaluation_date,
        "confidence": confidence,
        "coverage": current["coverage"],
        "requiredConditionResults": current["requiredConditionResults"],
        "requiredGroupResults": current["requiredGroupResults"],
        "confirmingEvidence": current["confirmingEvidence"],
        "conflictingEvidence": current["conflictingEvidence"],
        "missingEvidence": current["missingEvidence"],
        "persistence": {"consecutiveUpdates": persistence, "requiredForActive": int(rule.get("persistenceRequirement", 2)), "updateStepMonths": step_months},
        "historicalAnalogues": rule.get("historicalAnalogues", []),
        "alternativeExplanations": rule.get("alternativeExplanations", []),
        "evidenceLabel": rule.get("evidenceLabel", "Contextual indicator"),
        "rule": {
            "requiredIndicators": rule["requiredIndicators"],
            "confirmingIndicators": rule.get("confirmingIndicators", []),
            "conflictingIndicators": rule.get("conflictingIndicators", []),
            "minimumCoverage": minimum_coverage,
            "persistenceRequirement": int(rule.get("persistenceRequirement", 2)),
            "thresholds": thresholds,
        },
    }


def _regime_score(
    engine: IndicatorEngine,
    rule: dict[str, Any],
    symptom_results: dict[str, dict[str, Any]],
    evaluation_date: str,
    thresholds: dict[str, float],
) -> dict[str, Any]:
    evidence = []
    for item in rule["indicatorEvidence"]:
        condition_rule = {**item, "transformation": "momentum" if item["expectedDirection"] in {"rising", "falling"} else "full_history_percentile", "group": item.get("layer", "other"), "trendWindow": 3}
        evidence.append(engine.condition(condition_rule, evaluation_date, thresholds))
    by_layer: dict[str, list[dict[str, Any]]] = {}
    for item in evidence:
        by_layer.setdefault(str(item["group"]), []).append(item)
    layer_scores = {}
    for layer, items in by_layer.items():
        available = [item for item in items if item["available"]]
        layer_scores[layer] = {
            "score": sum(float(item.get("weightedStrength", 0.0)) for item in available) / len(available) if available else 0.0,
            "coverage": len(available) / len(items),
        }
    required_layers = list(rule.get("requiredLayers", by_layer))
    covered_layers = sum(layer_scores.get(layer, {}).get("coverage", 0.0) > 0 for layer in required_layers)
    layer_coverage = covered_layers / len(required_layers) if required_layers else 0.0
    indicator_coverage = sum(item["available"] for item in evidence) / len(evidence) if evidence else 0.0
    indicator_score = sum(layer_scores.get(layer, {}).get("score", 0.0) for layer in required_layers) / len(required_layers) if required_layers else 0.0
    expected_symptoms = [symptom_results[item] for item in rule.get("expectedSymptoms", []) if item in symptom_results]
    symptom_score = sum(STATUS_STRENGTH[item["status"]] for item in expected_symptoms) / len(expected_symptoms) if expected_symptoms else indicator_score
    conflicting_symptoms = [symptom_results[item] for item in rule.get("conflictingSymptoms", []) if item in symptom_results]
    symptom_penalty = 0.15 * (sum(STATUS_STRENGTH[item["status"]] for item in conflicting_symptoms) / len(conflicting_symptoms) if conflicting_symptoms else 0.0)
    contradiction = sum(max(0.0, 0.5 - float(item.get("strength", 0.0))) * 2 for item in evidence if item["available"]) / max(1, sum(item["available"] for item in evidence))
    contradiction_penalty = 0.10 * contradiction
    coverage = min(indicator_coverage, layer_coverage)
    missing_penalty_factor = 0.75 + 0.25 * coverage
    score = _clamp((0.75 * indicator_score + 0.25 * symptom_score - symptom_penalty - contradiction_penalty) * missing_penalty_factor)
    return {
        "id": rule["id"],
        "name": rule["name"],
        "score": score,
        "coverage": coverage,
        "indicatorCoverage": indicator_coverage,
        "layerCoverage": layer_coverage,
        "layerScores": layer_scores,
        "indicatorEvidence": evidence,
        "expectedSymptoms": [{"id": item["id"], "name": item["name"], "status": item["status"], "score": item["score"]} for item in expected_symptoms],
        "conflictingSymptoms": [{"id": item["id"], "name": item["name"], "status": item["status"]} for item in conflicting_symptoms],
        "contradictionPenalty": contradiction_penalty + symptom_penalty,
        "supportingEvidence": [item for item in evidence if item["available"] and float(item.get("strength", 0.0)) >= 0.67],
        "conflictingEvidence": [item for item in evidence if item["available"] and float(item.get("strength", 0.0)) <= 0.20],
        "missingEvidence": [item for item in evidence if not item["available"]],
        "predecessors": rule.get("predecessors", []),
        "successors": rule.get("successors", []),
        "exceptionalJumpConditions": rule.get("exceptionalJumpConditions", []),
    }


def classify_regimes(
    engine: IndicatorEngine,
    regime_config: dict[str, Any],
    symptom_results: list[dict[str, Any]],
    evaluation_date: str,
    thresholds: dict[str, float],
) -> dict[str, Any]:
    symptom_lookup = {item["id"]: item for item in symptom_results}
    scores = [_regime_score(engine, rule, symptom_lookup, evaluation_date, thresholds) for rule in regime_config["regimes"]]
    scores.sort(key=lambda item: (-item["score"], item["id"]))
    primary, secondary = scores[0], scores[1]
    settings = regime_config["settings"]
    minimum_coverage = float(settings["minimumEvidenceCoverage"])
    minimum_score = float(settings["minimumTopRegimeScore"])
    minimum_margin = float(settings["minimumMargin"])
    margin = primary["score"] - secondary["score"]
    coverage = primary["coverage"]
    if coverage < minimum_coverage or primary["score"] < minimum_score:
        classification = "Unclassified"
    elif margin < minimum_margin:
        classification = f"Mixed transition: {primary['name']}/{secondary['name']}"
    else:
        classification = primary["name"]
    confidence = "low"
    if classification != "Unclassified":
        confidence = "high" if coverage >= 0.85 and primary["score"] >= 0.72 and margin >= 0.15 else "moderate"
    return {
        "classification": classification,
        "primaryRegime": primary,
        "secondaryRegime": secondary,
        "confidence": confidence,
        "coverage": coverage,
        "margin": margin,
        "allRegimeScores": scores,
        "decisionRules": {"minimumEvidenceCoverage": minimum_coverage, "minimumTopRegimeScore": minimum_score, "minimumMargin": minimum_margin},
    }


def _required_fields(symptom_config: dict[str, Any], regime_config: dict[str, Any]) -> set[str]:
    fields = set()
    for symptom in symptom_config["symptoms"]:
        for kind in ("requiredIndicators", "confirmingIndicators", "conflictingIndicators"):
            fields.update(str(item["indicator"]) for item in symptom.get(kind, []))
    for regime in regime_config["regimes"]:
        fields.update(str(item["indicator"]) for item in regime["indicatorEvidence"])
    return fields


def _clock_metadata(engine: IndicatorEngine, fields: set[str], date: str, status: str, generated_at: str) -> dict[str, Any]:
    points = [engine.point(field, date) for field in fields]
    available = [point for point in points if point]
    source_dates = [str(point["sourceDate"]) for point in available]
    stale = []
    missing = []
    partial = []
    for field in sorted(fields):
        point = engine.point(field, date)
        if point is None:
            history = engine.histories.get(field, [])
            latest_before = [item for item in history if item[0] <= date]
            target = {"indicator": field, "label": engine.indicators.get(field, {}).get("label", field)}
            if latest_before:
                target["lastAvailableDate"] = latest_before[-1][0]
                stale.append(target)
            else:
                missing.append(target)
        elif status == "provisional" and date[:7] == generated_at[:7] and str(point["sourceDate"])[:7] == date[:7]:
            partial.append({"indicator": field, "label": point["label"], "sourceDate": point["sourceDate"]})
    return {
        "classificationDate": date,
        "generationDate": generated_at,
        "newestObservationDate": max(source_dates) if source_dates else None,
        "oldestRequiredObservationDate": min(source_dates) if source_dates else None,
        "coverage": len(available) / len(fields) if fields else 0.0,
        "status": status,
        "dataVintageStatus": "retrospective_revised_data",
        "dataVintageWarning": "Retrospective classification using revised data. Real-time vintage histories are not yet available for every required series.",
        "staleIndicators": stale,
        "missingIndicators": missing,
        "partialPeriodIndicators": partial,
    }


def _latest_confirmed_quarter(engine: IndicatorEngine, fields: set[str], minimum_coverage: float) -> str:
    latest_index = _month_index(engine.latest_date())
    year, month_zero = divmod(latest_index, 12)
    month = month_zero + 1
    completed_quarter_month = 12 if month <= 3 else 3 if month <= 6 else 6 if month <= 9 else 9
    completed_year = year - 1 if month <= 3 else year
    candidate = f"{completed_year:04d}-{completed_quarter_month:02d}-01"
    for _ in range(40):
        coverage = sum(engine.point(field, candidate) is not None for field in fields) / len(fields)
        if coverage >= minimum_coverage:
            return candidate
        candidate = _shift_months(candidate, -3)
    return candidate


def _evaluation(
    engine: IndicatorEngine,
    symptom_config: dict[str, Any],
    regime_config: dict[str, Any],
    date: str,
    step_months: int,
    threshold_key: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    thresholds = symptom_config["settings"]["thresholdSets"][threshold_key]
    symptoms = [evaluate_symptom(engine, rule, date, thresholds, step_months) for rule in symptom_config["symptoms"]]
    regimes = classify_regimes(engine, regime_config, symptoms, date, thresholds)
    return symptoms, regimes


def _turning_point(engine: IndicatorEngine, field: str, start: str, end: str, mode: str) -> str | None:
    rows = [(date, value) for date, value in engine.histories.get(field, []) if start <= date <= end]
    if not rows:
        return None
    return (max(rows, key=lambda item: item[1]) if mode == "max" else min(rows, key=lambda item: item[1]))[0]


def _episode_analogues(engine: IndicatorEngine, episodes: list[Row], current_date: str, fields: set[str]) -> list[dict[str, Any]]:
    current = {field: engine.point(field, current_date) for field in fields}
    results = []
    for episode in episodes:
        end = f"{episode['end']}-01" if len(str(episode.get("end"))) == 7 else str(episode.get("end"))
        distances = []
        for field in fields:
            current_point = current.get(field)
            episode_point = engine.point(field, end)
            if current_point and episode_point and current_point["historicalPercentile"] is not None and episode_point["historicalPercentile"] is not None:
                distances.append(abs(float(current_point["historicalPercentile"]) - float(episode_point["historicalPercentile"])) / 100.0)
        if distances:
            results.append({"episode": episode["episode"], "similarity": 1.0 - sum(distances) / len(distances), "commonIndicators": len(distances), "comparisonDate": end})
    return sorted(results, key=lambda item: (-item["similarity"], item["episode"]))[:3]


def build_classification_outputs(
    root: Path,
    indicators: list[dict[str, Any]],
    episodes: list[Row],
    generated_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[Row]]:
    generated_at = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    symptom_config, regime_config = load_rules(root)
    engine = IndicatorEngine(classification_indicators(root, indicators), symptom_config["settings"])
    fields = _required_fields(symptom_config, regime_config)
    nowcast_date = engine.latest_date()
    confirmed_date = _latest_confirmed_quarter(engine, fields, float(regime_config["settings"]["minimumEvidenceCoverage"]))
    primary_threshold = str(symptom_config["settings"]["primaryThresholdSet"])
    nowcast_symptoms, nowcast_regimes = _evaluation(engine, symptom_config, regime_config, nowcast_date, 1, primary_threshold)
    confirmed_symptoms, confirmed_regimes = _evaluation(engine, symptom_config, regime_config, confirmed_date, 3, primary_threshold)
    prior_month_symptoms, prior_month_regimes = _evaluation(engine, symptom_config, regime_config, _shift_months(nowcast_date, -1), 1, primary_threshold)
    del prior_month_symptoms
    monthly_persistence = 1
    for offset in range(1, 12):
        _, prior_regimes = _evaluation(engine, symptom_config, regime_config, _shift_months(nowcast_date, -offset), 1, primary_threshold)
        if prior_regimes["primaryRegime"]["id"] != nowcast_regimes["primaryRegime"]["id"]:
            break
        monthly_persistence += 1
    required_monthly_persistence = int(regime_config["settings"].get("confirmedMonthlyPersistence", 2))
    predecessor_id = prior_month_regimes["primaryRegime"]["id"]
    predecessor_expected = predecessor_id in nowcast_regimes["primaryRegime"].get("predecessors", []) or predecessor_id == nowcast_regimes["primaryRegime"]["id"]
    exceptional_transition = None
    if nowcast_regimes["classification"] != "Unclassified" and prior_month_regimes["classification"] != "Unclassified" and not predecessor_expected:
        exceptional_transition = {
            "fromRegime": prior_month_regimes["primaryRegime"]["name"],
            "toRegime": nowcast_regimes["primaryRegime"]["name"],
            "reasonRequired": True,
            "documentedJumpConditions": nowcast_regimes["primaryRegime"].get("exceptionalJumpConditions", []),
            "note": "This jump is outside the configured normal predecessor sequence and requires analyst review; the rules do not infer a causal shock.",
        }
    nowcast_clock = _clock_metadata(engine, fields, nowcast_date, "provisional", generated_at)
    confirmed_clock = _clock_metadata(engine, fields, confirmed_date, "confirmed_quarterly", generated_at)
    analogues = _episode_analogues(engine, episodes, nowcast_date, fields)
    sensitivities = {}
    for key in symptom_config["settings"]["thresholdSets"]:
        symptoms, regimes = _evaluation(engine, symptom_config, regime_config, nowcast_date, 1, key)
        sensitivities[key] = {"symptoms": {item["id"]: item["status"] for item in symptoms}, "classification": regimes["classification"], "topScore": regimes["primaryRegime"]["score"]}
    for symptom in nowcast_symptoms:
        symptom["sensitivity"] = {key: value["symptoms"][symptom["id"]] for key, value in sensitivities.items()}

    history_rows = []
    start_index = _month_index("2000-03-01")
    end_index = _month_index(confirmed_date)
    for index in range(start_index, end_index + 1, 3):
        date = _month_date(index)
        symptoms, regimes = _evaluation(engine, symptom_config, regime_config, date, 3, primary_threshold)
        history_rows.append({
            "date": date,
            "classification": regimes["classification"],
            "primaryRegimeId": regimes["primaryRegime"]["id"],
            "primaryRegime": regimes["primaryRegime"]["name"],
            "secondaryRegimeId": regimes["secondaryRegime"]["id"],
            "confidence": regimes["confidence"],
            "coverage": regimes["coverage"],
            "scores": {item["id"]: item["score"] for item in regimes["allRegimeScores"]},
            "activeSymptoms": [item["id"] for item in symptoms if item["status"] == "active"],
        })
    classified = [row for row in history_rows if row["classification"] != "Unclassified"]
    same_transitions = sum(history_rows[index]["primaryRegimeId"] == history_rows[index - 1]["primaryRegimeId"] for index in range(1, len(history_rows)))
    durations = []
    if history_rows:
        run = 1
        for index in range(1, len(history_rows)):
            if history_rows[index]["primaryRegimeId"] == history_rows[index - 1]["primaryRegimeId"]:
                run += 1
            else:
                durations.append(run)
                run = 1
        durations.append(run)
    control_rows = [row for row in history_rows if "2003-01-01" <= row["date"] <= "2005-12-01" or "2017-01-01" <= row["date"] <= "2019-12-01"]
    event_rows = [row for row in history_rows if "2007-01-01" <= row["date"] <= "2009-06-01" or "2020-02-01" <= row["date"] <= "2023-12-01"]
    stress_ids = {"B", "C", "D", "E", "F", "G"}
    threshold_history_sensitivity = {primary_threshold: {"classificationChangeRate": 0.0}}
    baseline_labels = [row["classification"] for row in history_rows]
    for threshold_key in symptom_config["settings"]["thresholdSets"]:
        if threshold_key == primary_threshold:
            continue
        alternate_labels = []
        for row in history_rows:
            _, alternate = _evaluation(engine, symptom_config, regime_config, row["date"], 3, threshold_key)
            alternate_labels.append(alternate["classification"])
        threshold_history_sensitivity[threshold_key] = {
            "classificationChangeRate": sum(left != right for left, right in zip(baseline_labels, alternate_labels)) / len(history_rows) if history_rows else None
        }
    validation = {
        "method": "walk_forward_latest_vintage",
        "start": history_rows[0]["date"] if history_rows else None,
        "end": history_rows[-1]["date"] if history_rows else None,
        "observations": len(history_rows),
        "unclassifiedRate": 1.0 - len(classified) / len(history_rows) if history_rows else None,
        "transitionStability": same_transitions / max(1, len(history_rows) - 1),
        "meanRegimeDurationQuarters": sum(durations) / len(durations) if durations else None,
        "controlPeriodStressFlagRate": sum(row["classification"] != "Unclassified" and row["primaryRegimeId"] in stress_ids for row in control_rows) / len(control_rows) if control_rows else None,
        "eventPeriodMissRate": sum(row["classification"] == "Unclassified" or row["primaryRegimeId"] not in stress_ids for row in event_rows) / len(event_rows) if event_rows else None,
        "falsePositiveRate": None,
        "falseNegativeRate": None,
        "classificationRevisionFrequency": None,
        "thresholdSensitivity": threshold_history_sensitivity,
        "limitations": ["No independently labelled monthly regime truth set exists, so formal false-positive and false-negative rates remain unavailable. Control-period stress flags and event-period misses are descriptive substitutes, not ground truth.", "Latest-vintage walk-forward evaluation prevents future observations from entering percentile calculations but does not recreate historical publication vintages.", "Classification revision frequency and revised-data sensitivity require real-time vintage histories that are not yet available for every required series."],
        "methodComparison": {
            "transparentRuleClassifier": "primary_public_result",
            "simpleStatisticalClassifier": "not_promoted_without_independent_regime_labels",
            "unsupervisedHiddenState": "not_promoted; future robustness research only"
        },
    }
    current = {
        "schemaVersion": 1,
        "scope": SCOPE,
        "classificationDate": nowcast_date,
        "asOfDate": generated_at,
        "provisionalClassification": {**nowcast_clock, **nowcast_regimes},
        "confirmedClassification": {**confirmed_clock, **confirmed_regimes},
        "primaryRegime": nowcast_regimes["primaryRegime"],
        "secondaryRegime": nowcast_regimes["secondaryRegime"],
        "confidence": nowcast_regimes["confidence"],
        "evidenceCoverage": nowcast_regimes["coverage"],
        "allRegimeScores": nowcast_regimes["allRegimeScores"],
        "activeSymptoms": [item for item in nowcast_symptoms if item["status"] == "active"],
        "emergingSymptoms": [item for item in nowcast_symptoms if item["status"] == "emerging"],
        "fadingSymptoms": [item for item in nowcast_symptoms if item["status"] == "fading"],
        "supportingIndicators": nowcast_regimes["primaryRegime"]["supportingEvidence"],
        "conflictingIndicators": nowcast_regimes["primaryRegime"]["conflictingEvidence"],
        "staleIndicators": nowcast_clock["staleIndicators"],
        "missingIndicators": nowcast_clock["missingIndicators"],
        "historicalAnalogues": analogues,
        "ruleVersion": {"symptoms": symptom_config["version"], "regimes": regime_config["version"]},
        "dataVintageWarning": nowcast_clock["dataVintageWarning"],
        "monthlyPersistence": {
            "consecutiveUpdates": monthly_persistence,
            "requiredUpdates": required_monthly_persistence,
            "confirmationStatus": "persistent_candidate" if monthly_persistence >= required_monthly_persistence else "new_candidate",
            "note": "The monthly result remains a provisional nowcast even when its leading candidate persists. The quarterly clock is the confirmed state.",
        },
        "exceptionalTransition": exceptional_transition,
    }
    symptom_output = {
        "schemaVersion": 1, "scope": SCOPE, "generationDate": generated_at, "clock": nowcast_clock,
        "thresholdSensitivity": sensitivities, "evaluations": nowcast_symptoms,
    }
    regime_scores = {
        "schemaVersion": 1, "scope": SCOPE, "generationDate": generated_at, "classificationDate": nowcast_date,
        "scores": nowcast_regimes["allRegimeScores"], "decision": {key: nowcast_regimes[key] for key in ("classification", "confidence", "coverage", "margin", "decisionRules")},
        "sensitivity": {key: {"classification": value["classification"], "topScore": value["topScore"]} for key, value in sensitivities.items()},
    }
    regime_history = {"schemaVersion": 1, "scope": SCOPE, "frequency": "quarterly", "generatedAt": generated_at, "rows": history_rows, "validation": validation}

    controls = [
        {"episode": "2003-2005 ordinary expansion control", "start": "2003-01", "end": "2005-12", "initiating_conditions": "Non-event control period", "schema_status": "quantitative control period"},
        {"episode": "2017-2019 ordinary late-cycle control", "start": "2017-01", "end": "2019-12", "initiating_conditions": "Non-event control period", "schema_status": "quantitative control period"},
    ]
    expanded_episodes: list[Row] = []
    symptom_by_date_cache: dict[str, list[dict[str, Any]]] = {}
    for episode in [*episodes, *controls]:
        start = f"{episode['start']}-01" if len(str(episode.get("start"))) == 7 else str(episode.get("start"))
        end = f"{episode['end']}-01" if len(str(episode.get("end"))) == 7 else str(episode.get("end"))
        dates = [_month_date(index) for index in range(_month_index(start), _month_index(end) + 1)]
        activation: dict[str, str] = {}
        fading: dict[str, str] = {}
        coverages = []
        for date in dates:
            if date not in symptom_by_date_cache:
                symptom_by_date_cache[date], _ = _evaluation(engine, symptom_config, regime_config, date, 1, primary_threshold)
            for item in symptom_by_date_cache[date]:
                coverages.append(float(item["coverage"]))
                if item["status"] in {"active", "emerging"} and item["id"] not in activation:
                    activation[item["id"]] = date
                if item["status"] == "fading" and item["id"] not in fading:
                    fading[item["id"]] = date
        episode_history = [row for row in history_rows if start <= row["date"] <= end]
        sequence = []
        for row in episode_history:
            label = str(row["classification"])
            if not sequence or sequence[-1] != label:
                sequence.append(label)
        expanded_episodes.append({
            **episode,
            "monthly_or_quarterly_turning_points": "monthly indicators; quarterly regime sequence",
            "regime_sequence": " -> ".join(sequence) or "Insufficient data",
            "symptom_activation_dates": json.dumps(activation, sort_keys=True),
            "symptom_fading_dates": json.dumps(fading, sort_keys=True),
            "oil_price_peak": _turning_point(engine, "real_WTI_YoY", start, end, "max"),
            "inflation_peak": _turning_point(engine, "energy_CPI_YoY", start, end, "max"),
            "output_slowdown": _turning_point(engine, "Industrial_production_YoY", start, end, "min"),
            "labour_deterioration": _turning_point(engine, "unemployment_rate", start, end, "max"),
            "recovery_date": next((row["date"] for row in history_rows if episode_history and row["date"] > end and row["primaryRegimeId"] in {"H", "A"}), None),
            "classification_confidence": "moderate" if episode_history else "low",
            "available_data_coverage": sum(coverages) / len(coverages) if coverages else 0.0,
        })
    return current, symptom_output, regime_scores, regime_history, expanded_episodes
