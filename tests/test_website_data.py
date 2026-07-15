from __future__ import annotations

import unittest

from oil_model.website_data import validate_chart_dataset


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


if __name__ == "__main__":
    unittest.main()
