from __future__ import annotations

import csv
import math
from datetime import UTC, datetime
from pathlib import Path

from .adapters import Series
from .storage import Row, write_csv


SOURCE_MANIFEST: list[Row] = [
    {
        "source_name": "FRED",
        "series_id": "M2SL",
        "description": "U.S. M2 money stock",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL",
        "notes": "Billions of U.S. dollars; monthly; seasonally adjusted.",
    },
    {
        "source_name": "ECB Data Portal",
        "series_id": "BSI.M.U2.Y.V.M20.X.1.U2.2300.Z01.E",
        "description": "Euro area M2 stocks",
        "source_url_or_api": "https://data-api.ecb.europa.eu/service/data/BSI/M.U2.Y.V.M20.X.1.U2.2300.Z01.E?startPeriod=1980-01&format=csvdata",
        "notes": "Outstanding stocks; adapter stores EUR actual by multiplying ECB EUR millions by 1e6.",
    },
    {
        "source_name": "ChinaData/PBoC proxy plus IMF/FRED history",
        "series_id": "china-m2-money-supply; MYAGM2CNM189N",
        "description": "China M2 money supply",
        "source_url_or_api": "https://chinadata.live/api/v2/data/china-m2-money-supply",
        "notes": "Current API documents PBoC as source and reports 100 million CNY; stale IMF/FRED history is merged for older dates.",
    },
    {
        "source_name": "Bank of Japan",
        "series_id": "MD02:MAM1NAM2M2MO",
        "description": "Japan M2 money stock",
        "source_url_or_api": "https://www.stat-search.boj.or.jp/api/v1/getDataCode?format=csv&lang=en&db=MD02&startDate=199801&code=MAM1NAM2M2MO",
        "notes": "Average amounts outstanding; source unit is 100 million yen.",
    },
    {
        "source_name": "FRED",
        "series_id": "DEXUSEU",
        "description": "U.S. dollars per euro",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXUSEU",
        "notes": "Daily observations averaged to month.",
    },
    {
        "source_name": "FRED",
        "series_id": "DEXCHUS",
        "description": "Chinese yuan per U.S. dollar",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS",
        "notes": "Daily observations averaged to month.",
    },
    {
        "source_name": "FRED",
        "series_id": "DEXJPUS",
        "description": "Japanese yen per U.S. dollar",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXJPUS",
        "notes": "Daily observations averaged to month.",
    },
    {
        "source_name": "FRED",
        "series_id": "CPIAUCSL",
        "description": "U.S. consumer price index for all urban consumers",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL",
        "notes": "Monthly CPI index used to deflate nominal WTI and Brent price levels.",
    },
    {
        "source_name": "FRED",
        "series_id": "GDPC1",
        "description": "U.S. real gross domestic product",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1",
        "notes": "Quarterly chained-dollar real GDP used for energy-GDP lead-lag analysis.",
    },
    {
        "source_name": "FRED",
        "series_id": "INDPRO",
        "description": "U.S. industrial production index",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDPRO",
        "notes": "Monthly real-activity proxy used for higher-frequency energy-GDP tests.",
    },
    {
        "source_name": "EIA Monthly Energy Review",
        "series_id": "T01.03:TETCBUS",
        "description": "U.S. total primary energy consumption",
        "source_url_or_api": "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T01.03",
        "notes": "Monthly quadrillion Btu observations; annual rows ending in YYYY13 are excluded.",
    },
    {
        "source_name": "EIA Monthly Energy Review",
        "series_id": "T01.03:PMTCBUS",
        "description": "U.S. petroleum consumption excluding biofuels",
        "source_url_or_api": "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T01.03",
        "notes": "Monthly quadrillion Btu observations; used as oil-consumption proxy.",
    },
    {
        "source_name": "FRED",
        "series_id": "SP500",
        "description": "S&P 500 price index",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500",
        "notes": "Daily observations averaged to month for oil-equity lead-lag analysis.",
    },
    {
        "source_name": "Yahoo Finance chart API",
        "series_id": "USO",
        "description": "United States Oil Fund adjusted close",
        "source_url_or_api": "https://query2.finance.yahoo.com/v8/finance/chart/USO",
        "notes": "Daily adjusted close cached as raw JSON; pipeline derives monthly average and month-end adjusted close.",
    },
    {
        "source_name": "FRED",
        "series_id": "DCOILWTICO",
        "description": "WTI crude oil spot price",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO",
        "notes": "Daily observations averaged to month.",
    },
    {
        "source_name": "FRED",
        "series_id": "DCOILBRENTEU",
        "description": "Brent crude oil spot price",
        "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU",
        "notes": "Daily observations averaged to month.",
    },
    {
        "source_name": "EIA Petroleum Marketing Monthly",
        "series_id": "R0000____3; R1200____3; R1300____3",
        "description": "U.S. composite, domestic, and imported refiner acquisition costs",
        "source_url_or_api": "https://www.eia.gov/dnav/pet/PET_PRI_RAC2_DCU_NUS_M.htm",
        "notes": "Monthly dollars per barrel; current observations may be preliminary or estimated by EIA.",
    },
    {
        "source_name": "EIA Petroleum Marketing Monthly",
        "series_id": "F000000__3",
        "description": "U.S. domestic crude oil first purchase price",
        "source_url_or_api": "https://www.eia.gov/dnav/pet/PET_PRI_DFP1_K_M.htm",
        "notes": "Monthly dollars per barrel at the lease or wellhead first arm's-length purchase.",
    },
    {
        "source_name": "EIA Petroleum Marketing Monthly",
        "series_id": "I000000004; I000000008",
        "description": "Average imported crude oil FOB and landed costs",
        "source_url_or_api": "https://www.eia.gov/dnav/pet/pet_move_imc1_k_m.htm",
        "notes": "Monthly dollars per barrel; landed cost is measured at the port of discharge.",
    },
    {
        "source_name": "EIA",
        "series_id": "WCESTUS1",
        "description": "Weekly U.S. ending stocks excluding SPR of crude oil",
        "source_url_or_api": "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=W&n=PET&s=WCESTUS1",
        "notes": "Weekly thousand barrels averaged to month.",
    },
]


