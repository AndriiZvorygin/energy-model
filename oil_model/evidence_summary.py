from __future__ import annotations

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


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _indicator_maps(generated: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, Any]] = {}
    files: dict[str, dict[str, Any]] = {}
    for manifest_path, prefix in ((generated / "manifest.json", ""), (generated / "canada" / "manifest.json", "canada/")):
        manifest = _read(manifest_path)
        for entry in manifest.get("indicators", []):
            relative = f"{prefix}{entry['file']}"
            path = generated / relative
            if not path.exists():
                continue
            indicator = _read(path)
            record = {"file": relative, "payload": indicator}
            output[str(indicator.get("field", ""))] = record
            output[str(indicator.get("id", ""))] = record
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


def _topic(topic: str, interpretation: str, confidence: str, coverage: float | None, rows: list[dict[str, Any]], scope: str | None = None) -> dict[str, Any]:
    rows = _dedupe(rows)
    return {
        "topic": topic, "interpretation": interpretation, "confidence": confidence, "coverage": coverage, "scope": scope,
        "supporting": [row for row in rows if row["status"] == "supporting"],
        "mixed": [row for row in rows if row["status"] == "mixed"],
        "contradicting": [row for row in rows if row["status"] == "contradicting"],
        "insufficient": [row for row in rows if row["status"] == "insufficient"],
    }


def _regime_topic(key: str, classification: dict[str, Any], primary_key: str, secondary_key: str, lookup: dict[str, dict[str, Any]], *, interpretation: str, coverage: float, confidence: str) -> dict[str, Any]:
    primary = classification[primary_key]
    rows = [_condition_row(row, "supporting" if row.get("available", True) else "insufficient", lookup, "Supporting evidence") for row in primary.get("supportingEvidence", [])]
    rows += [_condition_row(row, "contradicting" if row.get("available", True) else "insufficient", lookup, "Conflicting evidence") for row in primary.get("conflictingEvidence", [])]
    named = {row["label"] for row in rows}
    rows += [_condition_row(row, "mixed" if row.get("available", True) else "insufficient", lookup, "Other evaluated evidence") for row in primary.get("indicatorEvidence", []) if row.get("label") not in named]
    secondary = classification[secondary_key]
    rows += [_condition_row(row, "mixed" if row.get("available", True) else "insufficient", lookup, f"Evidence for secondary candidate: {secondary['name']}") for row in secondary.get("supportingEvidence", []) if row.get("label") not in named]
    return _topic(key, interpretation, confidence, coverage, rows, classification.get("scope"))


def _symptom_topic(prefix: str, symptom: dict[str, Any], lookup: dict[str, dict[str, Any]], scope: str) -> dict[str, Any]:
    rows = []
    for condition in symptom.get("requiredConditionResults", []):
        status = "insufficient" if not condition.get("available") else "supporting" if condition.get("met") else "contradicting"
        rows.append(_condition_row(condition, status, lookup, "Required evidence"))
    for condition in symptom.get("confirmingEvidence", []):
        status = "insufficient" if not condition.get("available") else "supporting" if condition.get("met") else "mixed"
        rows.append(_condition_row(condition, status, lookup, "Confirming evidence"))
    for condition in symptom.get("conflictingEvidence", []):
        status = "insufficient" if not condition.get("available") else "contradicting" if condition.get("met") else "mixed"
        rows.append(_condition_row(condition, status, lookup, "Conflicting evidence"))
    rows += [_condition_row(condition, "insufficient", lookup, "Missing evidence") for condition in symptom.get("missingEvidence", [])]
    status = str(symptom.get("statusLabel") or symptom.get("status", "")).replace("_", " ")
    return _topic(f"{prefix}_{symptom['id']}", f"Why this symptom is {status.lower()}", symptom.get("confidence", "low"), symptom.get("coverage"), rows, scope)


def _indicator_row(indicator_id: str, status: str, lookup: dict[str, dict[str, Any]], group: str) -> dict[str, Any] | None:
    record = lookup.get(indicator_id)
    if not record:
        return None
    indicator = record["payload"]
    return {
        "indicator": indicator.get("field"), "label": indicator.get("label"), "status": status,
        "reason": STATUS_TEXT[status] + " " + str(indicator.get("interpretation", "Interpret using the published direction metadata.")),
        "chart": record["file"], "indicatorFile": record["file"], "group": group,
        "value": indicator.get("latest", {}).get("value"), "unit": indicator.get("unit"),
        "historicalPercentile": indicator.get("latest", {}).get("historicalPercentile"),
        "direction": indicator.get("latest", {}).get("momentum"), "sourceDate": indicator.get("latest", {}).get("sourceDate"),
        "calculation": indicator.get("calculation", {}).get("formula"), "limitations": indicator.get("limitations", []),
    }


