from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analysis import feature, rolling_predictions
from .storage import Row


SCHEMA_VERSION = "1.1.0"
EVIDENCE_LABELS = {
    "Validated relationship",
    "Supported historical pattern",
    "Contextual indicator",
    "Experimental proxy",
    "Scenario concept",
}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _iso_date(value: object) -> str:
    text = str(value)
    if len(text) == 7:
        return f"{text}-01"
    if len(text) == 10:
        return text
    raise ValueError(f"Website chart date must be YYYY-MM or YYYY-MM-DD, got {text!r}")


def _series(
    key: str,
    label: str,
    unit: str,
    source: str,
    status: str,
    default_visible: bool = True,
    frequency: str | None = None,
    color: str | None = None,
    transformations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "unit": unit,
        "source": source,
        "status": status,
        "defaultVisible": default_visible,
        "frequency": frequency,
        "color": color,
        "transformations": transformations or ["raw", "indexed", "zscore"],
    }


def _dataset(
    dataset_id: str,
    title: str,
    description: str,
    frequency: str,
    series: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    transformations: list[str],
    evidence_label: str,
    methodology: dict[str, Any],
    static_figure: str,
    generated_at: str,
    annotations: list[str] | None = None,
    details: dict[str, Any] | None = None,
    reference_period: tuple[str, str] = ("2007-01-01", "2019-12-01"),
) -> dict[str, Any]:
    observations = sorted(observations, key=lambda row: row["date"])
    present = [row for row in observations if any(row.get(item["key"]) is not None for item in series)]
    final_dates = {
        item["key"]: max((row["date"] for row in observations if row.get(item["key"]) is not None), default=None)
        for item in series
    }
    reference_start, reference_end = reference_period
    statistics: dict[str, dict[str, float | int | None]] = {}
    for item in series:
        values = [
            float(row[item["key"]])
            for row in observations
            if reference_start <= row["date"] <= reference_end and _number(row.get(item["key"])) is not None
        ]
        mean = sum(values) / len(values) if values else None
        std = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) if values and mean is not None else None
        statistics[item["key"]] = {"mean": mean, "standardDeviation": std, "n": len(values)}
    details = details or {}
    sources = list(dict.fromkeys(item["source"] for item in series))
    formula = str(methodology.get("formula", "Values are displayed at their documented observation frequency."))
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "id": dataset_id,
        "title": title,
        "description": description,
        "plainLanguageSummary": details.get("plainLanguageSummary", description),
        "howToRead": details.get("howToRead", "Compare direction, turning points, and sustained divergences. Use the tooltip for exact values and observation dates; visual alignment alone does not establish causation."),
        "calculation": details.get("calculation", {"formula": formula, "explanation": str(methodology.get("notes", "The chart uses the documented project transformation without changing the underlying observations.")), "example": "A value at date t uses only observations dated t or earlier unless the chart explicitly labels a visual shift."}),
        "patternsToWatch": details.get("patternsToWatch", ["Persistent co-movement across several observations", "Turning points or divergences that repeat across historical episodes"]),
        "limitations": details.get("limitations", [str(methodology.get("notes", "Correlation and visual alignment can reflect common macro factors, revisions, or measurement choices."))]),
        "sourceNotes": details.get("sourceNotes", sources),
        "transformation": {"type": "raw", "referenceStart": reference_start, "referenceEnd": reference_end, "mean": None, "standardDeviation": None, "statistics": statistics},
        "frequency": frequency,
        "dateRange": {"start": present[0]["date"] if present else None, "end": present[-1]["date"] if present else None},
        "series": [{**item, "finalObservationDate": final_dates[item["key"]]} for item in series],
        "observations": observations,
        "annotations": annotations or [],
        "availableTransformations": transformations,
        "evidenceLabel": evidence_label,
        "methodology": methodology,
        "staticFigure": static_figure,
        "generatedAt": generated_at,
    }
    validate_chart_dataset(result)
    return result