def write_audit_outputs(
    root: Path,
    rows: list[Row],
    lag_rows: list[Row],
    regression_rows: list[Row],
    rolling_rows: list[Row],
    source_series: dict[str, Series],
) -> list[str]:
    seed_dir = root / "data" / "seed"
    analysis_dir = root / "analysis"
    seed_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    prior_seed = read_csv(seed_dir / "global_m2_latest_seed.csv")
    latest_complete = latest_complete_gm2_row(rows)
    global_seed = global_m2_seed_rows(latest_complete, retrieved_at)
    warnings = compare_seed(prior_seed, global_seed)

    write_csv(seed_dir / "monthly_dataset_seed.csv", rows)
    write_csv(seed_dir / "global_m2_latest_seed.csv", global_seed)
    write_csv(seed_dir / "source_manifest.csv", SOURCE_MANIFEST)
    (analysis_dir / "latest_source_values.md").write_text(
        latest_source_values_markdown(rows, source_series, latest_complete, global_seed, warnings, retrieved_at),
        encoding="utf-8",
    )
    (analysis_dir / "model_findings.md").write_text(
        model_findings_markdown(lag_rows, regression_rows, rolling_rows, retrieved_at),
        encoding="utf-8",
    )
    return warnings


def latest_complete_gm2_row(rows: list[Row]) -> Row:
    for row in reversed(rows):
        required = [
            "US_M2_USD",
            "EA_M2_USD",
            "CN_M2_USD",
            "JP_M2_USD",
            "EURUSD",
            "CNY_per_USD",
            "JPY_per_USD",
            "GM2_USD",
        ]
        if all(is_number(row.get(col)) for col in required):
            return row
    raise RuntimeError("No complete G4 GM2 month found; refusing to produce synthetic seed data")


