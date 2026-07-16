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
    topics = evidence.get("topics", {})
    routes: dict[str, Any] = {}
    for route, topic_id in rules["routes"].items():
        if topic_id not in topics:
            raise ValueError(f"Presentation route {route} references missing evidence topic {topic_id}")
        topic = topics[topic_id]
        dates = _topic_dates(topic)
        routes[route] = {
            "route": route,
            "evidenceTopic": topic_id,
            "interpretation": topic["interpretation"],
            "confidence": topic["confidence"],
            "coverage": topic["coverage"],
            "scope": topic.get("scope"),
            "oldestObservationDate": dates[0] if dates else None,
            "newestObservationDate": dates[-1] if dates else None,
            "evidenceCounts": {status: len(topic.get(status, [])) for status in ("supporting", "mixed", "contradicting", "insufficient")},
            "provenance": ["website/public/generated/evidence-summary.json"],
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
            {"file": "website/public/generated/evidence-summary.json", "sha256": _hash(evidence_path)},
        ],
    }
    (generated / "presentation-manifest.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return payload