def _affordability_topic(key: str, title: str, groups: dict[str, list[str]], lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for group, ids in groups.items():
        for indicator_id in ids:
            record = lookup.get(indicator_id)
            if not record:
                rows.append({"indicator": indicator_id, "label": indicator_id.replace("-", " ").title(), "status": "insufficient", "reason": STATUS_TEXT["insufficient"], "chart": None, "indicatorFile": None, "group": group, "value": None, "unit": None, "historicalPercentile": None, "direction": None, "sourceDate": None, "calculation": None, "limitations": []})
                continue
            label = record["payload"].get("interpretationLabel")
            status = "supporting" if label == "Stressful" else "contradicting" if label == "Supportive" else "mixed"
            row = _indicator_row(indicator_id, status, lookup, group)
            if row:
                rows.append(row)
    support = sum(row["status"] == "supporting" for row in rows)
    contradiction = sum(row["status"] == "contradicting" for row in rows)
    interpretation = f"{title} evidence is mixed across costs and purchasing power" if support and contradiction else f"{title} pressure is present but not broad-based" if support else f"{title} evidence remains mixed or context-dependent"
    available = sum(row["status"] != "insufficient" for row in rows)
    return _topic(key, interpretation, "moderate" if available == len(rows) else "low", available / len(rows) if rows else 0, rows, "Canadian household affordability with global commodity context")


def write_evidence_summary(root: Path) -> dict[str, Any]:
    generated = root / "website" / "public" / "generated"
    lookup, _ = _indicator_maps(generated)
    us = _read(generated / "current-classification.json")
    canada = _read(generated / "canada" / "current-classification.json")
    us_symptoms = _read(generated / "symptom-evaluations.json")
    canada_symptoms = _read(generated / "canada" / "symptom-evaluations.json")
    topics: dict[str, Any] = {}
    topics["current_state_us"] = _regime_topic("current_state_us", us, "primaryRegime", "secondaryRegime", lookup, interpretation=us["provisionalClassification"]["classification"], coverage=us["evidenceCoverage"], confidence=us["confidence"])
    topics["regimes_us"] = {**topics["current_state_us"], "topic": "regimes_us"}
    topics["current_state_canada"] = _regime_topic("current_state_canada", canada, "primaryState", "secondaryState", lookup, interpretation=canada["status"], coverage=canada["coverage"], confidence=canada["confidence"])
    topics["regimes_canada"] = {**topics["current_state_canada"], "topic": "regimes_canada"}
    topics["canada"] = {**topics["current_state_canada"], "topic": "canada", "interpretation": canada["summary"]}
    for symptom in us_symptoms["evaluations"]:
        topics[f"symptom_us_{symptom['id']}"] = _symptom_topic("symptom_us", symptom, lookup, us_symptoms["scope"])
    for symptom in canada_symptoms["evaluations"]:
        topics[f"symptom_canada_{symptom['id']}"] = _symptom_topic("symptom_canada", symptom, lookup, canada_symptoms["scope"])
    symptom_rows = []
    for symptom in us_symptoms["evaluations"]:
        if symptom["status"] not in {"active", "emerging", "fading"}:
            continue
        status = "supporting" if symptom["status"] in {"active", "emerging"} else "mixed"
        symptom_rows.append({"indicator": symptom["id"], "label": symptom["name"], "status": status, "reason": STATUS_TEXT[status] + f" The published symptom status is {symptom['status'].replace('_', ' ')} at a score of {100 * symptom['score']:.0f}%.", "chart": None, "indicatorFile": None, "group": "Symptom status", "value": symptom["score"], "unit": "score, 0-1", "historicalPercentile": None, "direction": symptom["status"], "sourceDate": symptom["evaluationDate"], "calculation": "Version-controlled symptom rule", "limitations": symptom.get("alternativeExplanations", [])})
    topics["symptoms_us"] = _topic("symptoms_us", "Current documented symptom balance", us_symptoms["clock"].get("confidence", us["confidence"]), us_symptoms["clock"]["coverage"], symptom_rows, us_symptoms["scope"])
    canada_symptom_rows = []
    for symptom in canada_symptoms["evaluations"]:
        if symptom["status"] not in {"active", "emerging", "fading"}:
            continue
        status = "supporting" if symptom["status"] in {"active", "emerging"} else "mixed"
        canada_symptom_rows.append({"indicator": symptom["id"], "label": symptom["name"], "status": status, "reason": STATUS_TEXT[status] + f" The published symptom status is {symptom['status'].replace('_', ' ')}.", "chart": None, "indicatorFile": None, "group": "Symptom status", "value": symptom["score"], "unit": "score, 0-1", "historicalPercentile": None, "direction": symptom["status"], "sourceDate": symptom["evaluationDate"], "calculation": "Version-controlled Canadian symptom rule", "limitations": symptom.get("limitations", [])})
    topics["symptoms_canada"] = _topic("symptoms_canada", "Current Canadian symptom balance", canada_symptoms["clock"]["confidence"], canada_symptoms["clock"]["requiredIndicatorAvailability"], canada_symptom_rows, canada_symptoms["scope"])
    topics["affordability"] = _affordability_topic("affordability", "Household affordability", {"Food": ["food-to-income", "food-to-wage"], "Housing": ["mortgage-interest-to-income", "rent-to-income", "nhpi-to-income"], "Energy": ["canada-energy-cpi-yoy", "canada-real-wti-cad-yoy"]}, lookup)
    topics["food"] = _affordability_topic("food", "Food affordability", {"Food": ["food-to-income", "grocery-to-income", "food-to-wage", "grocery-to-wage"], "Purchasing power": ["real-disposable-income-per-person", "real-wage-growth", "household-saving-rate"]}, lookup)
    topics["housing"] = _affordability_topic("housing", "Housing affordability", {"Asset affordability": ["nhpi-to-income", "residential-property-price-to-income"], "Current costs": ["rent-to-income", "shelter-to-income", "mortgage-interest-to-income"], "Purchasing power": ["real-disposable-income-per-person", "real-wage-growth"]}, lookup)
    payload = {"schemaVersion": 1, "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"), "statusDefinitions": STATUS_TEXT, "topics": topics}
    path = generated / "evidence-summary.json"
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return payload