def global_m2_seed_rows(row: Row, retrieved_at: str) -> list[Row]:
    month = str(row["month"])
    components = [
        {
            "date": month,
            "component": "US M2",
            "native_value": float(row["US_M2_USD"]) / 1_000_000_000,
            "native_unit": "USD_billion",
            "fx_to_usd": 1.0,
            "usd_value": row["US_M2_USD"],
            "source_name": "FRED",
            "source_series_id": "M2SL",
            "source_url_or_api": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL",
            "retrieved_at": retrieved_at,
            "notes": "Converted from FRED billions of USD to actual USD.",
        },
        {
            "date": month,
            "component": "Euro area M2",
            "native_value": float(row["EA_M2_EUR"]) / 1_000_000,
            "native_unit": "EUR_million",
            "fx_to_usd": row["EURUSD"],
            "usd_value": row["EA_M2_USD"],
            "source_name": "ECB Data Portal",
            "source_series_id": "BSI.M.U2.Y.V.M20.X.1.U2.2300.Z01.E",
            "source_url_or_api": "https://data-api.ecb.europa.eu/service/data/BSI/M.U2.Y.V.M20.X.1.U2.2300.Z01.E?startPeriod=1980-01&format=csvdata",
            "retrieved_at": retrieved_at,
            "notes": "ECB EUR millions converted to EUR actual, then multiplied by same-month EURUSD.",
        },
        {
            "date": month,
            "component": "China M2",
            "native_value": float(row["CN_M2_CNY"]) / 1_000_000_000,
            "native_unit": "CNY_billion",
            "fx_to_usd": 1 / float(row["CNY_per_USD"]),
            "usd_value": row["CN_M2_USD"],
            "source_name": "ChinaData/PBoC proxy plus IMF/FRED history",
            "source_series_id": "china-m2-money-supply; MYAGM2CNM189N",
            "source_url_or_api": "https://chinadata.live/api/v2/data/china-m2-money-supply",
            "retrieved_at": retrieved_at,
            "notes": "Current API reports 100 million CNY; adapter stores CNY actual and divides by same-month CNY per USD.",
        },
        {
            "date": month,
            "component": "Japan M2",
            "native_value": float(row["JP_M2_JPY"]) / 1_000_000_000,
            "native_unit": "JPY_billion",
            "fx_to_usd": 1 / float(row["JPY_per_USD"]),
            "usd_value": row["JP_M2_USD"],
            "source_name": "Bank of Japan",
            "source_series_id": "MD02:MAM1NAM2M2MO",
            "source_url_or_api": "https://www.stat-search.boj.or.jp/api/v1/getDataCode?format=csv&lang=en&db=MD02&startDate=199801&code=MAM1NAM2M2MO",
            "retrieved_at": retrieved_at,
            "notes": "BOJ 100 million yen converted to JPY actual, then divided by same-month JPY per USD.",
        },
    ]
    total = {
        "date": month,
        "component": "G4 total",
        "native_value": None,
        "native_unit": None,
        "fx_to_usd": None,
        "usd_value": row["GM2_USD"],
        "source_name": "Computed",
        "source_series_id": "G4_GLOBAL_M2_USD",
        "source_url_or_api": "local pipeline sum",
        "retrieved_at": retrieved_at,
        "notes": "Sum of US, euro area, China, and Japan M2 converted to USD. No forward fill.",
    }
    return components + [total]


