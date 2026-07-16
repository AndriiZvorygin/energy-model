from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _topic_dates(topic: dict[str, Any]) -> list[str]:
    dates = []
    for status in ("supporting", "mixed", "contradicting", "insufficient"):
        dates.extend(str(row["sourceDate"]) for row in topic.get(status, []) if row.get("sourceDate"))
    return sorted(set(dates))


def write_presentation_contract(root: Path) -> dict[str, Any]:
    generated = root / "website" / "public" / "generated"
    config_path = root / "config" / "presentation_rules.json"
    evidence_path = generated / "evidence-summary.json"
    rules = _read(config_path)
    evidence = _read(evidence_path)
    summaries = evidence.get("evidence", {})
    routes: dict[str, Any] = {}
    for route, mapping in rules["routes"].items():
        geography = mapping["geography"]
        topic = mapping["topic"]
        key = f"{geography}:{topic}"
        if key not in summaries:
            raise ValueError(f"Presentation route {route} references missing evidence key {key}")
        summary = summaries[key]
        dates = _topic_dates(summary)
        routes[route] = {
            "route": route,
            "geography": geography,
            "topic": topic,
            "evidenceKey": key,
            "interpretation": summary["interpretation"],
            "confidence": summary["confidence"],
            "coverage": summary["coverage"],
            "scope": summary.get("scope"),
            "oldestObservationDate": dates[0] if dates else None,
            "newestObservationDate": dates[-1] if dates else None,
            "evidenceCounts": {status: len(summary.get(status, [])) for status in ("supporting", "mixed", "contradicting", "insufficient")},
            "provenance": [
                {"file": "website/public/generated/evidence-summary.json", "evidenceKey": key},
                {"file": "config/evidence_topics.json"},
                {"file": "config/absolute_affordability.json"},
                {"file": "config/presentation_rules.json"},
            ],
        }
    payload = {
        "schemaVersion": rules["schemaVersion"],
        "refineryVersion": rules["refineryVersion"],
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "regenerationCommand": "python -m oil_model.pipeline --root . --refresh",
        "policy": rules["policy"],
        "routes": routes,
        "inputs": [
            {"file": "config/presentation_rules.json", "sha256": _hash(config_path)},
            {"file": "config/evidence_topics.json", "sha256": _hash(root / "config" / "evidence_topics.json")},
            {"file": "config/absolute_affordability.json", "sha256": _hash(root / "config" / "absolute_affordability.json")},
            {"file": "website/public/generated/evidence-summary.json", "sha256": _hash(evidence_path)},
        ],
    }
    (generated / "presentation-manifest.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return payload
