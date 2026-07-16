from __future__ import annotations

from pathlib import Path

from oil_model.classification import IndicatorEngine, _latest_confirmed_quarter, build_classification_outputs, classification_indicators


def indicator(field: str, values: list[tuple[str, float]], frequency: str = "monthly") -> dict[str, object]:
    return {
        "id": field.lower().replace("_", "-"),
        "field": field,
        "label": field,
        "unit": "percent",
        "frequency": frequency,
        "confidenceLevel": "high",
        "latest": {"date": values[-1][0], "value": values[-1][1]},
        "observations": [{"date": date, "value": value} for date, value in values],
    }


def test_historical_percentile_does_not_use_future_observations() -> None:
    settings = {"monthlyMaximumAgeMonths": 6, "quarterlyMaximumAgeMonths": 9}
    base = indicator("series", [("2020-01-01", 1.0), ("2020-02-01", 2.0)])
    with_future = indicator("series", [("2020-01-01", 1.0), ("2020-02-01", 2.0), ("2021-01-01", 1000.0)])
    base_point = IndicatorEngine([base], settings).point("series", "2020-02-01")
    future_point = IndicatorEngine([with_future], settings).point("series", "2020-02-01")
    assert base_point is not None and future_point is not None
    assert base_point["historicalPercentile"] == future_point["historicalPercentile"]


def test_confirmed_quarter_never_uses_an_unfinished_quarter() -> None:
    history = [(f"2024-{month:02d}-01", float(month)) for month in range(1, 8)]
    engine = IndicatorEngine([indicator("series", history)], {"monthlyMaximumAgeMonths": 6, "quarterlyMaximumAgeMonths": 9})
    assert _latest_confirmed_quarter(engine, {"series"}, 0.70) == "2024-06-01"


def test_classifier_returns_unclassified_when_required_evidence_is_missing() -> None:
    sparse = indicator("CI_zscore", [("2024-01-01", 0.0), ("2024-02-01", 0.1)])
    current, symptoms, scores, history, episodes = build_classification_outputs(Path("."), [sparse], [])
    assert current["provisionalClassification"]["classification"] == "Unclassified"
    assert all(item["status"] == "insufficient_data" for item in symptoms["evaluations"])
    assert scores["decision"]["coverage"] < 0.70
    assert history["validation"]["method"] == "walk_forward_latest_vintage"
    assert episodes


def test_quarterly_classifier_uses_actual_source_dates(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw" / "fred"
    raw.mkdir(parents=True)
    (raw / "GDPC1.csv").write_text("observation_date,GDPC1\n2024-01-01,100\n2024-04-01,101\n", encoding="utf-8")
    carried = indicator("Real_GDP_growth", [("2024-01-01", 1.0), ("2024-02-01", 1.1), ("2024-03-01", 1.2), ("2024-04-01", 1.3)], "quarterly")
    filtered = classification_indicators(tmp_path, [carried])[0]
    assert [row["date"] for row in filtered["observations"]] == ["2024-01-01", "2024-04-01"]
    assert filtered["latest"]["date"] == "2024-04-01"
