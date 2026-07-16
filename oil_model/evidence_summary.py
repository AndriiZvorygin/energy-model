from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATUS_TEXT = {
    "supporting": "The indicator is consistent with this interpretation.",
    "mixed": "The indicator provides partial or ambiguous evidence.",
    "contradicting": "The indicator moves against this interpretation.",
    "insufficient": "The available data cannot evaluate this indicator.",
}

ABSOLUTE_STATUSES = {"affordable", "pressured", "unaffordable", "severe-shortfall", "unresolved", "insufficient"}
DIRECTIONS = {"worsening", "stable", "easing", "unclear"}


def evidence_key(geography: str, topic: str) -> str:
    return f"{geography}:{topic}"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _preferred_mbm_base(year: int) -> str:
    if year >= 2020:
        return "2023 base"
    if year >= 2015:
        return "2018 base"
    if year >= 2006:
        return "2008 base"
    return "2000 base"


def _national_distribution_history(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, str]]] = {}
    for row in rows:
        if row.get("scope") != "Canada national distribution" or row.get("income_group") == "Total deciles":
            continue
        grouped.setdefault((int(row["year"]), row["threshold_base"]), []).append(row)
    output = []
    for year in sorted({key[0] for key in grouped}):
        base = _preferred_mbm_base(year)
        current = grouped.get((year, base), [])
        if len(current) != 10:
            continue
        ratios = {row["income_group"]: float(row["income_relative_to_basic_needs"]) for row in current}
        values = list(ratios.values())
        output.append({
            "year": year,
            "thresholdBase": base,
            "populationBelow75Percent": sum(value < 0.75 for value in values) / 10,
            "populationBelowBasicNeeds": sum(value < 1.0 for value in values) / 10,
            "populationFromBasicNeedsToAffordableBuffer": sum(1.0 <= value < 1.25 for value in values) / 10,
            "populationAtOrAboveAffordableBuffer": sum(value >= 1.25 for value in values) / 10,
            "populationBelowAffordableBuffer": sum(value < 1.25 for value in values) / 10,
            "medianAffordabilityRatio": ratios.get("Fifth decile"),
            "lowerDecileAffordabilityRatios": {
                "lowest": ratios.get("Lowest decile"),
                "second": ratios.get("Second decile"),
                "third": ratios.get("Third decile"),
            },
        })
    return output


def _change(history: list[dict[str, Any]], years: int, field: str) -> float | None:
    latest = history[-1]
    prior = next((row for row in history if row["year"] == latest["year"] - years), None)
    if not prior:
        return None
    return float(latest[field]) - float(prior[field])


def _distribution_direction(history: list[dict[str, Any]]) -> str:
    changes = [
        _change(history, years, field)
        for years in (1, 3, 5)
        for field in ("populationBelowBasicNeeds", "populationBelowAffordableBuffer")
    ]
    available = [value for value in changes if value is not None]
    if not available:
        return "unclear"
    tolerance = 1e-9
    if all(abs(value) <= tolerance for value in available):
        return "stable"
    if any(value > tolerance for value in available) and not any(value < -tolerance for value in available):
        return "worsening"
    if any(value < -tolerance for value in available) and not any(value > tolerance for value in available):
        return "easing"
    return "unclear"


def _value(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        current = current[part]
    return current


def _indicator_maps(generated: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, Any]] = {}
    files: dict[str, dict[str, Any]] = {}
    manifests = [
        (generated / "manifest.json", ""),
        (generated / "canada" / "manifest.json", "canada/"),
        (generated / "global" / "manifest.json", "global/"),
        (generated / "us" / "manifest.json", "us/"),
    ]
    for manifest_path, prefix in manifests:
        if not manifest_path.exists():
            continue
        manifest = _read(manifest_path)
        for entry in manifest.get("indicators", []):
            relative = f"{prefix}{entry['file']}"
            path = generated / relative
            if not path.exists():
                continue
            indicator = _read(path)
            record = {"file": relative, "payload": indicator}
            for identifier in (indicator.get("field"), indicator.get("id")):
                if identifier:
                    output[str(identifier)] = record
            files[relative] = record
    return output, files


def _condition_row(condition: dict[str, Any], status: str, lookup: dict[str, dict[str, Any]], group: str) -> dict[str, Any]:
    record = lookup.get(str(condition.get("indicatorId") or condition.get("indicator") or ""))
    value = condition.get("value")
    detail = f" {condition.get('label', 'This indicator')} is evaluated using {str(condition.get('transformation', 'the published transformation')).replace('_', ' ')}"
    if value is not None:
        detail += f" at {float(value):.2f}{' ' + str(condition.get('unit')) if condition.get('unit') else ''}"
    detail += "."
    return {
        "indicator": condition.get("indicator"), "label": condition.get("label"), "status": status,
        "reason": STATUS_TEXT[status] + detail, "chart": record["file"] if record else None,
        "indicatorFile": record["file"] if record else None, "group": group,
        "value": value, "unit": condition.get("unit"), "historicalPercentile": condition.get("historicalPercentile"),
        "direction": condition.get("expectedDirection"), "sourceDate": condition.get("sourceDate"),
        "calculation": f"{condition.get('transformation', 'published condition')}; expected direction {condition.get('expectedDirection', 'documented in rule')}",
        "limitations": [],
    }


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rank = {"supporting": 3, "contradicting": 3, "mixed": 2, "insufficient": 1}
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = f"{row.get('group', '')}:{row.get('label') or row.get('indicator')}"
        if key not in selected or rank[row["status"]] > rank[selected[key]["status"]]:
            selected[key] = row
    return list(selected.values())


