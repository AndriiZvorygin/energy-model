from __future__ import annotations

import unittest

from oil_model.website_data import _current_state_snapshot, _indicator_payload, _percentile, _quantile, validate_chart_dataset, validate_indicator_dataset


def dataset() -> dict:
    return {
        "schemaVersion": "1.1.0",
        "id": "fixture",
        "title": "Fixture",
        "description": "Fixture data",
        "plainLanguageSummary": "Fixture summary",
        "howToRead": "Read fixture values.",
        "calculation": {"formula": "x", "explanation": "Fixture calculation.", "example": "x=1"},
        "patternsToWatch": ["Pattern"],
        "limitations": ["Limitation"],
        "sourceNotes": ["Fixture source"],
        "transformation": {"type": "raw", "referenceStart": "2020-01-01", "referenceEnd": "2020-02-01", "mean": None, "standardDeviation": None},
        "frequency": "monthly",
        "dateRange": {"start": "2020-01-01", "end": "2020-02-01"},
        "series": [{"key": "value", "label": "Value", "unit": "percent", "source": "Fixture", "status": "derived", "defaultVisible": True, "finalObservationDate": "2020-02-01"}],
        "observations": [{"date": "2020-01-01", "value": None}, {"date": "2020-02-01", "value": 1.0}],
        "methodology": {},
        "generatedAt": "2026-01-01T00:00:00+00:00",
        "evidenceLabel": "Contextual indicator",
    }


class WebsiteDataTests(unittest.TestCase):
    def test_schema_accepts_explicit_null_missing_values(self) -> None:
        validate_chart_dataset(dataset())

    def test_schema_rejects_duplicate_or_unordered_dates(self) -> None:
        duplicate = dataset()
        duplicate["observations"].append({"date": "2020-02-01", "value": 2.0})
        with self.assertRaisesRegex(ValueError, "duplicate dates"):
            validate_chart_dataset(duplicate)
        unordered = dataset()
        unordered["observations"] = list(reversed(unordered["observations"]))
        with self.assertRaisesRegex(ValueError, "not ordered"):
            validate_chart_dataset(unordered)

    def test_schema_rejects_missing_units_and_non_numeric_values(self) -> None:
        missing_unit = dataset()
        del missing_unit["series"][0]["unit"]
        with self.assertRaisesRegex(ValueError, "missing unit"):
            validate_chart_dataset(missing_unit)
        invalid_value = dataset()
        invalid_value["observations"][1]["value"] = "1.0"
        with self.assertRaisesRegex(ValueError, "non-numeric"):
            validate_chart_dataset(invalid_value)

    def test_percentile_and_historical_ranges_are_stable(self) -> None:
        self.assertEqual(_quantile([1.0, 2.0, 3.0, 4.0], 0.5), 2.5)
        self.assertEqual(_percentile([1.0, 2.0, 3.0, 4.0], 4.0), 87.5)

    def test_indicator_schema_preserves_nulls_and_latest_context(self) -> None:
        current = {"indicator_id": "Industrial_production_YoY", "indicator": "Industrial production growth", "layer": "Production", "update_frequency": "monthly", "interpretation": "Rising is generally supportive.", "confirming_indicators": "Manufacturing; GDP", "conflicting_indicators": "Energy burden", "confidence_level": "medium", "evidence_label": "Contextual indicator"}
        catalogue = {"indicator": "Industrial production growth", "unit": "percent", "source": "FRED INDPRO", "status": "derived", "exact_definition": "Year-over-year industrial production growth.", "data_quality_limitations": "Latest data may be revised.", "alternative_explanations": "Sector mix."}
        rows = [
            {"month": "2024-01", "Industrial_production_YoY": 1.0},
            {"month": "2024-02", "Industrial_production_YoY": None},
            {"month": "2025-01", "Industrial_production_YoY": 2.0},
        ]
        payload = _indicator_payload(current, catalogue, rows, "2026-01-01T00:00:00+00:00")
        validate_indicator_dataset(payload)
        self.assertIsNone(payload["observations"][1]["value"])
        self.assertEqual(payload["latest"]["date"], "2025-01-01")
        self.assertEqual(payload["latest"]["oneYearChange"], 1.0)
        self.assertEqual(payload["interpretationDirection"], "higher-generally-supportive")

    def test_current_state_snapshot_groups_and_orders_pipeline_evidence(self) -> None:
        def indicator(identifier: str, label: str, classification: str, percentile: float, date: str) -> dict:
            return {"id": identifier, "field": identifier, "label": label, "layer": "Fixture", "interpretationLabel": classification, "latest": {"date": date, "historicalPercentile": percentile}}

        snapshot = _current_state_snapshot([
            indicator("ordinary", "Ordinary", "Mixed", 52.0, "2026-03-01"),
            indicator("stress", "Stress", "Stressful", 5.0, "2026-05-01"),
            indicator("support", "Support", "Supportive", 90.0, "2026-04-01"),
        ], "2026-06-15T12:00:00+00:00")

        self.assertEqual(snapshot["latestObservationDate"], "2026-05-01")
        self.assertEqual(snapshot["oldestLatestObservationDate"], "2026-03-01")
        self.assertEqual(snapshot["indicatorOrder"], ["stress", "support", "ordinary"])
        self.assertEqual([row["id"] for row in snapshot["groups"]["stressful"]], ["stress"])
        self.assertEqual(snapshot["groups"]["supportive"][0]["anomalyScore"], 40.0)


if __name__ == "__main__":
    unittest.main()
