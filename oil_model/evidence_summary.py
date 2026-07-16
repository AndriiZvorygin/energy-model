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


def evidence_key(geography: str, topic: str) -> str:
    return f"{geography}:{topic}"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _topic(geography: str, topic: str, interpretation: str, confidence: str, coverage: float | None, rows: list[dict[str, Any]], scope: str | None = None) -> dict[str, Any]:
    rows = _dedupe(rows)
    return {
        "geography": geography, "topic": topic, "evidenceKey": evidence_key(geography, topic),
        "interpretation": interpretation, "confidence": confidence, "coverage": coverage, "scope": scope,
        "supporting": [row for row in rows if row["status"] == "supporting"],
        "mixed": [row for row in rows if row["status"] == "mixed"],
        "contradicting": [row for row in rows if row["status"] == "contradicting"],
        "insufficient": [row for row in rows if row["status"] == "insufficient"],
    }


class EvidenceRefinery:
    def __init__(self, root: Path):
        self.root = root
        self.generated = root / "website" / "public" / "generated"
        self.rules = _read(root / "config" / "evidence_topics.json")
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
        }

    def _indicator_groups(self, geography: str, topic: str, geography_rule: dict[str, Any], topic_rule: dict[str, Any]) -> dict[str, Any]:
        rows = []
        for group, ids in topic_rule["groups"].items():
            for indicator_id in ids:
                record = self.lookup.get(indicator_id)
                if not record:
                    rows.append({"indicator": indicator_id, "label": indicator_id.replace("-", " ").title(), "status": "insufficient", "reason": STATUS_TEXT["insufficient"], "chart": None, "indicatorFile": None, "group": group, "value": None, "unit": None, "historicalPercentile": None, "direction": None, "sourceDate": None, "calculation": None, "limitations": []})
                    continue
                label = record["payload"].get("interpretationLabel")
                status = "supporting" if label == "Stressful" else "contradicting" if label == "Supportive" else "mixed"
                row = self._indicator_row(indicator_id, status, group)
                if row:
                    rows.append(row)
        support = sum(row["status"] == "supporting" for row in rows)
        contradiction = sum(row["status"] == "contradicting" for row in rows)
        title = topic_rule["title"]
        interpretation = f"{title} evidence is mixed across costs and purchasing power" if support and contradiction else f"{title} pressure is present but not broad-based" if support else f"{title} evidence remains mixed or context-dependent"
        available = sum(row["status"] != "insufficient" for row in rows)
        return _topic(geography, topic, interpretation, "moderate" if available == len(rows) else "low", available / len(rows) if rows else 0, rows, topic_rule.get("scope") or geography_rule["scope"])

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