def _topic(geography: str, topic: str, interpretation: str, confidence: str, coverage: float | None, rows: list[dict[str, Any]], scope: str | None = None, **extra: Any) -> dict[str, Any]:
    rows = _dedupe(rows)
    return {
        "geography": geography, "topic": topic, "evidenceKey": evidence_key(geography, topic),
        "interpretation": interpretation, "confidence": confidence, "coverage": coverage, "scope": scope,
        "supporting": [row for row in rows if row["status"] == "supporting"],
        "mixed": [row for row in rows if row["status"] == "mixed"],
        "contradicting": [row for row in rows if row["status"] == "contradicting"],
        "insufficient": [row for row in rows if row["status"] == "insufficient"],
        **extra,
    }


class EvidenceRefinery:
    def __init__(self, root: Path):
        self.root = root
        self.generated = root / "website" / "public" / "generated"
        self.rules = _read(root / "config" / "evidence_topics.json")
        self.absolute_rules = _read(root / "config" / "absolute_affordability.json")
        self.lookup, self.files = _indicator_maps(self.generated)

    def generate(self, geography: str, topic: str) -> dict[str, Any]:
        geography_rule = self.rules["geographies"].get(geography)
        if not geography_rule:
            raise ValueError(f"Unknown evidence geography: {geography}")
        topic_rule = self._topic_rule(topic, geography_rule)
        evaluator = topic_rule["evaluator"]
        if evaluator == "regime":
            return self._regime(geography, topic, geography_rule, topic_rule)
        if evaluator == "symptom-aggregate":
            return self._symptom_aggregate(geography, topic, geography_rule)
        if evaluator == "symptom-detail":
            return self._symptom_detail(geography, topic, geography_rule)
        if evaluator == "indicator-groups":
            return self._indicator_groups(geography, topic, geography_rule, topic_rule)
        if evaluator == "indicator-state":
            return self._indicator_state(geography, topic, geography_rule)
        raise ValueError(f"Unsupported evidence evaluator: {evaluator}")

    def _topic_rule(self, topic: str, geography_rule: dict[str, Any]) -> dict[str, Any]:
        direct = self.rules["topics"].get(topic)
        if direct:
            return {**direct, **geography_rule.get("topicOverrides", {}).get(topic, {})}
        if topic.startswith("symptom/"):
            return self.rules["topics"]["symptom/*"]
        raise ValueError(f"Unknown evidence topic: {topic}")

    def _regime(self, geography: str, topic: str, geography_rule: dict[str, Any], topic_rule: dict[str, Any]) -> dict[str, Any]:
        settings = geography_rule.get("classification")
        if not settings:
            raise ValueError(f"Geography {geography} has no regime classifier")
        classification = _read(self.generated / settings["file"])
        primary = classification[settings["primaryKey"]]
        secondary = classification[settings["secondaryKey"]]
        rows = [_condition_row(row, "supporting" if row.get("available", True) else "insufficient", self.lookup, "Supporting evidence") for row in primary.get("supportingEvidence", [])]
        rows += [_condition_row(row, "contradicting" if row.get("available", True) else "insufficient", self.lookup, "Conflicting evidence") for row in primary.get("conflictingEvidence", [])]
        named = {row["label"] for row in rows}
        rows += [_condition_row(row, "mixed" if row.get("available", True) else "insufficient", self.lookup, "Other evaluated evidence") for row in primary.get("indicatorEvidence", []) if row.get("label") not in named]
        rows += [_condition_row(row, "mixed" if row.get("available", True) else "insufficient", self.lookup, f"Evidence for secondary candidate: {secondary['name']}") for row in secondary.get("supportingEvidence", []) if row.get("label") not in named]
        interpretation_path = settings["overviewInterpretationPath"] if topic_rule["interpretation"] == "overview" else settings["currentInterpretationPath"]
        return _topic(geography, topic, str(_value(classification, interpretation_path)), str(_value(classification, settings["confidencePath"])), float(_value(classification, settings["coveragePath"])), rows, classification.get("scope") or geography_rule["scope"])

    def _symptoms(self, geography_rule: dict[str, Any]) -> dict[str, Any]:
        path = geography_rule.get("symptomsFile")
        if not path:
            raise ValueError("This geography has no symptom evaluator")
        return _read(self.generated / path)

    def _symptom_aggregate(self, geography: str, topic: str, geography_rule: dict[str, Any]) -> dict[str, Any]:
        symptoms = self._symptoms(geography_rule)
        rows = []
        for symptom in symptoms["evaluations"]:
            if symptom["status"] not in {"active", "emerging", "fading"}:
                continue
            status = "supporting" if symptom["status"] in {"active", "emerging"} else "mixed"
            score_text = f" at a score of {100 * symptom['score']:.0f}%." if geography_rule.get("symptomReasonIncludesScore") else "."
            rows.append({
                "indicator": symptom["id"], "label": symptom["name"], "status": status,
                "reason": STATUS_TEXT[status] + f" The published symptom status is {symptom['status'].replace('_', ' ')}" + score_text,
                "chart": None, "indicatorFile": None, "group": "Symptom status", "value": symptom["score"], "unit": "score, 0-1",
                "historicalPercentile": None, "direction": symptom["status"], "sourceDate": symptom["evaluationDate"],
                "calculation": geography_rule["symptomCalculation"], "limitations": symptom.get(geography_rule["symptomLimitationsField"], []),
            })
        clock = symptoms["clock"]
        confidence = clock.get("confidence") or "low"
        coverage = clock.get("coverage", clock.get("requiredIndicatorAvailability"))
        return _topic(geography, topic, geography_rule["symptomInterpretation"], confidence, coverage, rows, symptoms["scope"])

    def _symptom_detail(self, geography: str, topic: str, geography_rule: dict[str, Any]) -> dict[str, Any]:
        symptom_id = topic.split("/", 1)[1]
        symptoms = self._symptoms(geography_rule)
        symptom = next((item for item in symptoms["evaluations"] if item["id"] == symptom_id), None)
        if not symptom:
            raise ValueError(f"Unknown {geography} symptom topic: {symptom_id}")
        rows = []
        for condition in symptom.get("requiredConditionResults", []):
            status = "insufficient" if not condition.get("available") else "supporting" if condition.get("met") else "contradicting"
            rows.append(_condition_row(condition, status, self.lookup, "Required evidence"))
        for condition in symptom.get("confirmingEvidence", []):
            status = "insufficient" if not condition.get("available") else "supporting" if condition.get("met") else "mixed"
            rows.append(_condition_row(condition, status, self.lookup, "Confirming evidence"))
        for condition in symptom.get("conflictingEvidence", []):
            status = "insufficient" if not condition.get("available") else "contradicting" if condition.get("met") else "mixed"
            rows.append(_condition_row(condition, status, self.lookup, "Conflicting evidence"))
        rows += [_condition_row(condition, "insufficient", self.lookup, "Missing evidence") for condition in symptom.get("missingEvidence", [])]
        status = str(symptom.get("statusLabel") or symptom.get("status", "")).replace("_", " ")
        return _topic(geography, topic, f"Why this symptom is {status.lower()}", symptom.get("confidence", "low"), symptom.get("coverage"), rows, symptoms["scope"])

    def _indicator_row(self, indicator_id: str, status: str, group: str) -> dict[str, Any] | None:
        record = self.lookup.get(indicator_id)
        if not record:
            return None
        indicator = record["payload"]
        return {
            "indicator": indicator.get("field") or indicator.get("id"), "label": indicator.get("label"), "status": status,
            "reason": STATUS_TEXT[status] + " " + str(indicator.get("interpretation", "Interpret using the published direction metadata.")),
            "chart": record["file"], "indicatorFile": record["file"], "group": group,
            "value": indicator.get("latest", {}).get("value"), "unit": indicator.get("unit"),
            "historicalPercentile": indicator.get("latest", {}).get("historicalPercentile"),
            "direction": indicator.get("latest", {}).get("momentum"), "sourceDate": indicator.get("latest", {}).get("sourceDate"),
            "calculation": indicator.get("calculation", {}).get("formula"), "limitations": indicator.get("limitations", []),
            "absoluteStatus": None,
        }

    @staticmethod
    def _predicate(metric: float | None, operator: str, expected: float) -> bool:
        if metric is None:
            return False
        operations = {
            "lt": lambda: metric < expected,
            "lte": lambda: metric <= expected,
            "gt": lambda: metric > expected,
            "gte": lambda: metric >= expected,
            "eq": lambda: metric == expected,
        }
        if operator not in operations:
            raise ValueError(f"Unsupported affordability threshold operator: {operator}")
        return operations[operator]()

    def _direction(self, indicator_ids: list[str]) -> tuple[str, list[dict[str, Any]]]:
        votes: list[str] = []
        details: list[dict[str, Any]] = []
        for indicator_id in indicator_ids:
            record = self.lookup.get(indicator_id)
            if not record:
                details.append({"indicator": indicator_id, "available": False, "direction": "unclear"})
                continue
            latest = record["payload"].get("latest", {})
            momentum = str(latest.get("momentum") or "").lower()
            vote = "worsening" if momentum == "rising" else "easing" if momentum == "falling" else "stable" if momentum in {"stable", "flat"} else "unclear"
            if vote != "unclear":
                votes.append(vote)
            details.append({
                "indicator": indicator_id,
                "label": record["payload"].get("label"),
                "available": True,
                "direction": vote,
                "momentum": momentum or None,
                "sourceDate": latest.get("sourceDate"),
            })
        worsening = votes.count("worsening")
        easing = votes.count("easing")
        stable = votes.count("stable")
        if worsening > easing and worsening >= stable:
            return "worsening", details
        if easing > worsening and easing >= stable:
            return "easing", details
        if stable > worsening and stable > easing:
            return "stable", details
        return "unclear", details

    def _historical_status(self, metrics: dict[str, float], rules: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
        for rule in rules:
            matched = bool(rule.get("otherwise"))
            if "any" in rule:
                matched = any(self._predicate(metrics.get(item["metric"]), item["operator"], float(item["value"])) for item in rule["any"])
            if "all" in rule:
                matched = all(self._predicate(metrics.get(item["metric"]), item["operator"], float(item["value"])) for item in rule["all"])
            if matched:
                return str(rule["status"]), rule
        return "insufficient", None

    def _historical_affordability(
        self,
        geography: str,
        geography_rule: dict[str, Any],
        current_status: str,
        current_direction: str,
    ) -> dict[str, Any] | None:
        settings = geography_rule.get("historicalAffordability")
        if not settings:
            return None
        dataset_path = self.root / settings["dataset"]
        validation_path = self.root / settings["validationDataset"]
        rows = _csv(dataset_path)
        validation = _csv(validation_path)
        provenance = [
            {"file": settings["dataset"], "role": "historical affordability input"},
            {"file": settings["validationDataset"], "role": "hardship and observed-cost validation"},
        ]
        limitations = list(settings.get("limitations", []))

        if geography == "canada":
            history = _national_distribution_history(rows)
            if not history:
                return {
                    "latestYear": None, "absoluteStatus": "insufficient", "direction": "unclear",
                    "populationBelowBasicNeeds": None, "populationBelowAffordableBuffer": None,
                    "oneYearChange": None, "threeYearChange": None, "fiveYearChange": None,
                    "historicalSeries": [], "geographyLevel": settings["geographyLevel"],
                    "limitations": [*limitations, "No complete national decile distribution was available."], "provenance": provenance,
                }
            latest = history[-1]
            metrics = {
                "populationBelow75Percent": latest["populationBelow75Percent"],
                "populationBelowBasicNeeds": latest["populationBelowBasicNeeds"],
                "populationBelowAffordableBuffer": latest["populationBelowAffordableBuffer"],
            }
            status, selected_rule = self._historical_status(metrics, settings["statusRules"])
            return {
                "latestYear": latest["year"],
                "absoluteStatus": status,
                "direction": _distribution_direction(history),
                "populationBelow75Percent": latest["populationBelow75Percent"],
                "populationBelowBasicNeeds": latest["populationBelowBasicNeeds"],
                "populationBelowAffordableBuffer": latest["populationBelowAffordableBuffer"],
                "populationFromBasicNeedsToAffordableBuffer": latest["populationFromBasicNeedsToAffordableBuffer"],
                "populationAtOrAboveAffordableBuffer": latest["populationAtOrAboveAffordableBuffer"],
                "medianAffordabilityRatio": latest["medianAffordabilityRatio"],
                "lowerDecileAffordabilityRatios": latest["lowerDecileAffordabilityRatios"],
                "oneYearChange": _change(history, 1, "populationBelowBasicNeeds"),
                "threeYearChange": _change(history, 3, "populationBelowBasicNeeds"),
                "fiveYearChange": _change(history, 5, "populationBelowBasicNeeds"),
                "changeDetails": {
                    f"{years}Year": {
                        "populationBelowBasicNeeds": _change(history, years, "populationBelowBasicNeeds"),
                        "populationBelowAffordableBuffer": _change(history, years, "populationBelowAffordableBuffer"),
                    }
                    for years in (1, 3, 5)
                },
                "historicalSeries": history,
                "geographyLevel": settings["geographyLevel"],
                "classificationRule": selected_rule,
                "limitations": limitations,
                "provenance": provenance,
            }

        regional = [row for row in rows if row.get("scope") == settings["scope"]]
        selected: dict[int, list[dict[str, str]]] = {}
        for year in sorted({int(row["year"]) for row in regional}):
            base = _preferred_mbm_base(year)
            current = [row for row in regional if int(row["year"]) == year and row["threshold_base"] == base]
            if current:
                selected[year] = current
        history = [
            {
                "year": year,
                "thresholdBase": _preferred_mbm_base(year),
                "medianHouseholdTypeRatios": {
                    row["household_type"]: _float(row["income_relative_to_basic_needs"])
                    for row in current
                },
                "contextOnly": True,
            }
            for year, current in sorted(selected.items())
        ]
        validation_rows = [
            {
                "geography": row["geography"], "year": int(row["year"]), "measure": row["measure"],
                "value": _float(row["value"]), "unit": row["unit"], "source": row["source"],
            }
            for row in validation
            if row.get("geography") in {"Owen Sound rental market", "Grey Bruce"}
        ]
        return {
            "latestYear": history[-1]["year"] if history else None,
            "absoluteStatus": current_status,
            "direction": current_direction,
            "populationBelowBasicNeeds": None,
            "populationBelowAffordableBuffer": None,
            "oneYearChange": None,
            "threeYearChange": None,
            "fiveYearChange": None,
            "historicalSeries": history,
            "validationSeries": validation_rows,
            "geographyLevel": settings["geographyLevel"],
            "limitations": limitations,
            "provenance": provenance,
            "contextOnly": True,
        }

    def _matched_case_evaluations(self, cases: list[dict[str, Any]], topic_rule: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float]]:
        if not topic_rule.get("caseStatusRules"):
            return cases, {}
        evaluated: list[dict[str, Any]] = []
        status_weights = {status: 0.0 for status in ("affordable", "pressured", "unaffordable", "severe-shortfall")}
        total_weight = 0.0
        for case in cases:
            income = float(case["income"])
            metrics = {
                "incomeToBasicNeeds": income / float(case["basicNeedsCost"]) if case.get("basicNeedsCost") else None,
                "foodShare": float(case["foodCost"]) / income if case.get("foodCost") else None,
                "renterHousingShare": float(case["renterHousingCost"]) / income if case.get("renterHousingCost") else None,
                "ownerHousingShare": float(case["ownerHousingCost"]) / income if case.get("ownerHousingCost") else None,
                "foodAndRenterHousingShare": (float(case.get("foodCost") or 0) + float(case.get("renterHousingCost") or 0)) / income,
                "newerFoodShareOfStaleIncome": float(case["newerFoodCost"]) / income if case.get("newerFoodCost") else None,
                "newerRenterHousingShareOfStaleIncome": float(case["newerRenterHousingCost"]) / income if case.get("newerRenterHousingCost") else None,
            }
            status = "insufficient"
            selected_rule = None
            for rule in topic_rule.get("caseStatusRules", []):
                matched = bool(rule.get("otherwise"))
                if "any" in rule:
                    matched = any(self._predicate(metrics.get(item["metric"]), item["operator"], float(item["value"])) for item in rule["any"])
                if "all" in rule:
                    matched = all(self._predicate(metrics.get(item["metric"]), item["operator"], float(item["value"])) for item in rule["all"])
                if matched:
                    status = rule["status"]
                    selected_rule = rule
                    break
            weight = float(case.get("householdCount") or 0)
            if status in status_weights:
                status_weights[status] += weight
                total_weight += weight
            evaluated.append({**case, "status": status, "metrics": metrics, "classificationRule": selected_rule, "classificationBasis": topic_rule.get("caseStatusBasis")})
        shares = {f"{status}Share": value / total_weight if total_weight else 0.0 for status, value in status_weights.items()}
        shares["unaffordableOrWorseShare"] = shares["unaffordableShare"] + shares["severe-shortfallShare"]
        shares["nonAffordableShare"] = shares["pressuredShare"] + shares["unaffordableOrWorseShare"]
        shares["evaluatedHouseholdCount"] = total_weight
        return evaluated, shares

    def _absolute_affordability(self, geography: str, topic: str) -> dict[str, Any]:
        geography_rule = self.absolute_rules["geographies"].get(geography)
        if not geography_rule or geography_rule.get("unsupportedReason"):
            reason = (geography_rule or {}).get("unsupportedReason", "No configured absolute household affordability measure is available.")
            return {
                "absoluteStatus": "insufficient", "direction": "unclear", "householdType": None,
                "income": None, "essentialCost": None, "costShare": None, "residualIncome": None,
                "thresholdUsed": None, "components": {}, "directionEvidence": [],
                "limitations": [reason], "missingEvidence": [reason], "distributionMeasures": [],
                "headlineInputs": [], "representativeBudgets": [], "matchedHouseholdCases": [],
            }
        topic_rule = geography_rule.get("topics", {}).get(topic)
        measures = geography_rule.get("distributionMeasures", {})
        headline_ids = topic_rule.get("headlineMeasures", []) if topic_rule else []
        headline_inputs = [{"id": identifier, **measures[identifier]} for identifier in headline_ids if identifier in measures]
        available_inputs = [item for item in headline_inputs if item.get("value") is not None]
        missing = [f"{item['label']} is not yet integrated." for item in headline_inputs if item.get("value") is None]
        matched_cases = geography_rule.get("matchedHouseholdCases", [])
        matched_cases_complete = bool(matched_cases) and all(item.get("status") == "evaluated" for item in matched_cases)
        case_evaluations, case_metrics = self._matched_case_evaluations(matched_cases, topic_rule or {})

        if not topic_rule or not available_inputs:
            status = "insufficient"
            selected_threshold = None
            missing.append(f"No population-distribution evidence is configured for {geography} {topic}.")
        elif topic_rule.get("requiresCompletedMatchedHouseholdCases") and not matched_cases_complete:
            status = "unresolved"
            selected_threshold = {
                "status": "unresolved",
                "definition": topic_rule["unresolvedReason"],
                "formula": "population hardship measures available AND matched household-type cases incomplete",
                "source": "Configured official distribution measures",
                "observationDate": geography_rule.get("observationDate"),
                "limitations": "Population hardship is measured, but a single absolute national budget verdict is not supportable yet.",
            }
            missing.append(topic_rule["unresolvedReason"])
        elif topic_rule.get("headlineMethod") == "matched-household-cases":
            status = "insufficient"
            selected_threshold = None
            for rule in topic_rule.get("aggregateStatusRules", []):
                matched = bool(rule.get("otherwise"))
                if "any" in rule:
                    matched = any(self._predicate(case_metrics.get(item["metric"]), item["operator"], float(item["value"])) for item in rule["any"])
                if "all" in rule:
                    matched = all(self._predicate(case_metrics.get(item["metric"]), item["operator"], float(item["value"])) for item in rule["all"])
                if matched:
                    status = rule["status"]
                    selected_threshold = {
                        **rule, "geography": geography,
                        "definition": f"Household-type-weighted rule for {topic}",
                        "formula": json.dumps({key: value for key, value in rule.items() if key != "status"}, sort_keys=True),
                        "source": "Project rule applied to matched official household-type incomes and basic-needs thresholds",
                        "observationDate": geography_rule.get("observationDate"),
                        "limitations": topic_rule.get("aggregateLimitations", "Household-type medians describe central cases, not the full within-type income distribution."),
                    }
                    break
        else:
            status = "insufficient"
            selected_threshold = None
            for rule in topic_rule.get("statusRules", []):
                matched = bool(rule.get("otherwise"))
                if "any" in rule:
                    matched = any(self._predicate(measures.get(item["measure"], {}).get("value"), item["operator"], float(item["value"])) for item in rule["any"])
                if "all" in rule:
                    matched = all(self._predicate(measures.get(item["measure"], {}).get("value"), item["operator"], float(item["value"])) for item in rule["all"])
                if matched:
                    status = rule["status"]
                    selected_threshold = {
                        **rule,
                        "geography": geography,
                        "definition": f"Population-distribution rule for national {topic}",
                        "formula": json.dumps({key: value for key, value in rule.items() if key != "status"}, sort_keys=True),
                        "source": "Project rule applied to configured official population hardship measures",
                        "observationDate": geography_rule.get("observationDate"),
                        "limitations": "Transparent project classification threshold; not an official national affordability verdict.",
                    }
                    break
        if status not in ABSOLUTE_STATUSES:
            raise ValueError(f"Invalid absolute affordability status: {status}")
        direction_override = topic_rule.get("directionOverride") if topic_rule else None
        if direction_override:
            direction = direction_override["value"]
            direction_evidence = direction_override.get("evidence", [])
        else:
            direction, direction_evidence = self._direction(topic_rule.get("directionIndicators", []) if topic_rule else [])
        if direction not in DIRECTIONS:
            raise ValueError(f"Invalid affordability direction: {direction}")
        historical = self._historical_affordability(geography, geography_rule, status, direction)
        historical_settings = geography_rule.get("historicalAffordability", {})
        if historical and historical_settings.get("headline") and historical["absoluteStatus"] != "insufficient":
            status = historical["absoluteStatus"]
            direction = historical["direction"]
            missing = [item for item in missing if item != topic_rule.get("unresolvedReason")]
            selected_threshold = {
                "status": status,
                "definition": "National distribution of family units across matched MBM affordability bands",
                "formula": "ten equal-weight income deciles classified by average after-tax income / applicable MBM basket",
                "source": "Historical affordability refinery input",
                "observationDate": f"{historical['latestYear']}-01-01",
                "limitations": "Decile-average approximation; see historicalAffordability.limitations and provenance.",
                "rule": historical.get("classificationRule"),
            }
            direction_evidence = [{
                "label": "Historical national affordability distribution",
                "available": True,
                "direction": direction,
                "sourceDate": f"{historical['latestYear']}-01-01",
            }]
        limitations = [item.get("limitations", "") for item in headline_inputs]
        if selected_threshold and selected_threshold.get("limitations"):
            limitations.append(selected_threshold["limitations"])
        return {
            "absoluteStatus": status,
            "direction": direction,
            "householdType": geography_rule.get("referencePopulation"),
            "referencePopulation": geography_rule.get("referencePopulation"),
            "assessmentLabel": geography_rule.get("assessmentLabel", "Absolute"),
            "observationDate": geography_rule.get("observationDate"),
            "income": geography_rule.get("descriptiveIncome"),
            "essentialCost": None,
            "costShare": None,
            "residualIncome": None,
            "incomeRemainingAfterHousing": None,
            "incomeRemainingAfterMeasuredEssentials": None,
            "thresholdUsed": {"classification": selected_threshold, "basicNeeds": None},
            "components": {},
            "distributionMeasures": list(measures.values()),
            "headlineInputs": headline_inputs,
            "contextEvidence": [item for item in geography_rule.get("contextEvidence", []) if topic in item.get("topics", [])],
            "representativeBudgets": geography_rule.get("representativeBudgets", []),
            "matchedHouseholdCases": case_evaluations,
            "matchedHouseholdSummary": case_metrics,
            "historicalAffordability": historical,
            "directionEvidence": direction_evidence,
            "limitations": [item for item in limitations if item],
            "missingEvidence": missing,
        }

    def _distribution_rows(self, assessment: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for measure in assessment.get("headlineInputs", []):
            value = measure.get("value")
            disposition = "supporting" if value is not None else "insufficient"
            reason = STATUS_TEXT[disposition]
            if value is not None:
                reason += f" {measure['label']} is {float(value) * 100:.1f}% of the published reference population."
            else:
                reason += f" {measure['label']} has not yet been integrated as a verified national estimate."
            rows.append({
                "indicator": measure["id"], "label": measure["label"], "status": disposition,
                "reason": reason, "chart": None, "indicatorFile": None, "group": "Population hardship evidence",
                "value": float(value) * 100 if value is not None else None, "unit": "% of population/households", "historicalPercentile": None, "direction": None,
                "sourceDate": measure.get("observationDate"), "source": measure.get("source"),
                "calculation": measure.get("definition"), "limitations": [measure.get("limitations", "")],
                "absoluteStatus": None,
            })
        return rows

    def _context_rows(self, assessment: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in assessment.get("contextEvidence", []):
            disposition = item.get("status", "mixed")
            rows.append({
                "indicator": item["id"], "label": item["label"], "status": disposition,
                "reason": STATUS_TEXT[disposition] + " " + item["reason"],
                "chart": None, "indicatorFile": None, "group": "Newer local context",
                "value": item.get("value"), "unit": item.get("unit"), "historicalPercentile": None,
                "direction": item.get("direction"), "sourceDate": item.get("observationDate"),
                "source": item.get("source"), "calculation": item.get("definition"),
                "limitations": [item.get("limitations", "")], "absoluteStatus": None,
            })
        return rows

    def _matched_case_rows(self, topic: str, assessment: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        headline_is_pressure = assessment["absoluteStatus"] in {"pressured", "unaffordable", "severe-shortfall"}
        for case in assessment.get("matchedHouseholdCases", []):
            if not case.get("metrics"):
                continue
            status = case.get("status")
            if status == "insufficient":
                disposition = "insufficient"
            elif (status == "affordable") == headline_is_pressure:
                disposition = "contradicting"
            elif status == "pressured":
                disposition = "supporting" if headline_is_pressure else "mixed"
            else:
                disposition = "supporting"
            ratio = case.get("metrics", {}).get("incomeToBasicNeeds")
            reason = STATUS_TEXT[disposition]
            basis = f", using {case['classificationBasis']}," if case.get("classificationBasis") else ""
            reason += f" The {case['householdType']} median case{basis} is classified {str(status).replace('-', ' ')}"
            if ratio is not None:
                reason += f" with income at {ratio:.2f} times its matched basic-needs threshold."
            else:
                reason += "."
            if case.get("newerFoodCost") and case.get("newerRenterHousingCost"):
                newer_share = (float(case["newerFoodCost"]) + float(case["newerRenterHousingCost"])) / float(case["income"])
                reason += f" For scale only, the newer regional food and rental references equal {newer_share * 100:.1f}% of the older 2020 median income; that mixed-year ratio does not determine status."
            rows.append({
                "indicator": case["id"], "label": case["householdType"], "status": disposition,
                "reason": reason, "chart": None, "indicatorFile": None, "group": "Matched household cases",
                "value": case.get("income"), "unit": case.get("unit"), "historicalPercentile": None,
                "direction": assessment.get("direction"), "sourceDate": case.get("observationDate"),
                "source": case.get("source"), "calculation": f"income / matched basic-needs cost; {topic} context publishes food and tenure-specific housing components separately",
                "limitations": [case.get("limitations", "")], "absoluteStatus": status,
            })
        return rows

    def _absolute_row(self, topic: str, assessment: dict[str, Any]) -> dict[str, Any]:
        status = assessment["absoluteStatus"]
        disposition = "insufficient" if status == "insufficient" else "mixed" if status == "unresolved" else "supporting"
        label = f"{assessment.get('assessmentLabel', 'Absolute')} {topic.replace('-', ' ')} assessment"
        cost = assessment.get("essentialCost") or {}
        reason = STATUS_TEXT[disposition]
        if status == "insufficient":
            reason += " " + " ".join(assessment.get("missingEvidence", []))
        elif status == "unresolved":
            reason += " Population hardship measures show pressure, but incomplete matched household-type budgets prevent a defensible national absolute verdict."
        else:
            reason += f" The configured population-distribution evidence is {status.replace('-', ' ')} and {assessment['direction']}."
        threshold = assessment.get("thresholdUsed") or {}
        classification = threshold.get("classification") or {}
        return {
            "indicator": f"absolute-{topic}", "label": label, "status": disposition, "reason": reason,
            "chart": None, "indicatorFile": None, "group": "Absolute affordability", "value": cost.get("value"),
            "unit": cost.get("unit"), "historicalPercentile": None, "direction": assessment["direction"],
            "absoluteStatus": status, "sourceDate": assessment.get("observationDate"),
            "source": cost.get("source"), "calculation": classification.get("formula"), "limitations": assessment.get("limitations", []),
        }

    def _indicator_groups(self, geography: str, topic: str, geography_rule: dict[str, Any], topic_rule: dict[str, Any]) -> dict[str, Any]:
        assessment = self._absolute_affordability(geography, topic)
        rows = [self._absolute_row(topic, assessment), *self._distribution_rows(assessment), *self._matched_case_rows(topic, assessment), *self._context_rows(assessment)]
        pressure_headline = assessment["absoluteStatus"] in {"pressured", "unaffordable", "severe-shortfall"}
        for group, ids in topic_rule["groups"].items():
            for indicator_id in ids:
                record = self.lookup.get(indicator_id)
                if not record:
                    rows.append({"indicator": indicator_id, "label": indicator_id.replace("-", " ").title(), "status": "insufficient", "reason": STATUS_TEXT["insufficient"], "chart": None, "indicatorFile": None, "group": group, "value": None, "unit": None, "historicalPercentile": None, "direction": None, "sourceDate": None, "calculation": None, "limitations": []})
                    continue
                label = record["payload"].get("interpretationLabel")
                if label == "Stressful":
                    status = "supporting" if pressure_headline else "contradicting"
                elif label == "Supportive":
                    status = "contradicting" if pressure_headline else "supporting"
                else:
                    status = "mixed"
                row = self._indicator_row(indicator_id, status, group)
                if row:
                    rows.append(row)
        title = topic_rule["title"]
        absolute_label = assessment["absoluteStatus"].replace("-", " ").capitalize()
        direction_label = assessment["direction"].replace("-", " ")
        interpretation = f"{absolute_label} · {direction_label}"
        available = sum(row["status"] != "insufficient" for row in rows)
        return _topic(
            geography, topic, interpretation, "low" if assessment["absoluteStatus"] in {"insufficient", "unresolved"} else "moderate",
            available / len(rows) if rows else 0, rows, topic_rule.get("scope") or geography_rule["scope"],
            absoluteStatus=assessment["absoluteStatus"], direction=assessment["direction"],
            householdType=assessment.get("householdType"), income=assessment.get("income"),
            essentialCost=assessment.get("essentialCost"), costShare=assessment.get("costShare"),
            residualIncome=assessment.get("residualIncome"), thresholdUsed=assessment.get("thresholdUsed"),
            referencePopulation=assessment.get("referencePopulation"), headlineInputs=assessment.get("headlineInputs"),
            historicalAffordability=assessment.get("historicalAffordability"),
            absoluteEvaluation=assessment,
        )

    def _indicator_state(self, geography: str, topic: str, geography_rule: dict[str, Any]) -> dict[str, Any]:
        allowed = set(geography_rule.get("indicatorGeographies", []))
        records = {record["file"]: record for record in self.lookup.values() if record["payload"].get("geography") in allowed}
        rows = []
        for record in records.values():
            indicator = record["payload"]
            label = indicator.get("interpretationLabel")
            status = "supporting" if label == "Supportive" else "contradicting" if label == "Stressful" else "mixed"
            row = self._indicator_row(str(indicator.get("id")), status, str(indicator.get("layer") or "Current indicators"))
            if row:
                rows.append(row)
        interpretation = f"{geography_rule['label']} indicators are assembled for geography-specific evaluation"
        return _topic(geography, topic, interpretation, "moderate" if rows else "low", 1.0 if rows else 0.0, rows, geography_rule["scope"])


def generate_evidence_summary(geography: str, topic: str, root: Path | str = ".") -> dict[str, Any]:
    return EvidenceRefinery(Path(root)).generate(geography, topic)


def _topic_audit(rules: dict[str, Any], generated: list[tuple[str, str]]) -> str:
    manual = [topic for topic, spec in rules["topics"].items() if spec["evaluator"] == "indicator-groups"]
    geography_fields = [name for name, spec in rules["geographies"].items() if spec.get("classification") or spec.get("symptomsFile") or spec.get("indicatorGeographies")]
    lines = [
        "# Evidence Topic Audit", "", "Evidence summaries use canonical `geography:topic` keys and one `generate_evidence_summary(geography, topic)` interface.", "",
        f"Generated geography/topic combinations: {len(generated)}.", "", "## Remaining Manually Named Topics", "",
        "The following analytical topic names and indicator groups remain explicitly configured because they express research semantics rather than route behavior:", "",
        *[f"- `{topic}`: indicator groups and component IDs are declared in `config/evidence_topics.json`." for topic in manual],
        "- `symptom/<rule-id>`: names and required evidence come from the jurisdiction symptom-rule files.", "- `overview`, `current-state`, `regimes`, and `symptoms`: canonical evaluator names shared across geographies.", "",
        "## Geography-Specific Configuration", "",
        *[f"- `{name}`: source namespace, classifier field names, symptom source, or indicator-geography filters are configured without route-specific code." for name in geography_fields],
        "", "Adding a future geography requires configuration and generated source data, not a new Python or React route branch.", "",
    ]
    return "\n".join(lines)


def write_evidence_summary(root: Path) -> dict[str, Any]:
    refinery = EvidenceRefinery(root)
    evidence: dict[str, Any] = {}
    generated_pairs: list[tuple[str, str]] = []
    for output in refinery.rules["outputs"]:
        geography = output["geography"]
        for topic in output["topics"]:
            summary = refinery.generate(geography, topic)
            evidence[summary["evidenceKey"]] = summary
            generated_pairs.append((geography, topic))
        symptoms_file = refinery.rules["geographies"][geography].get("symptomsFile")
        if symptoms_file:
            symptoms = _read(refinery.generated / symptoms_file)
            for symptom in symptoms["evaluations"]:
                topic = f"symptom/{symptom['id']}"
                summary = refinery.generate(geography, topic)
                evidence[summary["evidenceKey"]] = summary
                generated_pairs.append((geography, topic))
    payload = {"schemaVersion": 2, "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"), "statusDefinitions": STATUS_TEXT, "evidence": evidence}
    path = refinery.generated / "evidence-summary.json"
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (root / "analysis" / "evidence_topic_audit.md").write_text(_topic_audit(refinery.rules, generated_pairs), encoding="utf-8")
    return payload