def latest_source_values_markdown(
    rows: list[Row],
    source_series: dict[str, Series],
    latest_complete: Row,
    global_seed: list[Row],
    warnings: list[str],
    retrieved_at: str,
) -> str:
    source_latest = []
    for label, series in source_series.items():
        date_value = max(series.observations, default=(None, None))
        source_latest.append((label, date_value[0], date_value[1], series.unit, series.source))

    latest_wti = latest_non_missing(rows, "WTI")
    latest_brent = latest_non_missing(rows, "Brent")
    latest_inv = latest_non_missing(rows, "crude_inventory_kb")
    latest_comp = latest_non_missing(rows, "comparative_inventory_kb")
    latest_any_month = rows[-1]["month"] if rows else "missing"
    limiting = [
        label
        for label, series in source_series.items()
        if label in {"US M2", "Euro area M2", "China M2", "Japan M2"}
        and max((d for d, _ in series.observations), default="") == latest_complete["month"]
    ]
    stale = []
    if latest_any_month != latest_complete["month"]:
        stale.append(
            f"GM2 is complete only through {latest_complete['month']}; later monthly rows exist through {latest_any_month} but are partial."
        )
    for label, series in source_series.items():
        if not series.observations:
            stale.append(f"{label} returned no observations")

    lines = [
        "# Latest Source Values",
        "",
        f"Retrieved at: `{retrieved_at}`",
        "",
        f"Latest complete GM2 month: **{latest_complete['month']}**",
        f"G4 GM2 USD: **{format_number(float(latest_complete['GM2_USD']))}**",
        "",
        "## G4 Components",
        "",
        "| Component | Native value | Native unit | FX to USD | USD value | Source | Series |",
        "|---|---:|---|---:|---:|---|---|",
    ]
    for row in global_seed:
        lines.append(
            f"| {row['component']} | {format_optional(row['native_value'])} | {row['native_unit'] or ''} | "
            f"{format_optional(row['fx_to_usd'])} | {format_optional(row['usd_value'])} | "
            f"{row['source_name']} | `{row['source_series_id']}` |"
        )
    lines.extend(
        [
            "",
            "## Latest Raw Source Dates",
            "",
            "| Source | Latest date | Latest native value | Unit | Adapter source |",
            "|---|---|---:|---|---|",
        ]
    )
    for label, obs_date, value, unit, source in source_latest:
        lines.append(f"| {label} | {obs_date or 'missing'} | {format_optional(value)} | {unit} | {source} |")
    lines.extend(
        [
            "",
            "## Oil And Inventory",
            "",
            f"- WTI latest monthly value: {format_latest(latest_wti)}",
            f"- Brent latest monthly value: {format_latest(latest_brent)}",
            f"- Crude inventory latest value: {format_latest(latest_inv)} thousand barrels",
            f"- Comparative inventory latest value: {format_latest(latest_comp)} thousand barrels",
            "",
            "## Missing Or Stale Sources",
            "",
        ]
    )
    if stale:
        lines.extend(f"- {item}" for item in stale)
    else:
        lines.append("- None detected.")
    if limiting:
        lines.append(f"- Source(s) limiting latest complete G4 month: {', '.join(limiting)}.")
    if warnings:
        lines.extend(["", "## Seed Audit Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines) + "\n"


def model_findings_markdown(
    lag_rows: list[Row],
    regression_rows: list[Row],
    rolling_rows: list[Row],
    retrieved_at: str,
) -> str:
    best_wti = best_corr(lag_rows, "WTI_YoY")
    best_brent = best_corr(lag_rows, "Brent_YoY")
    best_single = min(
        [r for r in regression_rows if r.get("model") in {"a_gm2", "b_inventory"} and is_number(r.get("test_rmse"))],
        key=lambda r: float(r["test_rmse"]),
    )
    best_combined = min(
        [r for r in regression_rows if r.get("model") == "c_gm2_inventory" and is_number(r.get("test_rmse"))],
        key=lambda r: float(r["test_rmse"]),
    )
    best_overall = min(
        [r for r in regression_rows if is_number(r.get("test_rmse"))],
        key=lambda r: float(r["test_rmse"]),
    )
    comparisons = combined_improvement_lines(regression_rows)
    rolling_best = sorted(
        [r for r in rolling_rows if is_number(r.get("rolling_rmse"))],
        key=lambda r: float(r["rolling_rmse"]),
    )[:6]

    lines = [
        "# Model Findings",
        "",
        f"Generated at: `{retrieved_at}`",
        "",
        "## Lag Correlations",
        "",
        f"- Best GM2 lead time for WTI YoY: {best_lag_sentence(best_wti)}",
        f"- Best GM2 lead time for Brent YoY: {best_lag_sentence(best_brent)}",
        "",
        "## Regression Selection",
        "",
        f"- Best single-signal model by test RMSE: {model_sentence(best_single)}",
        f"- Best combined model by test RMSE: {model_sentence(best_combined)}",
        f"- Best overall model by test RMSE: {model_sentence(best_overall)}",
        "",
        "## Combined Model Comparisons",
        "",
    ]
    lines.extend(f"- {line}" for line in comparisons)
    lines.extend(["", "## Rolling Validation", ""])
    for row in rolling_best:
        lines.append(
            f"- {row['target']} {row['model']} lag {row['lag_months']}: "
            f"rolling RMSE {float(row['rolling_rmse']):.3f}, rolling R2 {format_optional(row.get('rolling_r2'))}, "
            f"n={row['n_predictions']}."
        )
    lines.extend(
        [
            "",
            "## Regime Caveats",
            "",
            "- 2008: financial-crisis oil collapse can dominate liquidity relationships and produce high-leverage observations.",
            "- 2014 to 2016: shale supply growth and OPEC strategy shifts can weaken a pure liquidity signal.",
            "- 2020: pandemic demand shock and extreme oil-market dislocation are not normal monetary-transmission observations.",
            "- 2022: sanctions, SPR releases, and war-driven energy risk premia can make inventory and price behavior regime-specific.",
            "",
            "All findings above are computed from the generated CSV files. No assumed 5 to 10 month lead is used.",
        ]
    )
    return "\n".join(lines) + "\n"


def terminal_summary(rows: list[Row], lag_rows: list[Row], regression_rows: list[Row], warnings: list[str]) -> str:
    latest = latest_complete_gm2_row(rows)
    best_wti = best_corr(lag_rows, "WTI_YoY")
    best_brent = best_corr(lag_rows, "Brent_YoY")
    best_model = min(
        [r for r in regression_rows if is_number(r.get("test_rmse"))],
        key=lambda r: float(r["test_rmse"]),
    )
    combined_lines = combined_improvement_lines(regression_rows)
    return "\n".join(
        [
            "",
            f"Latest complete GM2 month: {latest['month']}",
            f"G4 GM2 USD: {format_number(float(latest['GM2_USD']))}",
            f"Best WTI GM2 lead: {best_lag_sentence(best_wti)}",
            f"Best Brent GM2 lead: {best_lag_sentence(best_brent)}",
            f"Best model by test RMSE: {model_sentence(best_model)}",
            f"Combined model improvement over GM2-only: {first_matching(combined_lines, 'vs GM2-only')}",
            f"Combined model improvement over CI-only: {first_matching(combined_lines, 'vs CI-only')}",
            f"Major missing/stale sources: {'; '.join(warnings) if warnings else 'none from seed audit; see analysis/latest_source_values.md for freshness notes'}",
        ]
    )


def compare_seed(previous: list[dict[str, str]], current: list[Row]) -> list[str]:
    if not previous:
        return []
    prior_by_component = {row["component"]: row for row in previous}
    warnings = []
    for row in current:
        prior = prior_by_component.get(str(row["component"]))
        if not prior:
            continue
        old = parse_number(prior.get("usd_value"))
        new = parse_number(row.get("usd_value"))
        if old is None or new is None or old == 0:
            continue
        pct = abs(new / old - 1) * 100
        if pct > 2:
            warnings.append(
                f"{row['component']} USD value changed {pct:.2f}% from existing seed "
                f"({format_number(old)} to {format_number(new)}). Source audit recommended."
            )
    return warnings


def combined_improvement_lines(regression_rows: list[Row]) -> list[str]:
    lines = []
    targets = sorted({str(r["target"]) for r in regression_rows})
    for target in targets:
        target_rows = [r for r in regression_rows if r["target"] == target and is_number(r.get("test_rmse"))]
        combined = best_model_row(target_rows, "c_gm2_inventory")
        gm2 = best_model_row(target_rows, "a_gm2")
        ci = best_model_row(target_rows, "b_inventory")
        if combined and gm2:
            lines.append(improvement_line(target, int(combined["lag_months"]), combined, gm2, "GM2-only"))
        if combined and ci:
            lines.append(improvement_line(target, int(combined["lag_months"]), combined, ci, "CI-only"))
    return lines or ["No comparable combined-model rows were available."]


def improvement_line(target: str, lag: int, combined: Row, baseline: Row, baseline_name: str) -> str:
    c = float(combined["test_rmse"])
    b = float(baseline["test_rmse"])
    improvement = (b - c) / b * 100 if b else math.nan
    verb = "beats" if improvement > 0 else "does not beat"
    return (
        f"{target} lag {lag}: combined RMSE {c:.3f} {verb} {baseline_name} "
        f"RMSE {b:.3f} by {improvement:.2f}% vs {baseline_name}."
    )


def pick(rows: list[Row], model: str, lag: int) -> Row | None:
    for row in rows:
        if row.get("model") == model and int(row["lag_months"]) == lag:
            return row
    return None


def best_model_row(rows: list[Row], model: str) -> Row | None:
    selected = [r for r in rows if r.get("model") == model and is_number(r.get("test_rmse"))]
    return min(selected, key=lambda r: float(r["test_rmse"])) if selected else None


def best_corr(rows: list[Row], target: str) -> Row | None:
    selected = [r for r in rows if r.get("target") == target and is_number(r.get("correlation"))]
    return max(selected, key=lambda r: float(r["correlation"])) if selected else None


def best_lag_sentence(row: Row | None) -> str:
    if not row:
        return "missing"
    return f"{row['lag_months']} months (correlation {float(row['correlation']):.3f}, n={row['n']})"


def model_sentence(row: Row) -> str:
    return (
        f"{row['target']} {row['model']} lag {row['lag_months']} "
        f"test RMSE {float(row['test_rmse']):.3f}, test R2 {format_optional(row.get('test_r2'))}"
    )


def latest_non_missing(rows: list[Row], column: str) -> tuple[str, float] | None:
    for row in reversed(rows):
        if is_number(row.get(column)):
            return str(row["month"]), float(row[column])
    return None


def format_latest(value: tuple[str, float] | None) -> str:
    if value is None:
        return "missing"
    return f"{value[0]} = {format_number(value[1])}"


def format_optional(value: object) -> str:
    parsed = parse_number(value)
    if parsed is None:
        return ""
    return f"{parsed:.6g}"


def format_number(value: float) -> str:
    return f"{value:,.6g}"


def parse_number(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def is_number(value: object) -> bool:
    return parse_number(value) is not None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def first_matching(lines: list[str], needle: str) -> str:
    for line in lines:
        if needle in line:
            return line
    return "not available"