def validate_chart_dataset(dataset: dict[str, Any]) -> None:
    required = {"schemaVersion", "id", "title", "description", "plainLanguageSummary", "howToRead", "calculation", "patternsToWatch", "limitations", "sourceNotes", "transformation", "frequency", "dateRange", "series", "observations", "methodology", "generatedAt", "evidenceLabel"}
    missing = sorted(required - dataset.keys())
    if missing:
        raise ValueError(f"Chart dataset {dataset.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if dataset["evidenceLabel"] not in EVIDENCE_LABELS:
        raise ValueError(f"Invalid evidence label for {dataset['id']}: {dataset['evidenceLabel']}")
    for field in ("formula", "explanation", "example"):
        if not dataset["calculation"].get(field):
            raise ValueError(f"Chart dataset {dataset['id']} calculation is missing {field}")
    if not dataset["transformation"].get("referenceStart") or not dataset["transformation"].get("referenceEnd"):
        raise ValueError(f"Chart dataset {dataset['id']} is missing a fixed transformation reference period")
    keys = [item.get("key") for item in dataset["series"]]
    if not keys or len(keys) != len(set(keys)):
        raise ValueError(f"Chart dataset {dataset['id']} has missing or duplicate series keys")
    for item in dataset["series"]:
        for field in ("key", "label", "unit", "source", "status", "defaultVisible", "finalObservationDate"):
            if field not in item:
                raise ValueError(f"Series {item.get('key')} in {dataset['id']} is missing {field}")
    dates = [row.get("date") for row in dataset["observations"]]
    if any(not isinstance(date, str) or len(date) != 10 for date in dates):
        raise ValueError(f"Chart dataset {dataset['id']} contains a non-ISO date")
    if dates != sorted(dates):
        raise ValueError(f"Chart dataset {dataset['id']} dates are not ordered")
    if len(dates) != len(set(dates)):
        raise ValueError(f"Chart dataset {dataset['id']} contains duplicate dates")
    for row in dataset["observations"]:
        for key in keys:
            value = row.get(key)
            if value is not None and not isinstance(value, (int, float)):
                raise ValueError(f"Chart dataset {dataset['id']} has non-numeric value for {key} at {row['date']}")


def _observations(rows: list[Row], mapping: dict[str, str], date_field: str = "month") -> list[dict[str, Any]]:
    return [
        {"date": _iso_date(row[date_field]), **{output: _number(row.get(source)) for output, source in mapping.items()}}
        for row in rows
        if row.get(date_field)
    ]


def _quality_observations(rows: list[Row], indicators: list[str]) -> list[dict[str, Any]]:
    dates = sorted({str(row["date"]) for row in rows if row.get("indicator") in indicators})
    lookup = {(str(row["date"]), str(row["indicator"])): _number(row.get("value")) for row in rows}
    return [{"date": date, **{indicator: lookup.get((date, indicator)) for indicator in indicators}} for date in dates]


def _regimes() -> list[dict[str, Any]]:
    return [
        {"id": "financial_crisis_2008_2009", "label": "Financial crisis", "start": "2008-01-01", "end": "2009-12-01", "color": "#64748b"},
        {"id": "shale_regime_2014_2017", "label": "Shale adjustment", "start": "2014-01-01", "end": "2017-12-01", "color": "#0f766e"},
        {"id": "covid_2020_2021", "label": "Pandemic disruption", "start": "2020-01-01", "end": "2021-12-01", "color": "#7c3aed"},
        {"id": "war_spr_2022_2023", "label": "War / SPR regime", "start": "2022-01-01", "end": "2023-12-01", "color": "#be123c"},
    ]


def _events() -> list[dict[str, Any]]:
    return [
        {"id": "oil_embargo_1973", "name": "Oil embargo", "start": "1973-10-01", "end": "1974-03-01", "category": "oil supply shock", "explanation": "A physical supply disruption and policy response sharply raised oil costs.", "layers": ["physical energy", "affordability", "economic activity"]},
        {"id": "gulf_war_1990", "name": "Gulf War oil shock", "start": "1990-08-01", "end": "1991-02-01", "category": "oil supply shock", "explanation": "Geopolitical supply risk produced a short, sharp oil-price shock.", "layers": ["physical energy", "oil pricing", "affordability"]},
        {"id": "gfc_2008", "name": "Financial crisis and oil collapse", "start": "2008-07-01", "end": "2009-06-01", "category": "financial crisis", "explanation": "An oil-price peak was followed by financial crisis, demand destruction, and price collapse; the overlap does not identify a single cause.", "layers": ["financial conditions", "oil pricing", "economic activity", "labour"]},
        {"id": "shale_2014", "name": "Shale supply adjustment", "start": "2014-06-01", "end": "2016-02-01", "category": "price collapse", "explanation": "Supply growth and changing producer strategy contributed to a prolonged oil-price decline.", "layers": ["physical energy", "oil pricing", "investment"]},
        {"id": "covid_2020", "name": "Pandemic and futures dislocation", "start": "2020-03-01", "end": "2020-06-01", "category": "pandemic disruption", "explanation": "Mobility restrictions collapsed petroleum demand and disrupted futures-linked exposure.", "layers": ["energy demand", "oil pricing", "tradable exposure", "economic activity"]},
        {"id": "reopening_2021", "name": "Demand recovery", "start": "2021-02-01", "end": "2022-06-01", "category": "demand recovery", "explanation": "Reopening demand, constrained supply chains, and geopolitical stress lifted energy prices and burden.", "layers": ["energy demand", "physical energy", "affordability", "inflation"]},
    ]


def _recession_periods(rows: list[Row]) -> list[dict[str, Any]]:
    periods: list[dict[str, Any]] = []
    start: str | None = None
    previous: str | None = None
    for row in rows:
        month = str(row.get("month"))
        active = _number(row.get("recession_dummy")) == 1
        if active and start is None:
            start = month
        if start is not None and not active:
            periods.append({"id": f"recession_{start}", "label": "NBER recession", "start": _iso_date(start), "end": _iso_date(previous or start), "color": "#78716c"})
            start = None
        previous = month
    if start is not None:
        periods.append({"id": f"recession_{start}", "label": "NBER recession", "start": _iso_date(start), "end": _iso_date(previous or start), "color": "#78716c"})
    return periods


def write_website_chart_data(
    root: Path,
    rows: list[Row],
    lag_rows: list[Row],
    rolling_rows: list[Row],
    equity_lag_rows: list[Row],
    energy_rows: list[Row],
    system_rows: list[Row],
    output_quality_rows: list[Row],
    output_quality_correlations: list[Row],
) -> list[str]:
    out_dir = root / "website" / "public" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    regimes = _regimes()
    events = _events()
    locked_performance = next((row for row in rolling_rows if row.get("target") == "WTI_YoY" and row.get("model") == "gm2_only" and row.get("lag_months") == 5 and row.get("window_months") == 60 and row.get("sample") == "all"), {})

    oil_prices = _dataset(
        "oil-price-layers", "Oil price layers", "Benchmark, realised refiner cost, and investor-accessible oil exposure.", "monthly",
        [
            _series("WTI", "WTI", "USD per barrel", "FRED DCOILWTICO", "measured", color="#0f766e", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("Brent", "Brent", "USD per barrel", "FRED DCOILBRENTEU", "measured", color="#2563eb", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("RAC_composite", "RAC composite", "USD per barrel", "EIA R0000____3", "measured", color="#7c3aed", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("USO", "USO adjusted close", "USD per share", "Yahoo-compatible chart data", "measured", color="#d97706", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("real_WTI", "Real WTI", "CPI-base USD per barrel", "FRED WTI / CPIAUCSL", "derived", False, color="#15803d", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("real_Brent", "Real Brent", "CPI-base USD per barrel", "FRED Brent / CPIAUCSL", "derived", False, color="#1d4ed8", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
        ],
        _observations(rows, {"WTI": "WTI", "Brent": "Brent", "RAC_composite": "RAC_composite", "USO": "USO_month_end_adjusted_close", "real_WTI": "real_WTI", "real_Brent": "real_Brent"}),
        ["raw", "indexed", "yoy", "zscore", "pct_change"], "Contextual indicator",
        {"formula": "Raw monthly values. Transformations are calculated in-browser within each series; indexed = 100 at first visible observation.", "notes": "USO is a share price and must not be read on a barrel-price axis in raw mode.", "sources": ["FRED", "EIA", "Yahoo-compatible public chart data"]},
        "final_oil_price_layers_time_series.png", generated_at, [event["id"] for event in events],
    )

    gm2_lead = _dataset(
        "gm2-oil-lead", "GM2 leading oil momentum", "Global liquidity growth aligned with later oil-price momentum.", "monthly",
        [
            _series("GM2_YoY", "G4 GM2 YoY", "percent", "Project G4 GM2 aggregate", "derived", color="#d97706"),
            _series("WTI_YoY", "WTI YoY", "percent", "FRED DCOILWTICO", "derived", color="#0f766e"),
            _series("Brent_YoY", "Brent YoY", "percent", "FRED DCOILBRENTEU", "derived", color="#2563eb"),
            _series("RAC_composite_YoY", "RAC composite YoY", "percent", "EIA R0000____3", "derived", color="#7c3aed"),
        ],
        _observations(rows, {"GM2_YoY": "GM2_YoY", "WTI_YoY": "WTI_YoY", "Brent_YoY": "Brent_YoY", "RAC_composite_YoY": "RAC_composite_YoY"}),
        ["raw", "zscore"], "Validated relationship",
        {"formula": "Oil_YoY[t] compared with GM2_YoY[t-lag]. Positive lag means GM2 leads oil.", "lockedLag": 5, "peakSimpleCorrelationLag": 4, "testedLags": [0, 18], "lockedPerformance": {"windowMonths": 60, "rmse": locked_performance.get("rolling_rmse"), "mae": locked_performance.get("rolling_mae"), "r2": locked_performance.get("rolling_r2"), "n": locked_performance.get("n_predictions")}, "notes": "The simple-correlation peak is descriptive; lag 5 remains locked from rolling validation."},
        "final_gm2_leads_oil_time_series.png", generated_at, [event["id"] for event in events],
    )

    wti_pred = rolling_predictions(rows, "WTI_YoY", [feature("GM2_YoY", 5, "GM2_YoY_lag")], 60)
    brent_pred = rolling_predictions(rows, "Brent_YoY", [feature("GM2_YoY", 5, "GM2_YoY_lag")], 60)
    wti_residual = {month: float(actual - pred) for month, actual, pred in zip(wti_pred.get("months", []), wti_pred.get("actuals", []), wti_pred.get("preds", []))}
    brent_residual = {month: float(actual - pred) for month, actual, pred in zip(brent_pred.get("months", []), brent_pred.get("actuals", []), brent_pred.get("preds", []))}
    residual_observations = [
        {"date": _iso_date(row["month"]), "WTI_residual": wti_residual.get(str(row["month"])), "Brent_residual": brent_residual.get(str(row["month"])), "CI_zscore": _number(row.get("CI_zscore")), "USO_tracking_residual": _number(row.get("USO_tracking_residual"))}
        for row in rows
    ]
    residuals = _dataset(
        "oil-residual-ci", "Oil residual and physical state", "Deviations from the locked liquidity-implied path alongside comparative inventory and USO tracking.", "monthly",
        [
            _series("WTI_residual", "WTI model residual", "YoY percentage points", "Project rolling GM2 lag-5 model", "modelled", color="#0f766e"),
            _series("Brent_residual", "Brent model residual", "YoY percentage points", "Project rolling GM2 lag-5 model", "modelled", False, color="#2563eb"),
            _series("CI_zscore", "Comparative inventory z-score", "standard deviations", "Derived from EIA WCESTUS1", "derived", color="#be123c"),
            _series("USO_tracking_residual", "USO minus WTI YoY", "percentage points", "Yahoo-compatible data and FRED WTI", "derived", False, color="#7c3aed"),
        ], residual_observations, ["raw", "zscore"], "Validated relationship",
        {"formula": "Oil residual = actual Oil_YoY - rolling fitted(alpha + beta*GM2_YoY[t-5]); CI uses only the prior five same-month inventory observations.", "windowMonths": 60, "notes": "Different units are shown in synchronized panels in raw mode and may share an axis only after standardization."},
        "final_oil_residual_ci_time_series.png", generated_at, ["gfc_2008", "shale_2014", "covid_2020", "reopening_2021"],
    )

    quarterly = sorted([dict(row) for row in energy_rows if row.get("section") == "time_series" and row.get("frequency") == "quarterly" and row.get("month")], key=lambda row: str(row["month"]))
    for row in quarterly:
        year, month = map(int, str(row["month"]).split("-"))
        quarter = (month - 1) // 3
        values = [_number(item.get("Industrial_production_YoY")) for item in system_rows if int(str(item["month"])[:4]) == year and (int(str(item["month"])[5:7]) - 1) // 3 == quarter]
        available = [item for item in values if item is not None]
        row["Industrial_production_YoY"] = sum(available) / len(available) if available else None
    energy_gdp = _dataset(
        "energy-gdp", "Energy throughput and real activity", "Quarterly growth in total energy, petroleum consumption, real GDP, and industrial production.", "quarterly",
        [
            _series("Energy_consumption_growth", "Total energy consumption growth", "percent", "EIA MER T01.03", "derived", frequency="quarterly", color="#0f766e"),
            _series("Oil_consumption_growth", "Petroleum consumption growth", "percent", "EIA MER T01.03", "derived", frequency="quarterly", color="#d97706"),
            _series("Real_GDP_growth", "Real GDP growth", "percent", "FRED GDPC1", "derived", frequency="quarterly", color="#2563eb"),
            _series("Industrial_production_YoY", "Industrial production growth", "percent", "FRED INDPRO", "derived", frequency="quarterly", color="#7c3aed"),
        ],
        _observations(quarterly, {"Energy_consumption_growth": "Energy_consumption_growth", "Oil_consumption_growth": "Oil_consumption_growth", "Real_GDP_growth": "Real_GDP_growth", "Industrial_production_YoY": "Industrial_production_YoY"}),
        ["raw", "zscore"], "Supported historical pattern",
        {"formula": "Quarterly growth observations aligned to quarter dates.", "notes": "Monthly energy and industrial series are aggregated to quarter; GDP remains at its native quarterly frequency. No monthly interpolation is used."},
        "final_energy_gdp_time_series.png", generated_at, [event["id"] for event in events],
    )

    equities = _dataset(
        "oil-equities", "Oil and S&P 500", "Monthly return and year-over-year macro-cycle comparisons.", "monthly",
        [
            _series("SP500_return", "S&P 500 monthly return", "log percent", "FRED SP500", "derived", color="#475569"),
            _series("WTI_return", "WTI monthly return", "log percent", "FRED DCOILWTICO", "derived", color="#0f766e"),
            _series("Brent_return", "Brent monthly return", "log percent", "FRED DCOILBRENTEU", "derived", False, color="#2563eb"),
            _series("SP500_YoY", "S&P 500 YoY", "percent", "FRED SP500", "derived", False, color="#475569"),
            _series("WTI_YoY", "WTI YoY", "percent", "FRED DCOILWTICO", "derived", False, color="#0f766e"),
            _series("Brent_YoY", "Brent YoY", "percent", "FRED DCOILBRENTEU", "derived", False, color="#2563eb"),
        ],
        _observations(rows, {"SP500_return": "SP500_log_return_1m", "WTI_return": "WTI_log_return_1m", "Brent_return": "Brent_log_return_1m", "SP500_YoY": "SP500_YoY", "WTI_YoY": "WTI_YoY", "Brent_YoY": "Brent_YoY"}),
        ["raw", "zscore"], "Contextual indicator",
        {"formula": "Monthly log return = 100*ln(P[t]/P[t-1]); YoY = 100*(P[t]/P[t-12]-1).", "notes": "YoY lag patterns describe macro stress; monthly returns are more relevant to timing and remain mostly contemporaneous."},
        "sp500_vs_wti_yoy.png", generated_at, [event["id"] for event in events],
    )

    uso = _dataset(
        "uso-tracking", "USO and benchmark oil", "Tradable ETF exposure compared with WTI and Brent benchmarks.", "monthly",
        [
            _series("USO", "USO adjusted close", "USD per share", "Yahoo-compatible chart data", "measured", color="#d97706", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("WTI", "WTI", "USD per barrel", "FRED DCOILWTICO", "measured", color="#0f766e", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("Brent", "Brent", "USD per barrel", "FRED DCOILBRENTEU", "measured", color="#2563eb", transformations=["raw", "indexed", "yoy", "zscore", "pct_change"]),
            _series("USO_tracking_residual", "USO minus WTI YoY", "percentage points", "Project derived", "derived", False, color="#7c3aed"),
            _series("CI_zscore", "Comparative inventory z-score", "standard deviations", "Derived from EIA WCESTUS1", "derived", False, color="#be123c"),
        ],
        _observations(rows, {"USO": "USO_month_end_adjusted_close", "WTI": "WTI", "Brent": "Brent", "USO_tracking_residual": "USO_tracking_residual", "CI_zscore": "CI_zscore"}),
        ["raw", "indexed", "yoy", "zscore", "pct_change"], "Contextual indicator",
        {"formula": "USO tracking residual = USO_YoY - WTI_YoY.", "notes": "USO can diverge through roll yield, fees, tracking differences, and ETF structure. Raw USO and barrel prices are not placed on one axis."},
        "uso_vs_wti_yoy.png", generated_at, ["gfc_2008", "shale_2014", "covid_2020", "reopening_2021"],
    )

    headline_keys = ["GDPC1", "A939RX0Q048SBEA", "A261RX1Q020SBEA", "LB0000031Q020SBEA"]
    headline = _dataset(
        "output-quality-headline", "Headline measured output", "Real GDP, GDP per capita, gross domestic income, and final private domestic sales measure related but distinct parts of recorded production and income.", "quarterly",
        [
            _series("GDPC1", "Real GDP", "billions chained 2017 USD", "BEA via FRED GDPC1", "measured", color="#0f766e"),
            _series("A939RX0Q048SBEA", "Real GDP per capita", "chained 2017 USD per person", "BEA via FRED", "measured", color="#2563eb"),
            _series("A261RX1Q020SBEA", "Real gross domestic income", "billions chained 2017 USD", "BEA via FRED", "measured", False, color="#7c3aed"),
            _series("LB0000031Q020SBEA", "Real final private domestic sales", "billions chained 2017 USD", "BEA via FRED", "measured", False, color="#d97706"),
        ], _quality_observations(output_quality_rows, headline_keys), ["raw", "indexed", "zscore"], "Contextual indicator",
        {"formula": "Official inflation-adjusted BEA aggregates at quarterly frequency.", "notes": "GDP measures production rather than total wealth; per-capita and income measures answer different distributional and accounting questions."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-10-01"),
    )
    net_output_keys = ["real_gdp_annual", "A362RX1A020NBEA", "real_ndp_per_capita"]
    net_output = _dataset(
        "output-quality-net-output", "Gross and net output", "Official real net domestic product accounts for capital consumption; per-capita net output asks how much net production remains per resident.", "annual",
        [
            _series("real_gdp_annual", "Real GDP", "billions chained 2017 USD", "BEA GDPC1 annual average", "derived", color="#0f766e"),
            _series("A362RX1A020NBEA", "Official real NDP", "billions chained 2017 USD", "BEA via FRED A362RX1A020NBEA", "measured", color="#2563eb"),
            _series("real_ndp_per_capita", "Real NDP per capita", "chained 2017 USD per person", "BEA / Census project derivation", "derived", color="#d97706"),
        ], _quality_observations(output_quality_rows, net_output_keys), ["raw", "indexed", "zscore"], "Contextual indicator",
        {"formula": "Real NDP is the official BEA chained-dollar series; NDP per capita = real NDP / population.", "notes": "The project does not subtract chained-dollar GDP components because chained measures are not exactly additive."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-01-01"),
    )
    capacity_keys = ["W171RC1Q027SBEA", "A262RX1Q020SBEA", "INDPRO", "IPMAN", "TSIFRGHT"]
    capacity = _dataset(
        "output-quality-capacity", "Productive capacity and net investment", "Net investment, capital consumption, industrial production, manufacturing, and freight provide different views of productive capacity and material throughput.", "quarterly",
        [
            _series("W171RC1Q027SBEA", "Net domestic investment", "billions USD SAAR", "BEA via FRED", "measured", color="#d97706"),
            _series("A262RX1Q020SBEA", "Real capital consumption", "billions chained 2017 USD SAAR", "BEA via FRED", "measured", color="#be123c"),
            _series("INDPRO", "Industrial production", "index", "Federal Reserve via FRED", "measured", color="#0f766e"),
            _series("IPMAN", "Manufacturing output", "index", "Federal Reserve via FRED", "measured", False, color="#2563eb"),
            _series("TSIFRGHT", "Freight activity", "index", "BTS via FRED", "measured", False, color="#7c3aed"),
        ], _quality_observations(output_quality_rows, capacity_keys), ["raw", "indexed", "zscore"], "Supported historical pattern",
        {"formula": "Official investment and output series; monthly physical-output indexes are averaged within genuine quarters.", "notes": "Net investment is nominal while capital consumption is real, so raw mode separates units."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-10-01"),
    )
    household_keys = ["MEHOINUSA672N", "HouseholdCommand", "CXUSHELTERLB0101M", "CXUFOODTOTLLB0101M", "CXUUTILSLB0101M"]
    household = _dataset(
        "output-quality-household", "Household prosperity and essential costs", "The experimental household-command measure subtracts shelter, food, and utilities/fuels costs from real median household income while keeping every component visible.", "annual",
        [
            _series("MEHOINUSA672N", "Real median household income", "2024 USD", "Census via FRED", "measured", color="#0f766e"),
            _series("HouseholdCommand", "Experimental household command", "2024 USD", "Census/BLS project derivation", "experimental", color="#2563eb"),
            _series("CXUSHELTERLB0101M", "Shelter expenditure", "2024 USD per consumer unit", "BLS CE via FRED", "derived", False, color="#d97706"),
            _series("CXUFOODTOTLLB0101M", "Food expenditure", "2024 USD per consumer unit", "BLS CE via FRED", "derived", False, color="#7c3aed"),
            _series("CXUUTILSLB0101M", "Utilities, fuels, public services", "2024 USD per consumer unit", "BLS CE via FRED", "derived", False, color="#be123c"),
        ], _quality_observations(output_quality_rows, household_keys), ["raw", "indexed", "zscore"], "Experimental proxy",
        {"formula": "HouseholdCommand = real median household income - real shelter - real food - real utilities/fuels/public-services expenditure.", "notes": "This combines median income with average consumer-unit costs and is not an official disposable-income statistic."}, "", generated_at, [event["id"] for event in events], reference_period=("1990-01-01", "2019-01-01"),
    )
    financial_keys = ["VAPGDPFI", "VAPGDPRL", "TDSP", "private_debt_gdp", "DDDM01USA156NWDB"]
    financial = _dataset(
        "output-quality-financial", "Financialization and asset valuation", "Finance, insurance, real estate, debt service, leverage, and equity valuation are shown separately rather than collapsed into a judgmental score.", "quarterly",
        [
            _series("VAPGDPFI", "Finance and insurance value-added", "percent of GDP", "BEA via FRED", "measured", color="#0f766e"),
            _series("VAPGDPRL", "Real estate and rental value-added", "percent of GDP", "BEA via FRED", "measured", color="#2563eb"),
            _series("TDSP", "Household debt-service burden", "percent of disposable income", "Federal Reserve via FRED", "measured", color="#d97706"),
            _series("private_debt_gdp", "Household debt", "percent of GDP", "Federal Reserve / BEA project derivation", "derived", False, color="#be123c"),
            _series("DDDM01USA156NWDB", "Equity-market capitalization", "percent of GDP", "World Bank via FRED", "measured", False, frequency="annual", color="#7c3aed"),
        ], _quality_observations(output_quality_rows, financial_keys), ["raw", "indexed", "zscore"], "Contextual indicator",
        {"formula": "Value-added and balance-sheet measures retain their official definitions; household debt/GDP = CMDEBT / nominal GDP * 100.", "notes": "A larger financial or real-estate share is not, by itself, evidence of low-quality output."}, "", generated_at, [event["id"] for event in events], reference_period=("2005-01-01", "2019-10-01"),
    )

    datasets = [oil_prices, gm2_lead, residuals, energy_gdp, equities, uso, headline, net_output, capacity, household, financial]
    files: list[str] = []
    for dataset in datasets:
        filename = f"{dataset['id']}.json"
        (out_dir / filename).write_text(json.dumps(dataset, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        files.append(filename)

    lag_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "gm2Oil": [{"target": row.get("target"), "lag": row.get("lag_months"), "correlation": row.get("correlation"), "n": row.get("n")} for row in lag_rows],
        "oilEquityReturns": [{"sample": row.get("sample"), "metric": row.get("metric"), "oilMetric": row.get("oil_metric"), "lag": row.get("lag_periods"), "correlation": row.get("correlation"), "n": row.get("n_obs")} for row in equity_lag_rows],
        "conventions": {"gm2Oil": "positive lag means GM2 leads oil", "oilEquity": "positive lag means stocks lead oil; negative lag means oil leads stocks"},
        "details": {
            "gm2": {"plainLanguageSummary": "This chart compares simple GM2-oil correlations across candidate lead times; the locked five-month model comes from rolling validation, not from choosing the tallest correlation point.", "description": "Lag correlation between GM2 YoY and later WTI or Brent YoY.", "howToRead": "Positive lags mean GM2 is observed before oil. Compare the four-month descriptive peak with the five-month locked benchmark marker.", "calculation": {"formula": "corr(GM2_YoY[t-lag], Oil_YoY[t])", "explanation": "Each point uses the common observations available at that lag.", "example": "Lag 5 compares GM2 in January with oil YoY in June."}, "patternsToWatch": ["A broad correlation plateau rather than a single isolated peak", "Differences between WTI and Brent"], "limitations": ["Overlapping YoY changes are autocorrelated; correlation is not out-of-sample performance or causation."], "sourceNotes": ["Project G4 GM2 aggregate; FRED WTI and Brent"], "transformation": {"type": "yoy", "referenceStart": None, "referenceEnd": None, "mean": None, "standardDeviation": None}},
            "equity": {"plainLanguageSummary": "Monthly-return lag correlations are a market-timing robustness check; the relationship is mostly contemporaneous and does not support a general oil-led equity timing rule.", "description": "Lag correlation between monthly S&P 500 and oil log returns.", "howToRead": "Positive lags mean stocks lead oil; negative lags mean oil leads stocks; zero is contemporaneous.", "calculation": {"formula": "corr(SP500_return[t-lag], Oil_return[t])", "explanation": "Returns use non-overlapping one-month log changes.", "example": "Lag -1 asks whether this month's oil return aligns with next month's equity return."}, "patternsToWatch": ["Whether correlations away from zero remain meaningful", "Agreement between WTI and Brent"], "limitations": ["Return correlations can vary by shock regime and do not establish a tradable or causal rule."], "sourceNotes": ["FRED SP500, DCOILWTICO, and DCOILBRENTEU"], "transformation": {"type": "raw", "referenceStart": None, "referenceEnd": None, "mean": None, "standardDeviation": None}},
        },
    }
    correlation_details = {
        "plainLanguageSummary": "This comparison asks whether energy-consumption growth moves more closely with productive and household measures than with broader financial or headline aggregates.",
        "description": "Contemporaneous correlations between total energy-consumption growth and each economic measure's growth rate.",
        "howToRead": "Bars farther from zero indicate stronger co-movement, not greater economic value or causal importance. Inspect coverage and out-of-sample columns before treating a relationship as stable.",
        "calculation": {"formula": "correlation = corr(Energy_growth[t], Economic_measure_growth[t])", "explanation": "Quarterly series use year-over-year growth and genuine common quarter dates. Separate table fields report lags, rolling stability, distributed lags, recession splits, and expanding out-of-sample errors.", "example": "A correlation of 0.60 means the two growth rates tended to move together in the covered sample; it does not mean energy caused 60% of the outcome."},
        "patternsToWatch": ["Whether material-output measures cluster above financial valuation measures", "Whether a full-sample relationship weakens in rolling or out-of-sample tests"],
        "limitations": ["Latest-vintage bivariate correlations are exposed to revisions, common business-cycle drivers, and differing date coverage.", "Correlation, predictive improvement, and causal interpretation are separate claims."],
        "sourceNotes": ["EIA Monthly Energy Review total energy consumption", "BEA, BLS, Federal Reserve, BTS, Census, and World Bank series distributed through FRED"],
        "transformation": {"type": "yoy", "referenceStart": None, "referenceEnd": None, "mean": None, "standardDeviation": None},
    }
    shared = {"lag-results.json": lag_payload, "regimes.json": {"schemaVersion": SCHEMA_VERSION, "regimes": regimes, "recessions": _recession_periods(system_rows)}, "events.json": {"schemaVersion": SCHEMA_VERSION, "events": events}, "output-quality-correlations.json": {"schemaVersion": SCHEMA_VERSION, "generatedAt": generated_at, "evidenceLabel": "Experimental proxy", "details": correlation_details, "rows": output_quality_correlations}}
    cross_mapping = {"GM2_YoY": "GM2_YoY", "WTI_YoY": "WTI_YoY", "CI_zscore": "CI_zscore", "household_energy_burden": "household_energy_expenditure_share", "industrial_production": "Industrial_production_YoY", "weekly_hours": "average_weekly_hours_YoY", "temporary_help": "temporary_help_YoY"}
    shared["cross-layer.json"] = {"schemaVersion": SCHEMA_VERSION, "frequency": "monthly", "fields": cross_mapping, "observations": _observations(system_rows, cross_mapping)}
    for filename, payload in shared.items():
        (out_dir / filename).write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        files.append(filename)

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "datasets": [{"id": item["id"], "file": f"{item['id']}.json", "title": item["title"], "frequency": item["frequency"], "dateRange": item["dateRange"], "evidenceLabel": item["evidenceLabel"]} for item in datasets],
        "shared": ["lag-results.json", "regimes.json", "events.json", "cross-layer.json", "output-quality-correlations.json"],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    files.append("manifest.json")
    return files
