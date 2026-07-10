from __future__ import annotations

import math

import numpy as np
from scipy import stats

from .adapters import Series
from .storage import Row


TARGETS = ["WTI_YoY", "Brent_YoY"]
REGIMES = {
    "financial_crisis_2008_2009": ("2008-01", "2009-12"),
    "shale_regime_2014_2017": ("2014-01", "2017-12"),
    "covid_2020_2021": ("2020-01", "2021-12"),
    "war_spr_2022_2023": ("2022-01", "2023-12"),
}
SHOCK_REGIMES = set(REGIMES)


def lag_correlations(rows: list[Row], target: str, max_lag: int = 18) -> list[Row]:
    out: list[Row] = []
    for lag in range(max_lag + 1):
        pairs = lagged_pairs(rows, "GM2_YoY", target, lag)
        if len(pairs) < 3:
            corr = pvalue = None
        else:
            x = np.array([p[0] for p in pairs], dtype=float)
            y = np.array([p[1] for p in pairs], dtype=float)
            corr, pvalue = stats.pearsonr(x, y)
        out.append({"target": target, "lag_months": lag, "correlation": corr, "p_value": pvalue, "n": len(pairs)})
    return out


def lagged_pairs(rows: list[Row], x_col: str, y_col: str, lag: int) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for i, row in enumerate(rows):
        j = i - lag
        if j < 0:
            continue
        x = rows[j].get(x_col)
        y = row.get(y_col)
        if is_number(x) and is_number(y):
            pairs.append((float(x), float(y)))
    return pairs


def regression_suite(rows: list[Row], max_lag: int = 18) -> tuple[list[Row], list[Row]]:
    summaries: list[Row] = []
    rolling: list[Row] = []
    for target in TARGETS:
        summaries.extend(run_specs(rows, target, max_lag))
        rolling.extend(rolling_validation(rows, target, max_lag))
    return summaries, rolling


def second_stage_suite(rows: list[Row], max_lag: int = 18) -> tuple[list[Row], list[Row], list[Row], list[Row], str]:
    enriched = add_regime_fields(rows)
    interaction_rows: list[Row] = []
    residual_rows: list[Row] = []
    regime_rows: list[Row] = []
    rolling_rows: list[Row] = []
    for target in TARGETS:
        baselines = {lag: rolling_predictions(enriched, target, [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60) for lag in range(max_lag + 1)}
        for lag in range(max_lag + 1):
            interaction_rows.extend(interaction_summaries(enriched, target, lag))
            residual_rows.append(residual_summary(enriched, target, lag))
        regime_rows.extend(regime_summaries(enriched, target, max_lag))
        no_shock = mask_target_shocks(enriched, target)
        for window in [60, 84, 120]:
            rolling_rows.extend(extended_rolling_for_target(enriched, target, max_lag, window, "all", baselines if window == 60 else None))
            rolling_rows.extend(extended_rolling_for_target(no_shock, target, max_lag, window, "excluding_shocks", None))
    findings = second_stage_findings(enriched, interaction_rows, residual_rows, regime_rows, rolling_rows)
    return interaction_rows, residual_rows, regime_rows, rolling_rows, findings


def third_stage_suite(rows: list[Row], max_lag: int = 18) -> tuple[list[Row], list[Row], str]:
    enriched = add_regime_fields(rows)
    residual_targets = add_gm2_residual_targets(enriched, max_lag)
    target_rows: list[Row] = []
    diagnostic_rows: list[Row] = []
    for target in third_stage_targets():
        target_rows.extend(target_comparison_rows(residual_targets, target, max_lag))
    for oil_target in TARGETS:
        diagnostic_rows.append(two_step_residual_diagnostic(residual_targets, oil_target, best_gm2_lag(residual_targets, oil_target, max_lag)))
    interpretation = final_model_interpretation(target_rows, diagnostic_rows)
    return target_rows, diagnostic_rows, interpretation


def final_reporting_suite(
    rows: list[Row],
    lag_rows: list[Row],
    rolling_extended_rows: list[Row],
    residual_diagnostic_rows: list[Row],
    best_lag: int = 5,
) -> tuple[list[Row], str, str, str]:
    enriched = add_regime_fields(rows)
    final_rows = final_findings_rows(enriched, lag_rows, rolling_extended_rows, residual_diagnostic_rows, best_lag)
    snapshot = current_signal_snapshot(enriched, best_lag)
    executive = executive_summary(final_rows, snapshot, best_lag)
    card = model_card(final_rows, best_lag)
    return final_rows, executive, card, snapshot


def oil_equity_suite(rows: list[Row], max_abs_lag: int = 18, gm2_lag: int = 5) -> tuple[list[Row], str]:
    enriched = add_oil_equity_fields(add_regime_fields(rows))
    out: list[Row] = []
    out.extend(oil_equity_correlation_matrix(enriched))
    out.extend(oil_equity_lead_lag_rows(enriched, max_abs_lag))
    out.extend(oil_equity_forecast_rows(enriched, max_abs_lag, gm2_lag))
    out.extend(oil_equity_reverse_rows(enriched, max_abs_lag))
    out.extend(oil_equity_regime_rows(enriched))
    findings = oil_equity_findings(out, gm2_lag)
    return out, findings


def oil_equity_robustness_suite(rows: list[Row], max_abs_lag: int = 18) -> tuple[list[Row], str]:
    enriched = add_oil_equity_fields(add_regime_fields(rows))
    summary = oil_equity_return_lag_rows(enriched, max_abs_lag)
    findings = oil_equity_robustness_findings(summary)
    return summary, findings


def uso_suite(rows: list[Row], max_abs_lag: int = 18, gm2_lag: int = 5) -> tuple[list[Row], list[Row], list[Row], str]:
    enriched = add_regime_fields(rows)
    lead_lag = uso_lead_lag_rows(enriched, max_abs_lag)
    tracking = uso_tracking_residual_rows(enriched)
    models = uso_model_rows(enriched, max_abs_lag, gm2_lag)
    findings = uso_findings(enriched, lead_lag, tracking, models, gm2_lag)
    return lead_lag, tracking, models, findings


def uso_lead_lag_rows(rows: list[Row], max_abs_lag: int) -> list[Row]:
    out: list[Row] = []
    pairs = [
        ("USO_YoY", "WTI_YoY"),
        ("USO_YoY", "Brent_YoY"),
        ("USO_log_return_1m", "WTI_log_return_1m"),
        ("USO_log_return_1m", "Brent_log_return_1m"),
    ]
    for uso_col, benchmark_col in pairs:
        x, y = aligned_values(rows, uso_col, benchmark_col)
        corr, pvalue = pearson(x, y)
        out.append(
            {
                "section": "correlation_matrix",
                "uso_metric": uso_col,
                "benchmark_metric": benchmark_col,
                "lag_months": 0,
                "lag_convention": "zero = contemporaneous",
                "correlation": corr,
                "p_value": pvalue,
                "n_obs": len(x),
            }
        )
        for lag in range(-max_abs_lag, max_abs_lag + 1):
            lx, ly, months = generic_lead_lag_values(rows, uso_col, benchmark_col, lag)
            lag_corr, lag_pvalue = pearson(lx, ly)
            out.append(
                {
                    "section": "lead_lag_correlation",
                    "uso_metric": uso_col,
                    "benchmark_metric": benchmark_col,
                    "lag_months": lag,
                    "lag_convention": "positive = USO leads benchmark oil; negative = benchmark oil leads USO",
                    "correlation": lag_corr,
                    "p_value": lag_pvalue,
                    "n_obs": len(lx),
                }
            )
            for window in [60, 84, 120]:
                rolling = rolling_correlations(lx, ly, months, window)
                if rolling:
                    out.append(
                        {
                            "section": "rolling_lead_lag_correlation",
                            "uso_metric": uso_col,
                            "benchmark_metric": benchmark_col,
                            "lag_months": lag,
                            "lag_convention": "positive = USO leads benchmark oil; negative = benchmark oil leads USO",
                            "window_months": window,
                            "rolling_correlation_mean": float(np.mean([r[1] for r in rolling])),
                            "rolling_correlation_latest": rolling[-1][1],
                            "rolling_correlation_latest_month": rolling[-1][0],
                            "n_windows": len(rolling),
                        }
                    )
    return out


def uso_tracking_residual_rows(rows: list[Row]) -> list[Row]:
    out: list[Row] = []
    regimes = ["all", *REGIMES, "normal_period"]
    columns = [
        "USO_tracking_residual",
        "USO_tracking_residual_vs_Brent",
        "USO_vs_WTI_return_spread",
        "USO_vs_Brent_return_spread",
    ]
    for regime in regimes:
        selected = rows if regime == "all" else [r for r in rows if r.get("regime") == regime]
        row: Row = {"section": "regime_tracking_summary", "regime": regime, "n_months": len(selected)}
        for col in columns:
            values = [float(r[col]) for r in selected if is_number(r.get(col))]
            row[f"{col}_mean"] = float(np.mean(values)) if values else None
            row[f"{col}_median"] = float(np.median(values)) if values else None
            row[f"{col}_std"] = float(np.std(values)) if values else None
            row[f"{col}_n"] = len(values)
        out.append(row)
    latest = latest_with_values(rows, ["USO_YoY", "WTI_YoY", "Brent_YoY", "USO_tracking_residual", "USO_log_return_1m"])
    if latest:
        out.append(
            {
                "section": "latest_tracking_snapshot",
                "month": latest.get("month"),
                "regime": latest.get("regime"),
                "USO_YoY": latest.get("USO_YoY"),
                "WTI_YoY": latest.get("WTI_YoY"),
                "Brent_YoY": latest.get("Brent_YoY"),
                "USO_tracking_residual": latest.get("USO_tracking_residual"),
                "USO_tracking_residual_vs_Brent": latest.get("USO_tracking_residual_vs_Brent"),
                "USO_vs_WTI_return_spread": latest.get("USO_vs_WTI_return_spread"),
                "USO_vs_Brent_return_spread": latest.get("USO_vs_Brent_return_spread"),
            }
        )
    return out


def uso_model_rows(rows: list[Row], max_lag: int, gm2_lag: int) -> list[Row]:
    out: list[Row] = []
    benchmark_features = [feature("GM2_YoY", gm2_lag, "GM2_YoY_lag5")]
    benchmark_pred = rolling_predictions(rows, "WTI_YoY", benchmark_features, 60)
    if benchmark_pred:
        out.append(rolling_forecast_summary("WTI_YoY", "oil_benchmark_model", "locked_gm2_only_lag5", gm2_lag, 60, benchmark_pred, benchmark_pred))
    out.append(fit_summary(rows, "WTI_YoY", "locked_gm2_only_lag5", benchmark_features, gm2_lag, "uso_benchmark_reference"))

    for lag in range(max_lag + 1):
        gm2 = feature("GM2_YoY", lag, "GM2_YoY_lag")
        gm2_pred = rolling_predictions(rows, "USO_YoY", [gm2], 60)
        if gm2_pred:
            out.append(rolling_forecast_summary("USO_YoY", "tradable_exposure_model", "uso_gm2_only", lag, 60, gm2_pred, {}))
        out.append(fit_summary(rows, "USO_YoY", "uso_gm2_only", [gm2], lag, "uso_tradable_exposure"))

        combined_features = [
            gm2,
            feature("CI_zscore", 0, "CI_zscore"),
            feature("CI_monthly_change", 0, "CI_monthly_change"),
            feature("SP500_log_return_1m", 0, "SP500_return_context"),
        ]
        combined_pred = rolling_predictions(rows, "USO_YoY", combined_features, 60)
        if combined_pred:
            combined_summary = rolling_forecast_summary(
                "USO_YoY", "tradable_exposure_model", "uso_gm2_ci_sp500", lag, 60, combined_pred, gm2_pred
            )
            combined_summary["same_lag_uso_gm2_rmse"] = combined_summary.get("baseline_gm2_lag5_rmse")
            combined_summary["same_lag_uso_gm2_mae"] = combined_summary.get("baseline_gm2_lag5_mae")
            combined_summary["rmse_improvement_vs_same_lag_uso_gm2"] = combined_summary.get("rmse_improvement_vs_gm2_lag5")
            combined_summary["mae_improvement_vs_same_lag_uso_gm2"] = combined_summary.get("mae_improvement_vs_gm2_lag5")
            out.append(combined_summary)
        out.append(fit_summary(rows, "USO_YoY", "uso_gm2_ci_sp500", combined_features, lag, "uso_tradable_exposure"))

    residual_features = [
        feature("CI_zscore", 0, "CI_zscore"),
        feature("CI_monthly_change", 0, "CI_monthly_change"),
        feature("financial_crisis_2008_2009", 0, "financial_crisis_2008_2009"),
        feature("shale_regime_2014_2017", 0, "shale_regime_2014_2017"),
        feature("covid_2020_2021", 0, "covid_2020_2021"),
        feature("war_spr_2022_2023", 0, "war_spr_2022_2023"),
    ]
    residual_summary = fit_summary(rows, "USO_tracking_residual", "uso_tracking_residual_ci_regime", residual_features, 0, "uso_tracking_residual")
    out.append(residual_summary)
    residual_pred = rolling_predictions(rows, "USO_tracking_residual", residual_features, 60)
    if residual_pred:
        out.append(rolling_forecast_summary("USO_tracking_residual", "tracking_residual_model", "uso_tracking_residual_ci_regime", 0, 60, residual_pred, {}))
    return [r for r in out if r]


def uso_findings(rows: list[Row], lead_lag_rows: list[Row], tracking_rows: list[Row], model_rows: list[Row], gm2_lag: int) -> str:
    lines = [
        "# USO Tradable Oil Exposure Findings",
        "",
        "## Scope",
        "",
        "WTI and Brent remain the benchmark oil-price targets. USO is added as a tradable ETF exposure proxy because its investor return path can diverge from benchmark oil through futures roll yield, contango/backwardation, fund expenses, tracking differences, and ETF structure.",
        "",
        "## Lead-Lag Evidence",
        "",
    ]
    for metric, benchmark in [("USO_YoY", "WTI_YoY"), ("USO_YoY", "Brent_YoY"), ("USO_log_return_1m", "WTI_log_return_1m"), ("USO_log_return_1m", "Brent_log_return_1m")]:
        subset = [r for r in lead_lag_rows if r.get("section") == "lead_lag_correlation" and r.get("uso_metric") == metric and r.get("benchmark_metric") == benchmark and is_number(r.get("correlation"))]
        if subset:
            best = max(subset, key=lambda r: abs(float(r["correlation"])))
            direction = "USO leads benchmark oil" if int(best["lag_months"]) > 0 else "benchmark oil leads USO" if int(best["lag_months"]) < 0 else "contemporaneous"
            lines.append(f"- {metric} vs {benchmark}: strongest correlation is {fmt(best.get('correlation'))} at lag {best.get('lag_months')} ({direction}), n={best.get('n_obs')}.")

    lines.extend(["", "## Model Comparison", ""])
    best_uso = best_model_row(model_rows, "USO_YoY", "tradable_exposure_model")
    best_combined = best_model_row([r for r in model_rows if r.get("model") == "uso_gm2_ci_sp500"], "USO_YoY", "tradable_exposure_model")
    if best_uso:
        lines.append(f"- Best rolling USO tradable-exposure specification is `{best_uso.get('model')}` at GM2 lag {best_uso.get('lag_months')}, RMSE {fmt(best_uso.get('rolling_rmse'))}, MAE {fmt(best_uso.get('rolling_mae'))}.")
    if best_combined:
        rmse_imp = best_combined.get("rmse_improvement_vs_same_lag_uso_gm2")
        mae_imp = best_combined.get("mae_improvement_vs_same_lag_uso_gm2")
        verdict = "passes" if ((is_number(rmse_imp) and float(rmse_imp) >= 0.05) or (is_number(mae_imp) and float(mae_imp) >= 0.05)) else "does not pass"
        lines.append(f"- Best combined USO model is lag {best_combined.get('lag_months')}; it {verdict} a 5% improvement rule versus the same-lag USO GM2-only baseline.")
    lines.append(f"- The locked benchmark oil model is unchanged: WTI_YoY ~ GM2_YoY lag {gm2_lag}. USO is interpreted as a separate market-pricing layer, not a replacement target.")

    lines.extend(["", "## Tracking Residuals By Regime", ""])
    for row in tracking_rows:
        if row.get("section") == "regime_tracking_summary":
            lines.append(f"- {row.get('regime')}: mean USO minus WTI YoY residual {fmt(row.get('USO_tracking_residual_mean'))}; mean monthly USO-WTI return spread {fmt(row.get('USO_vs_WTI_return_spread_mean'))}.")

    residual = next((r for r in model_rows if r.get("model") == "uso_tracking_residual_ci_regime" and is_number(r.get("full_r2"))), None)
    if residual:
        lines.extend(["", "## Residual Model", ""])
        lines.append(f"- CI and regime variables explain USO tracking residual variance with full-sample R2 {fmt(residual.get('full_r2'))}. This is a reduced-form diagnostic for ETF/market-structure divergence, not a direct benchmark-oil forecast.")

    latest = latest_with_values(rows, ["USO_YoY", "WTI_YoY", "USO_tracking_residual"])
    if latest:
        lines.extend(["", "## Latest Snapshot", ""])
        lines.append(f"- Latest USO tracking month in the processed dataset is {latest.get('month')}: USO YoY {fmt(latest.get('USO_YoY'))}, WTI YoY {fmt(latest.get('WTI_YoY'))}, USO minus WTI residual {fmt(latest.get('USO_tracking_residual'))}.")

    lines.extend(
        [
            "",
            "## Roll/Structure Note",
            "",
            "A clean public WTI futures-curve source is not yet wired into the release pipeline. Until a documented curve source is added, USO tracking residuals and USO-WTI return spreads serve as reduced-form evidence of roll yield, contango/backwardation exposure, expenses, tracking error, and ETF structure.",
        ]
    )
    return "\n".join(lines) + "\n"


def best_model_row(rows: list[Row], target: str, section: str) -> Row:
    subset = [r for r in rows if r.get("target") == target and r.get("section") == section and is_number(r.get("rolling_rmse"))]
    return min(subset, key=lambda r: finite_or_inf(r.get("rolling_rmse")), default={})


def add_oil_equity_fields(rows: list[Row]) -> list[Row]:
    out: list[Row] = []
    for row in rows:
        new = dict(row)
        wti_yoy = new.get("WTI_YoY")
        brent_yoy = new.get("Brent_YoY")
        wti_ret = new.get("WTI_log_return_1m")
        brent_ret = new.get("Brent_log_return_1m")
        new["WTI_yoy_shock_dummy"] = 1.0 if is_number(wti_yoy) and abs(float(wti_yoy)) >= 50 else 0.0
        new["Brent_yoy_shock_dummy"] = 1.0 if is_number(brent_yoy) and abs(float(brent_yoy)) >= 50 else 0.0
        new["WTI_return_shock_dummy"] = 1.0 if is_number(wti_ret) and abs(float(wti_ret)) >= 10 else 0.0
        new["Brent_return_shock_dummy"] = 1.0 if is_number(brent_ret) and abs(float(brent_ret)) >= 10 else 0.0
        out.append(new)
    return out


def oil_equity_correlation_matrix(rows: list[Row]) -> list[Row]:
    pairs = [
        ("SP500_YoY", "WTI_YoY"),
        ("SP500_YoY", "Brent_YoY"),
        ("SP500_log_return_1m", "WTI_log_return_1m"),
        ("SP500_log_return_1m", "Brent_log_return_1m"),
    ]
    out = []
    for equity_col, oil_col in pairs:
        x, y = aligned_values(rows, equity_col, oil_col)
        corr, pvalue = pearson(x, y)
        out.append(
            {
                "section": "correlation_matrix",
                "equity_metric": equity_col,
                "oil_metric": oil_col,
                "lag_months": 0,
                "lag_convention": "zero = contemporaneous",
                "correlation": corr,
                "p_value": pvalue,
                "n_obs": len(x),
            }
        )
    return out


def oil_equity_lead_lag_rows(rows: list[Row], max_abs_lag: int) -> list[Row]:
    out: list[Row] = []
    pairs = [
        ("SP500_YoY", "WTI_YoY"),
        ("SP500_YoY", "Brent_YoY"),
        ("SP500_log_return_1m", "WTI_log_return_1m"),
        ("SP500_log_return_1m", "Brent_log_return_1m"),
    ]
    for equity_col, oil_col in pairs:
        for lag in range(-max_abs_lag, max_abs_lag + 1):
            x, y, months = lead_lag_values(rows, equity_col, oil_col, lag)
            corr, pvalue = pearson(x, y)
            out.append(
                {
                    "section": "lead_lag_correlation",
                    "equity_metric": equity_col,
                    "oil_metric": oil_col,
                    "lag_months": lag,
                    "lag_convention": "positive = stock market leads oil; negative = oil leads stock market",
                    "correlation": corr,
                    "p_value": pvalue,
                    "n_obs": len(x),
                    "sample": "full",
                }
            )
            for window in [60, 84, 120]:
                rolling = rolling_correlations(x, y, months, window)
                if rolling:
                    out.append(
                        {
                            "section": "rolling_lead_lag_correlation",
                            "equity_metric": equity_col,
                            "oil_metric": oil_col,
                            "lag_months": lag,
                            "lag_convention": "positive = stock market leads oil; negative = oil leads stock market",
                            "window_months": window,
                            "rolling_correlation_mean": float(np.mean([r[1] for r in rolling])),
                            "rolling_correlation_latest": rolling[-1][1],
                            "rolling_correlation_latest_month": rolling[-1][0],
                            "n_windows": len(rolling),
                        }
                    )
    return out


def oil_equity_return_lag_rows(rows: list[Row], max_abs_lag: int) -> list[Row]:
    out: list[Row] = []
    samples = [
        ("full", rows),
        ("normal_period", [r for r in rows if r.get("regime") == "normal_period"]),
        ("shock_periods", [r for r in rows if r.get("regime") != "normal_period"]),
    ]
    metrics = [
        ("monthly_log_return", "SP500_log_return_1m", "WTI_log_return_1m", -18, 18),
        ("monthly_log_return", "SP500_log_return_1m", "Brent_log_return_1m", -18, 18),
        ("quarterly_return", "SP500_quarterly_return", "WTI_quarterly_return", -6, 6),
        ("quarterly_return", "SP500_quarterly_return", "Brent_quarterly_return", -6, 6),
    ]
    quarterly = add_regime_fields(aggregate_oil_equity_quarterly(rows))
    for sample_name, sample_rows in samples:
        for metric, equity_col, oil_col, min_lag, max_lag in metrics:
            source_rows = sample_rows if metric == "monthly_log_return" else [r for r in quarterly if sample_name == "full" or (sample_name == "normal_period" and r.get("regime") == "normal_period") or (sample_name == "shock_periods" and r.get("regime") != "normal_period")]
            for lag in range(min_lag, max_lag + 1):
                x, y, _ = lead_lag_values(source_rows, equity_col, oil_col, lag)
                corr, pvalue = pearson(x, y)
                out.append(
                    {
                        "sample": sample_name,
                        "metric": metric,
                        "equity_metric": equity_col,
                        "oil_metric": oil_col,
                        "lag_periods": lag,
                        "lag_convention": "positive = stock market leads oil; negative = oil leads stock market",
                        "correlation": corr,
                        "p_value": pvalue,
                        "n_obs": len(x),
                    }
                )
    return out


def aggregate_oil_equity_quarterly(rows: list[Row]) -> list[Row]:
    buckets: dict[str, list[Row]] = {}
    for row in rows:
        buckets.setdefault(quarter_key(str(row["month"])), []).append(row)
    out: list[Row] = []
    for quarter, vals in sorted(buckets.items()):
        first = vals[0]
        last = vals[-1]
        out.append(
            {
                "month": quarter_to_month(quarter),
                "quarter": quarter,
                "SP500_quarterly_return": percent_return(first.get("SP500"), last.get("SP500")),
                "WTI_quarterly_return": percent_return(first.get("WTI"), last.get("WTI")),
                "Brent_quarterly_return": percent_return(first.get("Brent"), last.get("Brent")),
            }
        )
    return out


def percent_return(start: object, end: object) -> float | None:
    if not is_number(start) or not is_number(end) or float(start) == 0:
        return None
    return 100 * (float(end) / float(start) - 1)


def oil_equity_forecast_rows(rows: list[Row], max_abs_lag: int, gm2_lag: int) -> list[Row]:
    out: list[Row] = []
    for target in TARGETS:
        baseline = rolling_predictions(rows, target, [feature("GM2_YoY", gm2_lag, "GM2_YoY_lag5")], 60)
        if baseline:
            out.append(rolling_forecast_summary(target, "oil_forecast", "gm2_only_lag5", gm2_lag, 60, baseline, baseline))
        for lag in range(0, max_abs_lag + 1):
            sp = feature("SP500_YoY", lag, "SP500_YoY_lag")
            specs = [
                ("sp500_only", [sp]),
                ("gm2_plus_sp500", [feature("GM2_YoY", gm2_lag, "GM2_YoY_lag5"), sp]),
                ("gm2_plus_sp500_plus_ci", [feature("GM2_YoY", gm2_lag, "GM2_YoY_lag5"), sp, feature("CI_zscore", 0, "CI_zscore")]),
            ]
            for model, features in specs:
                pred = rolling_predictions(rows, target, features, 60)
                if pred:
                    out.append(rolling_forecast_summary(target, "oil_forecast", model, lag, 60, pred, baseline))
    return out


def oil_equity_reverse_rows(rows: list[Row], max_abs_lag: int) -> list[Row]:
    out: list[Row] = []
    for oil_col, prefix in [("WTI_YoY", "WTI"), ("Brent_YoY", "Brent")]:
        for lag in range(0, max_abs_lag + 1):
            pred = rolling_predictions(rows, "SP500_YoY", [feature(oil_col, lag, f"{oil_col}_lag")], 60)
            if pred:
                out.append(rolling_forecast_summary("SP500_YoY", "reverse_equity_forecast", f"{oil_col}_lag", lag, 60, pred, {}))
        for target in ["SP500_forward_3m_return", "SP500_forward_6m_return"]:
            features = [
                feature(oil_col, 0, oil_col),
                feature(f"{prefix}_yoy_shock_dummy", 0, f"{prefix}_yoy_shock_dummy"),
                feature(f"{prefix}_return_shock_dummy", 0, f"{prefix}_return_shock_dummy"),
                feature("financial_crisis_2008_2009", 0, "financial_crisis_2008_2009"),
                feature("shale_regime_2014_2017", 0, "shale_regime_2014_2017"),
                feature("covid_2020_2021", 0, "covid_2020_2021"),
                feature("war_spr_2022_2023", 0, "war_spr_2022_2023"),
            ]
            pred = rolling_predictions(rows, target, features, 60)
            if pred:
                out.append(rolling_forecast_summary(target, "forward_equity_return", f"{prefix}_oil_shock_regime", 0, 60, pred, {}))
            for regime in [*REGIMES, "normal_period"]:
                masked = [dict(r, **{target: r.get(target) if r.get("regime") == regime else None}) for r in rows]
                regime_pred = rolling_predictions(masked, target, features[:3], 60)
                if regime_pred:
                    row = rolling_forecast_summary(target, "forward_equity_return_regime", f"{prefix}_oil_shock_{regime}", 0, 60, regime_pred, {})
                    row["regime"] = regime
                    out.append(row)
    return out


def oil_equity_regime_rows(rows: list[Row]) -> list[Row]:
    out: list[Row] = []
    for regime in [*REGIMES, "normal_period"]:
        selected = [r for r in rows if r.get("regime") == regime]
        for equity_col, oil_col in [
            ("SP500_YoY", "WTI_YoY"),
            ("SP500_YoY", "Brent_YoY"),
            ("SP500_log_return_1m", "WTI_log_return_1m"),
            ("SP500_log_return_1m", "Brent_log_return_1m"),
        ]:
            x, y = aligned_values(selected, equity_col, oil_col)
            corr, pvalue = pearson(x, y)
            out.append(
                {
                    "section": "regime_correlation",
                    "regime": regime,
                    "equity_metric": equity_col,
                    "oil_metric": oil_col,
                    "lag_months": 0,
                    "correlation": corr,
                    "p_value": pvalue,
                    "n_obs": len(x),
                }
            )
    return out


def rolling_forecast_summary(target: str, section: str, model: str, lag: int, window: int, pred: Row, baseline: Row) -> Row:
    actual = np.array(pred["actuals"], dtype=float)
    forecast = np.array(pred["preds"], dtype=float)
    row: Row = {
        "section": section,
        "target": target,
        "model": model,
        "lag_months": lag,
        "window_months": window,
        "n_predictions": len(actual),
        "rolling_rmse": rmse(actual, forecast),
        "rolling_mae": mae(actual, forecast),
        "rolling_r2": r2_score(actual, forecast),
        "directional_accuracy": directional_accuracy(actual, forecast),
        "sign_accuracy": sign_accuracy(actual, forecast),
    }
    if baseline:
        base_lookup = dict(zip(baseline.get("months", []), baseline.get("preds", [])))
        months = [m for m in pred.get("months", []) if m in base_lookup]
        if months:
            model_lookup = dict(zip(pred["months"], pred["preds"]))
            actual_lookup = dict(zip(pred["months"], pred["actuals"]))
            base_pred = np.array([base_lookup[m] for m in months], dtype=float)
            model_pred = np.array([model_lookup[m] for m in months], dtype=float)
            matched_actual = np.array([actual_lookup[m] for m in months], dtype=float)
            base_rmse = rmse(matched_actual, base_pred)
            base_mae = mae(matched_actual, base_pred)
            row["baseline_gm2_lag5_rmse"] = base_rmse
            row["baseline_gm2_lag5_mae"] = base_mae
            row["rmse_improvement_vs_gm2_lag5"] = pct_improvement(base_rmse, rmse(matched_actual, model_pred))
            row["mae_improvement_vs_gm2_lag5"] = pct_improvement(base_mae, mae(matched_actual, model_pred))
    return row


def aligned_values(rows: list[Row], x_col: str, y_col: str) -> tuple[list[float], list[float]]:
    x: list[float] = []
    y: list[float] = []
    for row in rows:
        if is_number(row.get(x_col)) and is_number(row.get(y_col)):
            x.append(float(row[x_col]))
            y.append(float(row[y_col]))
    return x, y


def lead_lag_values(rows: list[Row], equity_col: str, oil_col: str, lag: int) -> tuple[list[float], list[float], list[str]]:
    x: list[float] = []
    y: list[float] = []
    months: list[str] = []
    for i, row in enumerate(rows):
        j = i - lag
        if j < 0 or j >= len(rows):
            continue
        equity = rows[j].get(equity_col)
        oil = row.get(oil_col)
        if is_number(equity) and is_number(oil):
            x.append(float(equity))
            y.append(float(oil))
            months.append(str(row["month"]))
    return x, y, months


def rolling_correlations(x: list[float], y: list[float], months: list[str], window: int) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    if len(x) < window:
        return out
    for end in range(window, len(x) + 1):
        corr, _ = pearson(x[end - window : end], y[end - window : end])
        if corr is not None:
            out.append((months[end - 1], corr))
    return out


def pearson(x: list[float], y: list[float]) -> tuple[float | None, float | None]:
    if len(x) < 3 or len(y) < 3:
        return None, None
    corr, pvalue = stats.pearsonr(np.array(x, dtype=float), np.array(y, dtype=float))
    return float(corr), float(pvalue)


def oil_equity_findings(rows: list[Row], gm2_lag: int) -> str:
    lead_rows = [r for r in rows if r.get("section") == "lead_lag_correlation" and r.get("equity_metric") == "SP500_YoY"]
    forecast_rows = [r for r in rows if r.get("section") == "oil_forecast" and r.get("model") in {"gm2_plus_sp500", "gm2_plus_sp500_plus_ci"}]
    reverse_rows = [r for r in rows if r.get("section") in {"forward_equity_return", "forward_equity_return_regime"}]
    lines = [
        "# Oil-Equity Lead-Lag Findings",
        "",
        "## Scope",
        "",
        "This layer tests whether oil leads stocks, stocks lead oil, or both mostly behave as coincident risk/growth assets responding to common macro and liquidity factors.",
        "",
        "## Lead-Lag Convention",
        "",
        "- Positive lag means the stock market leads oil.",
        "- Negative lag means oil leads the stock market.",
        "- Zero means contemporaneous.",
        "",
        "## Correlation Evidence",
        "",
    ]
    for oil_col in ["WTI_YoY", "Brent_YoY"]:
        subset = [r for r in lead_rows if r.get("oil_metric") == oil_col and is_number(r.get("correlation"))]
        if subset:
            best = max(subset, key=lambda r: abs(float(r["correlation"])))
            direction = "stocks lead oil" if int(best["lag_months"]) > 0 else "oil leads stocks" if int(best["lag_months"]) < 0 else "contemporaneous"
            lines.append(f"- SP500 YoY vs {oil_col}: strongest full-sample correlation is {best.get('correlation'):.3f} at lag {best.get('lag_months')} ({direction}).")
    lines.append("- Caution: YoY variables are overlapping and autocorrelated, so the lag result is a macro stress-pattern signal rather than a precise equity timing rule. Monthly and quarterly return robustness checks are in `analysis/oil_equity_robustness.md`.")
    lines.extend(["", "## Forecast Evidence", ""])
    for target in TARGETS:
        subset = [r for r in forecast_rows if r.get("target") == target and is_number(r.get("rolling_rmse"))]
        if subset:
            best = min(subset, key=lambda r: finite_or_inf(r.get("rolling_rmse")))
            rmse_imp = best.get("rmse_improvement_vs_gm2_lag5")
            mae_imp = best.get("mae_improvement_vs_gm2_lag5")
            useful = (is_number(rmse_imp) and float(rmse_imp) >= 0.05) or (is_number(mae_imp) and float(mae_imp) >= 0.05)
            verdict = "passes" if useful else "does not pass"
            lines.append(f"- {target}: best SP500-augmented model is `{best.get('model')}` at SP500 lag {best.get('lag_months')}; it {verdict} the 5% improvement rule versus locked GM2-only lag {gm2_lag}.")
    lines.extend(["", "## Reverse Direction", ""])
    if reverse_rows:
        best_reverse = min([r for r in reverse_rows if is_number(r.get("rolling_rmse"))], key=lambda r: finite_or_inf(r.get("rolling_rmse")), default=None)
        if best_reverse:
            regime_text = f" in {best_reverse.get('regime')}" if best_reverse.get("regime") else ""
            lines.append(f"- Best forward-equity-return oil specification is `{best_reverse.get('model')}` for {best_reverse.get('target')}{regime_text}, RMSE {best_reverse.get('rolling_rmse'):.3f}.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "If SP500-augmented oil models fail the 5% rolling RMSE/MAE rule, stocks should be treated as a coincident risk/growth proxy rather than an independent oil forecast signal.",
            "If oil helps predict forward equity returns mainly inside shock regimes, oil should be treated as a regime-risk signal for stocks rather than a general equity timing tool.",
        ]
    )
    return "\n".join(lines) + "\n"


def oil_equity_robustness_findings(rows: list[Row]) -> str:
    yoy_message = "The YoY lag result is useful for macro-cycle interpretation because YoY variables smooth monthly noise, but the same overlap also creates autocorrelation."
    lines = [
        "# Oil-Equity Robustness",
        "",
        "## Purpose",
        "",
        "This robustness pass checks the SP500-oil lead-lag result using return horizons that are less overlapping than YoY growth rates.",
        "",
        "## Main Caution",
        "",
        "The SP500 YoY versus oil YoY result peaks at lag -13 with a negative sign, meaning oil leads stocks by about 13 months under the project convention. Because YoY variables are overlapping and autocorrelated, this should be interpreted as a broad macro stress-pattern signal, not as a precise equity timing rule.",
        "",
        "## YoY Versus Return Lead-Lag",
        "",
        f"- YoY lead-lag: {yoy_message}",
        "- Monthly return lead-lag: more relevant for tradable market timing, but usually noisier and less stable.",
        "- Quarterly return lead-lag: a middle ground between noisy monthly returns and overlapping YoY cycles.",
        "",
        "## Return-Based Results",
        "",
    ]
    for metric in ["monthly_log_return", "quarterly_return"]:
        for oil_metric in ["WTI_log_return_1m", "Brent_log_return_1m", "WTI_quarterly_return", "Brent_quarterly_return"]:
            subset = [r for r in rows if r.get("metric") == metric and r.get("oil_metric") == oil_metric and r.get("sample") == "full" and is_number(r.get("correlation"))]
            if subset:
                best = max(subset, key=lambda r: abs(float(r["correlation"])))
                direction = "stocks lead oil" if int(best["lag_periods"]) > 0 else "oil leads stocks" if int(best["lag_periods"]) < 0 else "contemporaneous"
                lines.append(f"- {metric}, {oil_metric}: strongest full-sample correlation {best.get('correlation'):.3f} at lag {best.get('lag_periods')} ({direction}).")
    lines.extend(["", "## Normal Versus Shock Periods", ""])
    for oil_metric in ["WTI_log_return_1m", "Brent_log_return_1m"]:
        full = best_return_row(rows, "monthly_log_return", oil_metric, "full")
        normal = best_return_row(rows, "monthly_log_return", oil_metric, "normal_period")
        shock = best_return_row(rows, "monthly_log_return", oil_metric, "shock_periods")
        if full and normal and shock:
            survives = abs(float(normal.get("correlation") or 0)) >= 0.15 and int(normal.get("lag_periods") or 0) < 0
            verdict = "survives directionally outside shock regimes" if survives else "does not clearly survive outside shock regimes"
            lines.append(f"- {oil_metric}: full best lag {full.get('lag_periods')} corr {fmt(full.get('correlation'))}; normal-period best lag {normal.get('lag_periods')} corr {fmt(normal.get('correlation'))}; shock-period best lag {shock.get('lag_periods')} corr {fmt(shock.get('correlation'))}. Oil-leading-stocks {verdict}.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The YoY oil-leading-stocks pattern is best treated as an oil-shock stress signal for equities. Monthly and quarterly return checks are the better evidence for market timing, and they should be expected to be noisier and more regime-dependent.",
        ]
    )
    return "\n".join(lines) + "\n"


def best_return_row(rows: list[Row], metric: str, oil_metric: str, sample: str) -> Row:
    subset = [r for r in rows if r.get("metric") == metric and r.get("oil_metric") == oil_metric and r.get("sample") == sample and is_number(r.get("correlation"))]
    return max(subset, key=lambda r: abs(float(r["correlation"])), default={})


def energy_gdp_suite(
    monthly_rows: list[Row],
    gdpc1: Series,
    indpro: Series,
    total_energy: Series,
    oil_energy: Series,
) -> tuple[list[Row], list[Row], str]:
    monthly = add_regime_fields(build_energy_monthly_rows(monthly_rows, indpro, total_energy, oil_energy))
    quarterly = add_regime_fields(build_energy_quarterly_rows(monthly_rows, gdpc1, total_energy, oil_energy))
    lead_lag_rows = energy_time_series_rows(monthly, quarterly) + energy_gdp_lead_lag_rows(monthly, quarterly)
    model_rows = energy_gdp_model_rows(monthly, quarterly)
    findings = energy_gdp_findings(lead_lag_rows, model_rows, monthly, quarterly)
    return lead_lag_rows, model_rows, findings


def build_energy_monthly_rows(monthly_rows: list[Row], indpro: Series, total_energy: Series, oil_energy: Series) -> list[Row]:
    indpro_map = dict(indpro.observations)
    energy_map = dict(total_energy.observations)
    oil_energy_map = dict(oil_energy.observations)
    months = sorted({str(r["month"]) for r in monthly_rows} | set(indpro_map) | set(energy_map) | set(oil_energy_map))
    base = {str(r["month"]): r for r in monthly_rows}
    energy_values = [energy_map.get(m) for m in months]
    oil_values = [oil_energy_map.get(m) for m in months]
    indpro_values = [indpro_map.get(m) for m in months]
    energy_yoy = series_yoy(energy_values)
    oil_yoy = series_yoy(oil_values)
    indpro_yoy = series_yoy(indpro_values)
    out: list[Row] = []
    for i, month in enumerate(months):
        row = dict(base.get(month, {"month": month}))
        row.update(
            {
                "frequency": "monthly",
                "US_total_energy_consumption": energy_values[i],
                "US_oil_consumption": oil_values[i],
                "INDPRO": indpro_values[i],
                "Energy_consumption_growth": energy_yoy[i],
                "Oil_consumption_growth": oil_yoy[i],
                "Industrial_production_YoY": indpro_yoy[i],
            }
        )
        out.append(row)
    return out


def build_energy_quarterly_rows(monthly_rows: list[Row], gdpc1: Series, total_energy: Series, oil_energy: Series) -> list[Row]:
    gdp_map = {quarter_key(d): v for d, v in gdpc1.observations}
    energy_q = quarterly_sum(total_energy)
    oil_q = quarterly_sum(oil_energy)
    monthly_q = aggregate_monthly_rows_to_quarter(monthly_rows)
    quarters = sorted(set(gdp_map) | set(energy_q) | set(oil_q) | set(monthly_q))
    gdp_values = [gdp_map.get(q) for q in quarters]
    energy_values = [energy_q.get(q) for q in quarters]
    oil_values = [oil_q.get(q) for q in quarters]
    gdp_growth = series_yoy(gdp_values, periods=4)
    energy_growth = series_yoy(energy_values, periods=4)
    oil_growth = series_yoy(oil_values, periods=4)
    out: list[Row] = []
    for i, quarter in enumerate(quarters):
        base = monthly_q.get(quarter, {})
        gdp = gdp_values[i]
        energy = energy_values[i]
        wti = base.get("WTI")
        gdp_per_energy = float(gdp) / float(energy) if is_number(gdp) and is_number(energy) and float(energy) else None
        out.append(
            {
                "month": quarter_to_month(quarter),
                "quarter": quarter,
                "frequency": "quarterly",
                "Real_GDP": gdp,
                "Real_GDP_growth": gdp_growth[i],
                "US_total_energy_consumption": energy,
                "US_oil_consumption": oil_values[i],
                "Energy_consumption_growth": energy_growth[i],
                "Oil_consumption_growth": oil_growth[i],
                "Energy_intensity": float(energy) / float(gdp) if is_number(gdp) and is_number(energy) and float(gdp) else None,
                "GDP_per_energy": gdp_per_energy,
                "WTI": wti,
                "WTI_YoY": base.get("WTI_YoY"),
                "Brent_YoY": base.get("Brent_YoY"),
                "GM2_YoY": base.get("GM2_YoY"),
                "Industrial_production_YoY": base.get("Industrial_production_YoY"),
                "Oil_price_burden": float(wti) / gdp_per_energy if is_number(wti) and is_number(gdp_per_energy) and float(gdp_per_energy) else None,
                "Forward_Real_GDP_growth": gdp_growth[i + 1] if i + 1 < len(gdp_growth) else None,
            }
        )
    return out


def energy_gdp_lead_lag_rows(monthly: list[Row], quarterly: list[Row]) -> list[Row]:
    specs = [
        ("quarterly", quarterly, "Energy_consumption_growth", "Real_GDP_growth", -8, 8),
        ("monthly", monthly, "Energy_consumption_growth", "Industrial_production_YoY", -24, 24),
        ("quarterly", quarterly, "Oil_consumption_growth", "Real_GDP_growth", -8, 8),
        ("quarterly", quarterly, "WTI_YoY", "Real_GDP_growth", -8, 8),
        ("monthly", monthly, "WTI_YoY", "Industrial_production_YoY", -24, 24),
        ("monthly", monthly, "GM2_YoY", "Industrial_production_YoY", -24, 24),
        ("quarterly", quarterly, "GM2_YoY", "Real_GDP_growth", -8, 8),
    ]
    out: list[Row] = []
    for frequency, rows, predictor, target, min_lag, max_lag in specs:
        for lag in range(min_lag, max_lag + 1):
            x, y, _ = generic_lead_lag_values(rows, predictor, target, lag)
            corr, pvalue = pearson(x, y)
            out.append(
                {
                    "frequency": frequency,
                    "predictor": predictor,
                    "target": target,
                    "lag_periods": lag,
                    "lag_convention": "positive = predictor leads target; negative = target leads predictor",
                    "correlation": corr,
                    "p_value": pvalue,
                    "n_obs": len(x),
                    "section": "lead_lag",
                }
            )
    return out


def energy_time_series_rows(monthly: list[Row], quarterly: list[Row]) -> list[Row]:
    out: list[Row] = []
    for row in monthly:
        if any(is_number(row.get(col)) for col in ["Energy_consumption_growth", "Industrial_production_YoY", "WTI_YoY", "GM2_YoY"]):
            out.append(
                {
                    "section": "time_series",
                    "frequency": "monthly",
                    "period": row.get("month"),
                    "Energy_consumption_growth": row.get("Energy_consumption_growth"),
                    "Oil_consumption_growth": row.get("Oil_consumption_growth"),
                    "Industrial_production_YoY": row.get("Industrial_production_YoY"),
                    "WTI_YoY": row.get("WTI_YoY"),
                    "GM2_YoY": row.get("GM2_YoY"),
                    "regime": row.get("regime"),
                }
            )
    for row in quarterly:
        if any(is_number(row.get(col)) for col in ["Real_GDP_growth", "Energy_consumption_growth", "Energy_intensity", "GDP_per_energy"]):
            out.append(
                {
                    "section": "time_series",
                    "frequency": "quarterly",
                    "period": row.get("quarter"),
                    "month": row.get("month"),
                    "Real_GDP_growth": row.get("Real_GDP_growth"),
                    "Energy_consumption_growth": row.get("Energy_consumption_growth"),
                    "Oil_consumption_growth": row.get("Oil_consumption_growth"),
                    "Energy_intensity": row.get("Energy_intensity"),
                    "GDP_per_energy": row.get("GDP_per_energy"),
                    "Oil_price_burden": row.get("Oil_price_burden"),
                    "WTI_YoY": row.get("WTI_YoY"),
                    "GM2_YoY": row.get("GM2_YoY"),
                    "regime": row.get("regime"),
                }
            )
    return out


def energy_gdp_model_rows(monthly: list[Row], quarterly: list[Row]) -> list[Row]:
    out: list[Row] = []
    out.extend(activity_model_rows(monthly, "Industrial_production_YoY", "monthly", 60, range(0, 25)))
    out.extend(activity_model_rows(quarterly, "Real_GDP_growth", "quarterly", 32, range(0, 9)))
    out.extend(energy_demand_model_rows(monthly, "Industrial_production_YoY", "monthly", 60, range(0, 25)))
    out.extend(energy_demand_model_rows(quarterly, "Real_GDP_growth", "quarterly", 32, range(0, 9)))
    out.extend(oil_stress_model_rows(quarterly))
    out.extend(energy_regime_model_rows(monthly, quarterly))
    return [r for r in out if r]


def activity_model_rows(rows: list[Row], target: str, frequency: str, window: int, lags: range) -> list[Row]:
    out: list[Row] = []
    for lag in lags:
        features = [
            feature("Energy_consumption_growth", lag, "Energy_consumption_growth_lag"),
            feature("WTI_YoY", lag, "Oil_price_YoY_lag"),
            feature("GM2_YoY", min(lag, 5), "GM2_YoY_lag"),
        ]
        out.append(energy_model_summary(rows, target, features, "real_activity_model", lag, frequency, window))
    return out


def energy_demand_model_rows(rows: list[Row], activity_col: str, frequency: str, window: int, lags: range) -> list[Row]:
    out: list[Row] = []
    for lag in lags:
        features = [
            feature(activity_col, lag, "Real_activity_growth_lag"),
            feature("WTI_YoY", lag, "Oil_price_YoY_lag"),
            feature("GM2_YoY", min(lag, 5), "GM2_YoY_lag"),
        ]
        out.append(energy_model_summary(rows, "Energy_consumption_growth", features, "energy_demand_model", lag, frequency, window))
    return out


def oil_stress_model_rows(quarterly: list[Row]) -> list[Row]:
    features = [
        feature("WTI_YoY", 0, "Oil_price_YoY"),
        feature("Oil_price_burden", 0, "Oil_price_burden"),
        feature("GM2_YoY", 1, "GM2_YoY_lag5_proxy"),
        feature("financial_crisis_2008_2009", 0, "financial_crisis_2008_2009"),
        feature("shale_regime_2014_2017", 0, "shale_regime_2014_2017"),
        feature("covid_2020_2021", 0, "covid_2020_2021"),
        feature("war_spr_2022_2023", 0, "war_spr_2022_2023"),
    ]
    return [energy_model_summary(quarterly, "Forward_Real_GDP_growth", features, "oil_stress_model", 0, "quarterly", 32)]


def energy_regime_model_rows(monthly: list[Row], quarterly: list[Row]) -> list[Row]:
    out: list[Row] = []
    for regime in [*REGIMES, "normal_period"]:
        m = [dict(r, **{"Industrial_production_YoY": r.get("Industrial_production_YoY") if r.get("regime") == regime else None}) for r in monthly]
        q = [dict(r, **{"Real_GDP_growth": r.get("Real_GDP_growth") if r.get("regime") == regime else None}) for r in quarterly]
        row_m = energy_model_summary(m, "Industrial_production_YoY", [feature("Energy_consumption_growth", 0), feature("WTI_YoY", 0), feature("GM2_YoY", 5)], "regime_real_activity_model", 0, "monthly", 24)
        row_q = energy_model_summary(q, "Real_GDP_growth", [feature("Energy_consumption_growth", 0), feature("WTI_YoY", 0), feature("GM2_YoY", 1)], "regime_real_activity_model", 0, "quarterly", 8)
        row_m["regime"] = regime
        row_q["regime"] = regime
        out.extend([row_m, row_q])
    return out


def energy_model_summary(rows: list[Row], target: str, features: list[Row], model: str, lag: int, frequency: str, window: int) -> Row:
    summary = fit_summary(rows, target, model, features, lag, "energy_gdp")
    if not summary:
        return {}
    pred = rolling_predictions(rows, target, features, window)
    summary["frequency"] = frequency
    summary["window_periods"] = window
    if pred:
        actual = np.array(pred["actuals"], dtype=float)
        forecast = np.array(pred["preds"], dtype=float)
        summary["rolling_rmse"] = rmse(actual, forecast)
        summary["rolling_mae"] = mae(actual, forecast)
        summary["rolling_r2"] = r2_score(actual, forecast)
        summary["directional_accuracy"] = directional_accuracy(actual, forecast)
        summary["sign_accuracy"] = sign_accuracy(actual, forecast)
        summary["n_rolling_predictions"] = len(actual)
    return summary


def energy_gdp_findings(lead_lag_rows: list[Row], model_rows: list[Row], monthly: list[Row], quarterly: list[Row]) -> str:
    lines = [
        "# Energy-GDP Lead-Lag Findings",
        "",
        "## Physical-Economy Hypothesis",
        "",
        "This layer tests whether energy use behaves like the physical throughput base of measured real activity, while GDP per unit of energy captures efficiency, technology, and partial decoupling.",
        "",
        "## Lead-Lag Evidence",
        "",
    ]
    for predictor, target in [
        ("Energy_consumption_growth", "Real_GDP_growth"),
        ("Energy_consumption_growth", "Industrial_production_YoY"),
        ("Oil_consumption_growth", "Real_GDP_growth"),
        ("WTI_YoY", "Real_GDP_growth"),
        ("WTI_YoY", "Industrial_production_YoY"),
        ("GM2_YoY", "Industrial_production_YoY"),
        ("GM2_YoY", "Real_GDP_growth"),
    ]:
        subset = [r for r in lead_lag_rows if r.get("predictor") == predictor and r.get("target") == target and is_number(r.get("correlation"))]
        if subset:
            best = max(subset, key=lambda r: abs(float(r["correlation"])))
            lines.append(f"- {predictor} vs {target}: strongest correlation {best.get('correlation'):.3f} at lag {best.get('lag_periods')} ({best.get('frequency')}).")
    latest_q = latest_with_values(quarterly, ["Energy_intensity", "GDP_per_energy"])
    first_q = first_with_values(quarterly, ["Energy_intensity", "GDP_per_energy"])
    if latest_q and first_q:
        direction = "higher" if float(latest_q["GDP_per_energy"]) > float(first_q["GDP_per_energy"]) else "lower"
        lines.extend(
            [
                "",
                "## Energy Intensity",
                "",
                f"- GDP per energy is {direction} at the latest usable quarter ({latest_q.get('quarter')}) than at the beginning of the sample, consistent with efficiency gains, structural change, or partial decoupling.",
            ]
        )
    lines.extend(["", "## Model Evidence", ""])
    for target in ["Real_GDP_growth", "Industrial_production_YoY", "Energy_consumption_growth", "Forward_Real_GDP_growth"]:
        subset = [r for r in model_rows if r.get("target") == target and is_number(r.get("rolling_rmse"))]
        if subset:
            best = min(subset, key=lambda r: finite_or_inf(r.get("rolling_rmse")))
            lines.append(f"- {target}: best rolling model `{best.get('model')}` ({best.get('frequency')}) RMSE {best.get('rolling_rmse'):.3f}, MAE {best.get('rolling_mae'):.3f}.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If energy consumption and GDP are tightly linked at quarterly scale, energy should be described as the physical throughput base of GDP.",
            "- Rising GDP per energy means efficiency and structural change allow more GDP per unit of energy.",
            "- If oil prices predict weaker future activity mainly during high-burden or shock regimes, oil should be described as a stress signal rather than a universal GDP predictor.",
            "",
            "## Model Hierarchy",
            "",
            "GM2 leads oil momentum. CI explains oil residual/state. SP500 reflects risk appetite. Energy anchors real activity. GDP records the measured economic outcome.",
        ]
    )
    return "\n".join(lines) + "\n"


def integrated_synthesis_suite(
    lag_rows: list[Row],
    rolling_extended_rows: list[Row],
    residual_diagnostic_rows: list[Row],
    oil_equity_rows: list[Row],
    energy_gdp_rows: list[Row],
) -> tuple[list[Row], str, str]:
    hierarchy = system_signal_hierarchy_rows(lag_rows, rolling_extended_rows, residual_diagnostic_rows, oil_equity_rows, energy_gdp_rows)
    atlas = integrated_lead_lag_atlas(hierarchy)
    interpretation = final_system_interpretation(hierarchy)
    return hierarchy, atlas, interpretation


def system_signal_hierarchy_rows(
    lag_rows: list[Row],
    rolling_extended_rows: list[Row],
    residual_diagnostic_rows: list[Row],
    oil_equity_rows: list[Row],
    energy_gdp_rows: list[Row],
) -> list[Row]:
    wti_lag5 = next(
        (
            r for r in rolling_extended_rows
            if r.get("target") == "WTI_YoY"
            and r.get("model") == "gm2_only"
            and r.get("lag_months") == 5
            and r.get("window_months") == 60
            and r.get("sample") == "all"
        ),
        {},
    )
    brent_lag5 = next(
        (
            r for r in rolling_extended_rows
            if r.get("target") == "Brent_YoY"
            and r.get("model") == "gm2_only"
            and r.get("lag_months") == 5
            and r.get("window_months") == 60
            and r.get("sample") == "all"
        ),
        {},
    )
    wti_peak = peak_lag_row(lag_rows, "WTI_YoY")
    brent_peak = peak_lag_row(lag_rows, "Brent_YoY")
    wti_resid = next((r for r in residual_diagnostic_rows if r.get("oil_target") == "WTI_YoY"), {})
    brent_resid = next((r for r in residual_diagnostic_rows if r.get("oil_target") == "Brent_YoY"), {})
    sp500_wti = peak_oil_equity_row(oil_equity_rows, "WTI_YoY")
    sp500_brent = peak_oil_equity_row(oil_equity_rows, "Brent_YoY")
    energy_gdp = peak_energy_row(energy_gdp_rows, "Energy_consumption_growth", "Real_GDP_growth")
    oil_gdp = peak_energy_row(energy_gdp_rows, "Oil_consumption_growth", "Real_GDP_growth")
    energy_indpro = peak_energy_row(energy_gdp_rows, "Energy_consumption_growth", "Industrial_production_YoY")
    rows = [
        {
            "layer": "Liquidity impulse",
            "signal": "G4 GM2 YoY",
            "target": "Oil YoY momentum",
            "relationship": "leads",
            "lead_lag": "locked lag 5 months; simple correlation peak 4 months",
            "metric": "WTI rolling RMSE / Brent rolling RMSE",
            "value": f"{fmt(wti_lag5.get('rolling_rmse'))} / {fmt(brent_lag5.get('rolling_rmse'))}",
            "interpretation": "Global M2 is the strongest leading financial signal for oil-price momentum.",
        },
        {
            "layer": "Oil momentum validation",
            "signal": "GM2 lag correlation",
            "target": "WTI / Brent YoY",
            "relationship": "leads",
            "lead_lag": f"WTI peak {wti_peak.get('lag_months')}m; Brent peak {brent_peak.get('lag_months')}m",
            "metric": "Pearson correlation",
            "value": f"{fmt(wti_peak.get('correlation'))} / {fmt(brent_peak.get('correlation'))}",
            "interpretation": "Correlation peaks slightly earlier than rolling forecast selection, but both point to a leading liquidity impulse.",
        },
        {
            "layer": "Physical oil-market state",
            "signal": "Comparative inventory",
            "target": "Oil residual vs GM2 path",
            "relationship": "diagnoses residual/state",
            "lead_lag": "same-month state variable",
            "metric": "Residual explained variance WTI / Brent",
            "value": f"{fmt(wti_resid.get('residual_explained_variance'))} / {fmt(brent_resid.get('residual_explained_variance'))}",
            "interpretation": "Inventory helps explain rich/cheap deviations but is not promoted to the primary forecast model.",
        },
        {
            "layer": "Market pricing layer",
            "signal": "SP500",
            "target": "Oil YoY and equity risk",
            "relationship": "coincident risk/growth proxy",
            "lead_lag": f"strongest SP500-oil correlation at WTI lag {sp500_wti.get('lag_months')}; Brent lag {sp500_brent.get('lag_months')}",
            "metric": "Peak correlation WTI / Brent",
            "value": f"{fmt(sp500_wti.get('correlation'))} / {fmt(sp500_brent.get('correlation'))}",
            "interpretation": "Stocks add context around risk appetite and growth expectations but do not improve the locked oil model by the 5% rule.",
        },
        {
            "layer": "Physical economy layer",
            "signal": "Energy consumption",
            "target": "Real GDP",
            "relationship": "moves with / anchors",
            "lead_lag": f"best lag {energy_gdp.get('lag_periods')} quarters",
            "metric": "Correlation",
            "value": fmt(energy_gdp.get("correlation")),
            "interpretation": "Energy use is the physical throughput base of GDP at quarterly scale.",
        },
        {
            "layer": "Physical economy layer",
            "signal": "Petroleum consumption",
            "target": "Real GDP",
            "relationship": "moves with / anchors",
            "lead_lag": f"best lag {oil_gdp.get('lag_periods')} quarters",
            "metric": "Correlation",
            "value": fmt(oil_gdp.get("correlation")),
            "interpretation": "Petroleum consumption growth has the strongest current real-economy relationship in the energy layer.",
        },
        {
            "layer": "Industrial activity",
            "signal": "Energy consumption",
            "target": "Industrial production",
            "relationship": "moves with",
            "lead_lag": f"best lag {energy_indpro.get('lag_periods')} months",
            "metric": "Correlation",
            "value": fmt(energy_indpro.get("correlation")),
            "interpretation": "Industrial production is the higher-frequency activity proxy tied to physical energy throughput.",
        },
        {
            "layer": "Measured outcome",
            "signal": "GDP per energy",
            "target": "Efficiency / structural change",
            "relationship": "trend over time",
            "lead_lag": "long-run trend",
            "metric": "Direction",
            "value": "rising",
            "interpretation": "Rising GDP per unit of energy shows efficiency gains and structural change, not full physical decoupling.",
        },
    ]
    return rows


def integrated_lead_lag_atlas(hierarchy: list[Row]) -> str:
    return "\n".join(
        [
            "# Integrated Lead-Lag Atlas",
            "",
            "## Core Interpretation",
            "",
            "Global M2 is the strongest leading financial signal for oil-price momentum. Stocks mostly reflect risk appetite and growth expectations, adding context rather than improving the locked oil model. Comparative inventory describes the physical oil-market state and helps explain deviations from the GM2-implied price path. Energy consumption anchors real activity, while GDP records the measured economic outcome. Rising GDP per unit of energy shows efficiency and structural change, while the continuing high correlation between energy use and GDP shows the economy remains physically grounded in energy throughput.",
            "",
            "## Which Signals Lead Oil?",
            "",
            "- G4 GM2 YoY is the primary leading signal. The final oil model is locked at GM2-only lag 5, with simple lag correlations peaking around 4 months.",
            "- SP500 does not qualify as an independent oil forecast signal because SP500-augmented models do not clear the 5% rolling RMSE/MAE improvement rule versus locked GM2-only lag 5.",
            "",
            "## Which Signals Move With Oil?",
            "",
            "- Stocks and oil share a market-pricing layer: both respond to risk appetite, inflation/growth expectations, and macro-financial conditions.",
            "- Oil and industrial activity have some contemporaneous or near-contemporaneous relationship, but this belongs more to the real-activity layer than the locked oil-price forecast.",
            "",
            "## Which Signals Lag Or Record The Outcome?",
            "",
            "- Real GDP records the measured economic outcome at quarterly frequency.",
            "- Industrial production gives a higher-frequency real-activity read.",
            "- Energy consumption and petroleum consumption move closely with GDP, showing the physical throughput base beneath measured output.",
            "",
            "## Where Do Stocks Fit?",
            "",
            "Stocks fit as a coincident risk/growth proxy. The full-sample SP500 YoY versus oil YoY test shows the strongest lag correlation at negative lag, meaning oil leads stocks under the project convention, but the sign is negative. Because YoY variables are overlapping and autocorrelated, this is best interpreted as a broad macro stress-pattern signal for equities, not as a precise equity timing rule.",
            "",
            "YoY lead-lag is useful for macro cycle interpretation because it smooths short-term noise and emphasizes broad expansions or contractions. Monthly return lead-lag is more relevant for market timing because it uses non-overlapping one-month changes, but it is also noisier and more regime-dependent.",
            "",
            "## Where Does Comparative Inventory Fit?",
            "",
            "Comparative inventory is a physical oil-market state variable. It explains residuals around the GM2-implied oil path and helps diagnose rich/cheap oil pricing, but it is not the primary Oil YoY forecast variable.",
            "",
            "## How Energy And GDP Fit",
            "",
            "Energy use anchors real activity. Petroleum consumption growth and real GDP growth have the strongest current energy-GDP relationship, while GDP per energy rises over time. The synthesis is that GDP remains physically grounded in energy throughput, while efficiency and structural change allow more measured GDP per unit of energy.",
            "",
            "## Signal Hierarchy",
            "",
            *[f"- {r['layer']}: {r['signal']} -> {r['target']} ({r['relationship']}; {r['metric']} {r['value']}). {r['interpretation']}" for r in hierarchy],
        ]
    ) + "\n"


def final_system_interpretation(hierarchy: list[Row]) -> str:
    return "\n".join(
        [
            "# Final System Interpretation",
            "",
            "## Integrated View",
            "",
            "The model hierarchy is now a layered macro system rather than a single-variable oil forecast.",
            "",
            "1. Liquidity impulse: GM2 leads oil momentum.",
            "2. Market pricing layer: stocks and oil respond to growth/risk conditions.",
            "3. Physical economy layer: energy use anchors industrial activity and GDP.",
            "",
            "## Final Interpretation",
            "",
            "Global M2 is the strongest leading financial signal for oil-price momentum. Stocks mostly reflect risk appetite and growth expectations, adding context rather than improving the locked oil model. Comparative inventory describes the physical oil-market state and helps explain deviations from the GM2-implied price path. Energy consumption anchors real activity, while GDP records the measured economic outcome. Rising GDP per unit of energy shows efficiency and structural change, while the continuing high correlation between energy use and GDP shows the economy remains physically grounded in energy throughput.",
            "",
            "## Practical Reading",
            "",
            "- Use GM2 to frame the oil momentum impulse.",
            "- Use comparative inventory to judge whether physical oil conditions amplify, dampen, or contradict that impulse.",
            "- Use SP500 as a risk/growth context variable, not as an independent oil forecast upgrade.",
            "- Use energy and petroleum consumption to anchor the real-economy layer.",
            "- Use GDP as the measured outcome, with GDP per energy tracking efficiency and structural change over time.",
        ]
    ) + "\n"


def peak_lag_row(rows: list[Row], target: str) -> Row:
    subset = [r for r in rows if r.get("target") == target and is_number(r.get("correlation"))]
    return max(subset, key=lambda r: abs(float(r["correlation"])), default={})


def peak_oil_equity_row(rows: list[Row], oil_metric: str) -> Row:
    subset = [
        r for r in rows
        if r.get("section") == "lead_lag_correlation"
        and r.get("equity_metric") == "SP500_YoY"
        and r.get("oil_metric") == oil_metric
        and is_number(r.get("correlation"))
    ]
    return max(subset, key=lambda r: abs(float(r["correlation"])), default={})


def peak_energy_row(rows: list[Row], predictor: str, target: str) -> Row:
    subset = [
        r for r in rows
        if r.get("section") == "lead_lag"
        and r.get("predictor") == predictor
        and r.get("target") == target
        and is_number(r.get("correlation"))
    ]
    return max(subset, key=lambda r: abs(float(r["correlation"])), default={})


def series_yoy(values: list[float | None], periods: int = 12) -> list[float | None]:
    out: list[float | None] = []
    for i, value in enumerate(values):
        prev = values[i - periods] if i >= periods else None
        if value is None or prev in (None, 0):
            out.append(None)
        else:
            out.append(100 * (float(value) / float(prev) - 1))
    return out


def quarter_key(date: str) -> str:
    month = int(date[5:7]) if len(date) >= 7 else 1
    return f"{date[:4]}Q{((month - 1) // 3) + 1}"


def quarter_to_month(quarter: str) -> str:
    q = int(quarter[-1])
    return f"{quarter[:4]}-{q * 3:02d}"


def quarterly_sum(series: Series) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for month, value in series.observations:
        buckets.setdefault(quarter_key(month), []).append(value)
    return {q: sum(v) for q, v in buckets.items() if len(v) == 3}


def aggregate_monthly_rows_to_quarter(rows: list[Row]) -> dict[str, Row]:
    buckets: dict[str, list[Row]] = {}
    for row in rows:
        buckets.setdefault(quarter_key(str(row["month"])), []).append(row)
    out: dict[str, Row] = {}
    for quarter, vals in buckets.items():
        agg: Row = {"quarter": quarter}
        for col in ["WTI", "WTI_YoY", "Brent_YoY", "GM2_YoY", "Industrial_production_YoY"]:
            nums = [float(r[col]) for r in vals if is_number(r.get(col))]
            agg[col] = sum(nums) / len(nums) if nums else None
        out[quarter] = agg
    return out


def generic_lead_lag_values(rows: list[Row], predictor: str, target: str, lag: int) -> tuple[list[float], list[float], list[str]]:
    x: list[float] = []
    y: list[float] = []
    periods: list[str] = []
    for i, row in enumerate(rows):
        j = i - lag
        if j < 0 or j >= len(rows):
            continue
        p = rows[j].get(predictor)
        t = row.get(target)
        if is_number(p) and is_number(t):
            x.append(float(p))
            y.append(float(t))
            periods.append(str(row.get("quarter") or row.get("month")))
    return x, y, periods


def first_with_values(rows: list[Row], cols: list[str]) -> Row:
    for row in rows:
        if all(is_number(row.get(c)) for c in cols):
            return row
    return {}


def latest_with_values(rows: list[Row], cols: list[str]) -> Row:
    for row in reversed(rows):
        if all(is_number(row.get(c)) for c in cols):
            return row
    return {}


def final_findings_rows(
    rows: list[Row],
    lag_rows: list[Row],
    rolling_extended_rows: list[Row],
    residual_diagnostic_rows: list[Row],
    best_lag: int,
) -> list[Row]:
    out: list[Row] = []
    for target in TARGETS:
        corr_rows = [r for r in lag_rows if r.get("target") == target and is_number(r.get("correlation"))]
        peak = max(corr_rows, key=lambda r: abs(float(r["correlation"]))) if corr_rows else {}
        locked = [
            r
            for r in rolling_extended_rows
            if r.get("target") == target
            and r.get("model") == "gm2_only"
            and r.get("lag_months") == best_lag
            and r.get("window_months") == 60
            and r.get("sample") == "all"
        ]
        diag = next((r for r in residual_diagnostic_rows if r.get("oil_target") == target), {})
        row: Row = {
            "target": target,
            "locked_model": "gm2_only",
            "locked_lag_months": best_lag,
            "peak_correlation_lag_months": peak.get("lag_months"),
            "peak_correlation": peak.get("correlation"),
            "rolling_rmse_60m": locked[0].get("rolling_rmse") if locked else None,
            "rolling_mae_60m": locked[0].get("rolling_mae") if locked else None,
            "rolling_r2_60m": locked[0].get("rolling_r2") if locked else None,
            "directional_accuracy_60m": locked[0].get("directional_accuracy") if locked else None,
            "sign_accuracy_60m": locked[0].get("sign_accuracy") if locked else None,
            "residual_explained_variance_ci_regime": diag.get("residual_explained_variance"),
            "residual_directional_accuracy_ci_regime": diag.get("residual_directional_accuracy"),
            "final_role_for_ci": "market-state diagnostic / residual explainer / regime signal",
            "primary_decision": "Use GM2-only lag 5 for Oil_YoY momentum; use CI to interpret residuals and regime risk.",
        }
        out.append(row)
    latest = latest_complete_signal_row(rows)
    pred = latest_locked_prediction(rows, "WTI_YoY", best_lag, str(latest.get("month")))
    out.append(
        {
            "target": "current_signal_snapshot",
            "locked_model": "gm2_only",
            "locked_lag_months": best_lag,
            "latest_complete_month": latest.get("month"),
            "latest_gm2_usd": latest.get("GM2_USD"),
            "latest_gm2_yoy": latest.get("GM2_YoY"),
            "latest_wti_yoy": latest.get("WTI_YoY"),
            "latest_brent_yoy": latest.get("Brent_YoY"),
            "latest_comparative_inventory_kb": latest.get("comparative_inventory_kb"),
            "latest_ci_zscore": latest.get("CI_zscore"),
            "model_implied_wti_yoy": pred.get("predicted"),
            "actual_wti_yoy": pred.get("actual"),
            "wti_residual": pred.get("residual"),
            "regime": latest.get("regime"),
            "ci_interpretation": ci_state_text(latest),
        }
    )
    return out


def latest_complete_signal_row(rows: list[Row]) -> Row:
    required = ["GM2_USD", "GM2_YoY", "WTI_YoY", "Brent_YoY", "comparative_inventory_kb", "CI_zscore"]
    for row in reversed(rows):
        if all(is_number(row.get(col)) for col in required):
            return row
    return {}


def latest_locked_prediction(rows: list[Row], target: str, best_lag: int, month: str | None = None) -> Row:
    pred = rolling_predictions(rows, target, [feature("GM2_YoY", best_lag, "GM2_YoY_lag")], 60)
    if not pred:
        return {}
    selected_month = month if month in pred["months"] else pred["months"][-1]
    idx = pred["months"].index(selected_month)
    actual = float(pred["actuals"][idx])
    predicted = float(pred["preds"][idx])
    return {"month": selected_month, "actual": actual, "predicted": predicted, "residual": actual - predicted}


def executive_summary(final_rows: list[Row], snapshot: str, best_lag: int) -> str:
    wti = next((r for r in final_rows if r.get("target") == "WTI_YoY"), {})
    brent = next((r for r in final_rows if r.get("target") == "Brent_YoY"), {})
    current = next((r for r in final_rows if r.get("target") == "current_signal_snapshot"), {})
    return "\n".join(
        [
            "# Executive Summary",
            "",
            "## Headline",
            "",
            f"The strongest stable lead-time range for G4 GM2 is 5 to 6 months in rolling validation, with the locked final reporting model set to GM2-only lag {best_lag}. Simple lag correlation peaks at 4 months for both WTI and Brent.",
            "",
            "## GM2-Only Performance",
            "",
            f"- WTI YoY, GM2-only lag {best_lag}: rolling RMSE {fmt(wti.get('rolling_rmse_60m'))}, MAE {fmt(wti.get('rolling_mae_60m'))}, directional accuracy {fmt_pct(wti.get('directional_accuracy_60m'))}.",
            f"- Brent YoY, GM2-only lag {best_lag}: rolling RMSE {fmt(brent.get('rolling_rmse_60m'))}, MAE {fmt(brent.get('rolling_mae_60m'))}, directional accuracy {fmt_pct(brent.get('directional_accuracy_60m'))}.",
            "",
            "## Comparative Inventory Role",
            "",
            "Comparative inventory does not improve primary Oil_YoY rolling RMSE or MAE versus GM2-only by the 5% rule. Its useful role is diagnostic: it helps explain whether oil is rich or cheap versus the liquidity-implied path, especially when combined with regime labels.",
            "",
            "## Where The Model Fails",
            "",
            "The model is weakest around abrupt geopolitical, pandemic, financial-crisis, shale-cycle, and policy shocks. It also does not directly model OPEC behavior, spare capacity, refining margins, curve structure, global inventories, sanctions, or shipping disruptions.",
            "",
            "## Current Signal",
            "",
            f"As of {current.get('latest_complete_month')}, WTI YoY is {fmt(current.get('actual_wti_yoy'))}. The locked GM2-only model implies {fmt(current.get('model_implied_wti_yoy'))}, leaving a residual of {fmt(current.get('wti_residual'))}. Inventory state: {current.get('ci_interpretation')}.",
            "",
            "## What To Watch Next",
            "",
            "- Whether G4 GM2 YoY keeps accelerating or rolls over, because the locked model reads that impulse with a 5-month lead.",
            "- Whether comparative inventory stays in surplus or deficit, because that frames residual risk around the liquidity path.",
            "- Whether the current period resembles a shock regime where the simple liquidity relationship is more likely to break.",
            "- Whether Brent and WTI residuals diverge, which can signal location-specific physical-market stress rather than broad liquidity momentum.",
        ]
    ) + "\n"


def model_card(final_rows: list[Row], best_lag: int) -> str:
    wti = next((r for r in final_rows if r.get("target") == "WTI_YoY"), {})
    brent = next((r for r in final_rows if r.get("target") == "Brent_YoY"), {})
    return "\n".join(
        [
            "# Model Card",
            "",
            "## Purpose",
            "",
            "Interpret monthly oil-price momentum through a global-liquidity signal, then use comparative inventory and regime context to diagnose residual deviations.",
            "",
            "## Data Sources",
            "",
            "- FRED: U.S. M2 `M2SL`, FX `DEXUSEU`/`DEXCHUS`/`DEXJPUS`, WTI `DCOILWTICO`, Brent `DCOILBRENTEU`, CPI `CPIAUCSL`.",
            "- ECB Data Portal: euro area M2.",
            "- Bank of Japan: Japan M2.",
            "- ChinaData/PBoC proxy plus IMF/FRED history: China M2.",
            "- EIA: U.S. crude stocks excluding SPR `WCESTUS1`.",
            "",
            "## Core Formulas",
            "",
            "- `GM2_USD = US_M2_USD + EA_M2_EUR*EURUSD + CN_M2_CNY/CNY_per_USD + JP_M2_JPY/JPY_per_USD`.",
            "- `GM2_YoY = 100 * (GM2_USD / GM2_USD[t-12] - 1)`.",
            "- `Oil_YoY = 100 * (monthly oil price / monthly oil price[t-12] - 1)`.",
            "- `comparative_inventory = current inventory - prior five-year same-month average`.",
            "- `CI_zscore = comparative_inventory / prior five-year same-month standard deviation`.",
            "",
            "## Target Definitions",
            "",
            "- Primary target: WTI YoY and Brent YoY.",
            "- Diagnostic targets: GM2-implied residuals, nominal price levels, CPI-deflated price levels, trailing 12-month deviations, and forward 3-month/6-month returns.",
            "",
            "## Lag Convention",
            "",
            f"`GM2_YoY_lag_{best_lag}` means oil at month `t` is predicted using GM2 YoY from `t-{best_lag}`. The final reporting model is locked at lag {best_lag}.",
            "",
            "## Validation Method",
            "",
            "Primary validation uses 60-month rolling one-step predictions. Supporting checks include 84-month and 120-month rolling windows, chronological train/test splits, directional accuracy, sign accuracy, paired error comparisons, HAC standard errors, high-leverage month flags, and shock-excluded reruns.",
            "",
            "## Current Best Model",
            "",
            f"- WTI YoY: GM2-only lag {best_lag}, rolling RMSE {fmt(wti.get('rolling_rmse_60m'))}, MAE {fmt(wti.get('rolling_mae_60m'))}.",
            f"- Brent YoY: GM2-only lag {best_lag}, rolling RMSE {fmt(brent.get('rolling_rmse_60m'))}, MAE {fmt(brent.get('rolling_mae_60m'))}.",
            "",
            "## Known Caveats",
            "",
            "- G4 M2 is a proxy, not a harmonized monetary aggregate.",
            "- USD conversion blends domestic money growth with FX moves.",
            "- U.S. comparative inventory is not global oil inventory.",
            "- Monthly averaging can hide intra-month shocks.",
            "- Linear OLS models are descriptive and can miss nonlinear policy/geopolitical breaks.",
            "",
            "## Shock Periods",
            "",
            "- Financial crisis: 2008-2009.",
            "- Shale regime: 2014-2017.",
            "- Covid shock: 2020-2021.",
            "- War/SPR period: 2022-2023.",
            "",
            "## Suitable Uses",
            "",
            "- Monthly macro/commodity research.",
            "- Interpreting oil momentum relative to global liquidity.",
            "- Diagnosing rich/cheap residuals using inventory and regime state.",
            "- Scenario framing for human analysts.",
            "",
            "## Unsuitable Uses",
            "",
            "- Short-term trading signals.",
            "- Standalone price forecasts without analyst review.",
            "- Replacing physical oil-market analysis.",
            "- Forecasting during acute geopolitical or policy shocks without overrides.",
        ]
    ) + "\n"


def current_signal_snapshot(rows: list[Row], best_lag: int) -> str:
    latest = latest_complete_signal_row(rows)
    prediction = latest_locked_prediction(rows, "WTI_YoY", best_lag, str(latest.get("month")))
    lagged_month = month_shift(str(latest.get("month")), -best_lag) if latest else None
    residual = prediction.get("residual")
    residual_text = residual_interpretation(residual)
    return "\n".join(
        [
            "# Current Signal Snapshot",
            "",
            f"The latest complete signal month is {latest.get('month')}. G4 GM2 is {fmt_usd(latest.get('GM2_USD'))}, with GM2 YoY at {fmt(latest.get('GM2_YoY'))}.",
            "",
            f"WTI YoY is {fmt(latest.get('WTI_YoY'))} and Brent YoY is {fmt(latest.get('Brent_YoY'))}. Comparative inventory is {fmt(latest.get('comparative_inventory_kb'))} thousand barrels versus the prior five-year same-month norm, with a CI z-score of {fmt(latest.get('CI_zscore'))}.",
            "",
            f"Using the locked GM2-only lag-{best_lag} model, GM2 from {lagged_month} implies WTI YoY of {fmt(prediction.get('predicted'))}. Actual WTI YoY is {fmt(prediction.get('actual'))}, so the residual is {fmt(residual)} percentage points.",
            "",
            f"Residual interpretation: {residual_text} Inventory interpretation: {ci_state_text(latest)}. Regime state: {latest.get('regime', 'unknown')}.",
            "",
            "Plain-English read: liquidity is the primary impulse in the model. Comparative inventory is the physical-market diagnostic that helps explain whether the observed oil move is running ahead of, behind, or against that liquidity-implied path.",
        ]
    ) + "\n"


def ci_state_text(row: Row) -> str:
    z = row.get("CI_zscore")
    if not is_number(z):
        return "inventory state is unavailable"
    zf = float(z)
    if zf > 0.5:
        return "inventories are loose versus history, which can dampen bullish liquidity impulses or validate weak residuals"
    if zf < -0.5:
        return "inventories are tight versus history, which can amplify bullish liquidity impulses or validate strong residuals"
    return "inventories are near normal versus history, so CI is not sending a strong surplus/deficit signal"


def residual_interpretation(value: object) -> str:
    if not is_number(value):
        return "the residual is unavailable."
    vf = float(value)
    if vf > 5:
        return "oil is materially richer than the GM2-implied path."
    if vf < -5:
        return "oil is materially cheaper than the GM2-implied path."
    return "oil is close to the GM2-implied path."


def month_shift(month: str, delta: int) -> str:
    year = int(month[:4])
    month_num = int(month[5:7]) + delta
    while month_num < 1:
        year -= 1
        month_num += 12
    while month_num > 12:
        year += 1
        month_num -= 12
    return f"{year}-{month_num:02d}"


def fmt(value: object) -> str:
    return f"{float(value):.3f}" if is_number(value) else "n/a"


def fmt_pct(value: object) -> str:
    return f"{100 * float(value):.1f}%" if is_number(value) else "n/a"


def fmt_usd(value: object) -> str:
    return f"${float(value) / 1_000_000_000_000:.2f} trillion" if is_number(value) else "n/a"


def third_stage_targets() -> list[str]:
    return [
        "WTI_YoY",
        "Brent_YoY",
        "WTI",
        "Brent",
        "real_WTI",
        "real_Brent",
        "WTI_deviation_12m_avg",
        "Brent_deviation_12m_avg",
        "WTI_GM2_path_residual",
        "Brent_GM2_path_residual",
        "WTI_forward_3m_return",
        "Brent_forward_3m_return",
        "WTI_forward_6m_return",
        "Brent_forward_6m_return",
    ]


def add_gm2_residual_targets(rows: list[Row], max_lag: int) -> list[Row]:
    out = [dict(row) for row in rows]
    by_month = {row["month"]: row for row in out}
    for oil_target, prefix in [("WTI_YoY", "WTI"), ("Brent_YoY", "Brent")]:
        lag = best_gm2_lag(rows, oil_target, max_lag)
        pred_rows = rolling_predictions(rows, oil_target, [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
        for month, actual, pred in zip(pred_rows.get("months", []), pred_rows.get("actuals", []), pred_rows.get("preds", [])):
            by_month[month][f"{prefix}_GM2_path_residual"] = float(actual - pred)
            by_month[month][f"{prefix}_GM2_path_lag"] = lag
    return out


def best_gm2_lag(rows: list[Row], target: str, max_lag: int) -> int:
    best_lag = 0
    best_rmse = float("inf")
    for lag in range(max_lag + 1):
        pred = rolling_predictions(rows, target, [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
        if not pred:
            continue
        value = rmse(np.array(pred["actuals"], dtype=float), np.array(pred["preds"], dtype=float))
        if value < best_rmse:
            best_lag, best_rmse = lag, value
    return best_lag


def target_comparison_rows(rows: list[Row], target: str, max_lag: int) -> list[Row]:
    out: list[Row] = []
    ci = [
        feature("CI_zscore", 0, "CI_zscore"),
        feature("CI_monthly_change", 0, "CI_monthly_change"),
        feature("inventory_deficit_dummy", 0, "inventory_deficit_dummy"),
        feature("inventory_surplus_dummy", 0, "inventory_surplus_dummy"),
    ]
    for lag in range(max_lag + 1):
        gm2 = [feature("GM2_YoY", lag, "GM2_YoY_lag")]
        specs = [
            ("gm2_only", gm2),
            ("ci_diagnostic", ci),
            ("gm2_plus_ci", gm2 + ci),
        ]
        for model, features in specs:
            pred = rolling_predictions(rows, target, features, 60)
            if not pred:
                continue
            actual = np.array(pred["actuals"], dtype=float)
            forecast = np.array(pred["preds"], dtype=float)
            row = {
                "target": target,
                "model": model,
                "lag_months": lag,
                "window_months": 60,
                "n_predictions": len(actual),
                "rolling_rmse": rmse(actual, forecast),
                "rolling_mae": mae(actual, forecast),
                "rolling_r2": r2_score(actual, forecast),
                "directional_accuracy": directional_accuracy(actual, forecast),
                "sign_accuracy": sign_accuracy(actual, forecast),
                "target_family": target_family(target),
            }
            out.append(row)
    return add_target_baseline_comparisons(out)


def add_target_baseline_comparisons(rows: list[Row]) -> list[Row]:
    baselines: dict[tuple[str, int], Row] = {
        (str(row["target"]), int(row["lag_months"])): row
        for row in rows
        if row.get("model") == "gm2_only"
    }
    for row in rows:
        base = baselines.get((str(row["target"]), int(row["lag_months"])))
        if base:
            row["baseline_gm2_rmse_same_lag"] = base.get("rolling_rmse")
            row["baseline_gm2_mae_same_lag"] = base.get("rolling_mae")
            row["rmse_improvement_vs_same_lag_gm2"] = pct_improvement(base.get("rolling_rmse"), row.get("rolling_rmse"))  # type: ignore[arg-type]
            row["mae_improvement_vs_same_lag_gm2"] = pct_improvement(base.get("rolling_mae"), row.get("rolling_mae"))  # type: ignore[arg-type]
    return rows


def target_family(target: str) -> str:
    if target.endswith("_YoY"):
        return "oil_yoy_baseline"
    if target in {"WTI", "Brent", "real_WTI", "real_Brent"}:
        return "price_level"
    if "GM2_path_residual" in target:
        return "gm2_path_residual"
    if "deviation_12m_avg" in target:
        return "trailing_average_deviation"
    if "forward" in target:
        return "forward_return"
    return "other"


def two_step_residual_diagnostic(rows: list[Row], oil_target: str, lag: int) -> Row:
    prefix = oil_target.split("_")[0]
    residual_target = f"{prefix}_GM2_path_residual"
    features = [
        feature("CI_zscore", 0, "CI_zscore"),
        feature("CI_monthly_change", 0, "CI_monthly_change"),
        feature("inventory_deficit_dummy", 0, "inventory_deficit_dummy"),
        feature("inventory_surplus_dummy", 0, "inventory_surplus_dummy"),
        feature("financial_crisis_2008_2009", 0, "financial_crisis_2008_2009"),
        feature("shale_regime_2014_2017", 0, "shale_regime_2014_2017"),
        feature("covid_2020_2021", 0, "covid_2020_2021"),
        feature("war_spr_2022_2023", 0, "war_spr_2022_2023"),
    ]
    summary = fit_summary(rows, residual_target, "two_step_ci_regime_residual", features, lag, "third_stage_residual")
    pred = rolling_predictions(rows, residual_target, features, 60)
    if pred:
        actual = np.array(pred["actuals"], dtype=float)
        forecast = np.array(pred["preds"], dtype=float)
        summary.update(
            {
                "oil_target": oil_target,
                "residual_target": residual_target,
                "step_a_gm2_lag": lag,
                "residual_rolling_rmse": rmse(actual, forecast),
                "residual_rolling_mae": mae(actual, forecast),
                "residual_directional_accuracy": directional_accuracy(actual, forecast),
                "residual_sign_accuracy": sign_accuracy(actual, forecast),
                "residual_explained_variance": summary.get("full_r2"),
                "decision": "market-state diagnostic",
            }
        )
    return summary


def final_model_interpretation(target_rows: list[Row], diagnostic_rows: list[Row]) -> str:
    lines = [
        "# Final Model Interpretation",
        "",
        "## Current Forecasting Core",
        "",
        "- GM2-only remains the preferred primary Oil_YoY forecasting specification under the 60-month rolling validation rule.",
        "- Comparative inventory is not promoted to a direct forecasting feature because it does not improve rolling RMSE or MAE versus GM2-only by at least 5%.",
        "",
        "## Target Design",
        "",
    ]
    for target in third_stage_targets():
        subset = [r for r in target_rows if r.get("target") == target]
        if not subset:
            continue
        best = min(subset, key=lambda r: finite_or_inf(r.get("rolling_rmse")))
        lines.append(f"- {target}: best model `{best.get('model')}` lag {best.get('lag_months')} with rolling RMSE {best.get('rolling_rmse'):.3f} and MAE {best.get('rolling_mae'):.3f}.")
    lines.extend(["", "## Two-Step Residual Framework", ""])
    for row in diagnostic_rows:
        if not row:
            continue
        lines.append(
            f"- {row.get('oil_target')}: Step A GM2 lag {row.get('step_a_gm2_lag')}; Step B residual explained variance {row.get('residual_explained_variance'):.3f}, residual directional accuracy {row.get('residual_directional_accuracy'):.3f}."
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The practical interpretation is two-layered: GM2 describes broad oil-price momentum; comparative inventory describes physical-market state and residual risk around that path.",
            "- CI can be useful for diagnosing whether oil is rich or cheap relative to liquidity-implied momentum, especially across regimes, without being a robust direct Oil_YoY forecast improver.",
            "- Regime caveat: 2008-2009, 2014-2017, 2020-2021, and 2022-2023 are high-shock periods. Results should be checked both with and without those windows before using the model operationally.",
            "",
            "## Regeneration",
            "",
            "Run `python3 -m oil_model.pipeline --refresh --root .` to rebuild raw data, processed data, analysis tables, SQLite tables, and charts.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_specs(rows: list[Row], target: str, max_lag: int) -> list[Row]:
    out: list[Row] = []
    for lag in range(max_lag + 1):
        out.append(evaluate_spec(rows, target, [("GM2_YoY", lag)], "a_gm2", lag))
        out.append(
            evaluate_spec(
                rows,
                target,
                [("GM2_YoY", lag), ("CI_zscore", 0), ("CI_monthly_change", 0)],
                "c_gm2_inventory",
                lag,
            )
        )
    out.append(evaluate_spec(rows, target, [("CI_zscore", 0), ("CI_monthly_change", 0)], "b_inventory", 0))
    return [row for row in out if row]


def evaluate_spec(rows: list[Row], target: str, features: list[tuple[str, int]], model: str, lag: int) -> Row:
    x, y = design_matrix(rows, target, features)
    if len(y) < len(features) + 8:
        return {}
    split = max(len(y) - max(12, len(y) // 5), len(features) + 5)
    beta, stderr, tstats, pvalues, train_r2 = ols(x[:split], y[:split])
    yhat_test = add_intercept(x[split:]) @ beta if len(y[split:]) else np.array([])
    test_rmse = rmse(y[split:], yhat_test) if len(yhat_test) else None
    test_r2 = r2_score(y[split:], yhat_test) if len(yhat_test) > 1 else None
    return {
        "target": target,
        "model": model,
        "lag_months": lag,
        "n_train": split,
        "n_test": len(y) - split,
        "train_r2": train_r2,
        "test_r2": test_r2,
        "test_rmse": test_rmse,
        "coef_intercept": beta[0],
        "coef_GM2_YoY_lag": coef_for(features, beta, "GM2_YoY"),
        "p_GM2_YoY_lag": pvalue_for(features, pvalues, "GM2_YoY"),
        "coef_CI_zscore": coef_for(features, beta, "CI_zscore"),
        "p_CI_zscore": pvalue_for(features, pvalues, "CI_zscore"),
        "coef_CI_monthly_change": coef_for(features, beta, "CI_monthly_change"),
        "p_CI_monthly_change": pvalue_for(features, pvalues, "CI_monthly_change"),
        "max_abs_t": float(max(abs(v) for v in tstats[1:])) if len(tstats) > 1 else None,
    }


def rolling_validation(rows: list[Row], target: str, max_lag: int, window: int = 60) -> list[Row]:
    out: list[Row] = []
    specs = [("a_gm2", [("GM2_YoY", lag)], lag) for lag in range(max_lag + 1)]
    specs += [("b_inventory", [("CI_zscore", 0), ("CI_monthly_change", 0)], 0)]
    for model, features, lag in specs:
        x, y = design_matrix(rows, target, features)
        if len(y) < window + 12:
            continue
        preds: list[float] = []
        actuals: list[float] = []
        for end in range(window, len(y)):
            beta, *_ = ols(x[end - window : end], y[end - window : end])
            preds.append(float((add_intercept(x[end : end + 1]) @ beta).item()))
            actuals.append(float(y[end]))
        out.append(
            {
                "target": target,
                "model": model,
                "lag_months": lag,
                "window_months": window,
                "rolling_rmse": rmse(np.array(actuals), np.array(preds)),
                "rolling_r2": r2_score(np.array(actuals), np.array(preds)),
                "n_predictions": len(preds),
            }
        )
    return out


def add_regime_fields(rows: list[Row]) -> list[Row]:
    out: list[Row] = []
    for row in rows:
        month = str(row["month"])
        regime = regime_for_month(month)
        z = row.get("CI_zscore")
        new = dict(row)
        new["regime"] = regime
        new["financial_crisis_2008_2009"] = 1.0 if regime == "financial_crisis_2008_2009" else 0.0
        new["shale_regime_2014_2017"] = 1.0 if regime == "shale_regime_2014_2017" else 0.0
        new["covid_2020_2021"] = 1.0 if regime == "covid_2020_2021" else 0.0
        new["war_spr_2022_2023"] = 1.0 if regime == "war_spr_2022_2023" else 0.0
        new["normal_period"] = 1.0 if regime == "normal_period" else 0.0
        new["inventory_surplus_dummy"] = 1.0 if is_number(z) and float(z) > 0.5 else 0.0
        new["inventory_deficit_dummy"] = 1.0 if is_number(z) and float(z) < -0.5 else 0.0
        new["is_shock_period"] = 1.0 if regime in SHOCK_REGIMES else 0.0
        out.append(new)
    return out


def mask_target_shocks(rows: list[Row], target: str) -> list[Row]:
    out: list[Row] = []
    for row in rows:
        new = dict(row)
        if new.get("is_shock_period") == 1.0:
            new[target] = None
        out.append(new)
    return out


def regime_for_month(month: str) -> str:
    for name, (start, end) in REGIMES.items():
        if start <= month <= end:
            return name
    return "normal_period"


def feature(source: str, lag: int = 0, name: str | None = None) -> Row:
    return {"kind": "column", "source": source, "lag": lag, "name": name or source}


def interaction(left: Row, right: Row, name: str) -> Row:
    return {"kind": "interaction", "left": left, "right": right, "name": name}


def interaction_summaries(rows: list[Row], target: str, lag: int) -> list[Row]:
    gm2 = feature("GM2_YoY", lag, "GM2_YoY_lag")
    ci_z = feature("CI_zscore", 0, "CI_zscore")
    ci_chg = feature("CI_monthly_change", 0, "CI_monthly_change")
    specs = [
        ("interaction_full", [gm2, ci_z, ci_chg, interaction(gm2, ci_z, "GM2_x_CI_zscore"), interaction(gm2, ci_chg, "GM2_x_CI_monthly_change")]),
        ("interaction_zscore", [gm2, ci_z, interaction(gm2, ci_z, "GM2_x_CI_zscore")]),
        ("interaction_change", [gm2, ci_chg, interaction(gm2, ci_chg, "GM2_x_CI_monthly_change")]),
        ("interaction_selected_p10", selected_interaction_features(rows, target, lag)),
    ]
    return [fit_summary(rows, target, spec, features, lag, "interaction") for spec, features in specs]


def selected_interaction_features(rows: list[Row], target: str, lag: int) -> list[Row]:
    gm2 = feature("GM2_YoY", lag, "GM2_YoY_lag")
    ci_z = feature("CI_zscore", 0, "CI_zscore")
    ci_chg = feature("CI_monthly_change", 0, "CI_monthly_change")
    full = [gm2, ci_z, ci_chg, interaction(gm2, ci_z, "GM2_x_CI_zscore"), interaction(gm2, ci_chg, "GM2_x_CI_monthly_change")]
    x, y, _ = design_matrix_specs(rows, target, full)
    selected = [gm2, ci_z, ci_chg]
    if len(y) >= 72:
        _, _, _, pvalues, _ = ols_hac(x[-60:], y[-60:])
        names = feature_names(full)
        for name, spec, pvalue in zip(names, full, pvalues[1:]):
            if name.startswith("GM2_x_") and pvalue < 0.10:
                selected.append(spec)
    return selected


def residual_summary(rows: list[Row], target: str, lag: int) -> Row:
    gm2 = [feature("GM2_YoY", lag, "GM2_YoY_lag")]
    x, y, months = design_matrix_specs(rows, target, gm2)
    if len(y) < 24:
        return {}
    beta, *_ = ols_hac(x, y)
    residuals = y - add_intercept(x) @ beta
    res_rows = [
        {
            "month": month,
            "GM2_residual": float(resid),
            "CI_zscore": row_by_month(rows, month).get("CI_zscore"),
            "CI_monthly_change": row_by_month(rows, month).get("CI_monthly_change"),
            "inventory_surplus_dummy": row_by_month(rows, month).get("inventory_surplus_dummy"),
            "inventory_deficit_dummy": row_by_month(rows, month).get("inventory_deficit_dummy"),
        }
        for month, resid in zip(months, residuals)
    ]
    features = [
        feature("CI_zscore", 0, "CI_zscore"),
        feature("CI_monthly_change", 0, "CI_monthly_change"),
        feature("inventory_surplus_dummy", 0, "inventory_surplus_dummy"),
        feature("inventory_deficit_dummy", 0, "inventory_deficit_dummy"),
    ]
    summary = fit_summary(res_rows, "GM2_residual", "residual_ci_dummies", features, lag, "residual")
    summary["target"] = target
    return summary


def regime_summaries(rows: list[Row], target: str, max_lag: int) -> list[Row]:
    out: list[Row] = []
    for lag in range(max_lag + 1):
        gm2 = feature("GM2_YoY", lag, "GM2_YoY_lag")
        ci_z = feature("CI_zscore", 0, "CI_zscore")
        ci_chg = feature("CI_monthly_change", 0, "CI_monthly_change")
        for regime in [*REGIMES, "normal_period"]:
            dummy = feature(regime, 0, regime)
            specs = [
                ("regime_gm2", [gm2, interaction(gm2, dummy, f"GM2_x_{regime}")]),
                ("regime_ci", [ci_z, ci_chg, interaction(ci_z, dummy, f"CI_zscore_x_{regime}"), interaction(ci_chg, dummy, f"CI_monthly_change_x_{regime}")]),
                ("regime_gm2_ci", [gm2, ci_z, ci_chg, interaction(gm2, dummy, f"GM2_x_{regime}"), interaction(ci_z, dummy, f"CI_zscore_x_{regime}")]),
                ("regime_gm2_ci_interaction", [gm2, ci_z, ci_chg, interaction(gm2, ci_z, "GM2_x_CI_zscore"), interaction(interaction(gm2, ci_z, "GM2_x_CI_zscore"), dummy, f"GM2_x_CI_zscore_x_{regime}")]),
            ]
            for model, features in specs:
                row = fit_summary(rows, target, model, features, lag, regime)
                row["regime"] = regime
                out.append(row)
    return out


def extended_rolling_for_target(rows: list[Row], target: str, max_lag: int, window: int, sample: str, baselines_60: dict[int, Row] | None) -> list[Row]:
    out: list[Row] = []
    for lag in range(max_lag + 1):
        gm2 = feature("GM2_YoY", lag, "GM2_YoY_lag")
        ci_z = feature("CI_zscore", 0, "CI_zscore")
        ci_chg = feature("CI_monthly_change", 0, "CI_monthly_change")
        candidates = [
            ("gm2_only", [gm2]),
            ("ci_only", [ci_z, ci_chg]),
            ("gm2_ci_additive", [gm2, ci_z, ci_chg]),
            ("interaction_full", [gm2, ci_z, ci_chg, interaction(gm2, ci_z, "GM2_x_CI_zscore"), interaction(gm2, ci_chg, "GM2_x_CI_monthly_change")]),
            ("interaction_zscore", [gm2, ci_z, interaction(gm2, ci_z, "GM2_x_CI_zscore")]),
            ("interaction_change", [gm2, ci_chg, interaction(gm2, ci_chg, "GM2_x_CI_monthly_change")]),
            ("interaction_selected_p10", selected_interaction_features(rows, target, lag)),
        ]
        base = rolling_predictions(rows, target, [gm2], window)
        for model, features in candidates:
            pred = rolling_predictions(rows, target, features, window)
            if not pred:
                continue
            summary = rolling_metrics_row(target, model, lag, window, sample, pred, base)
            if baselines_60 and window == 60 and model != "gm2_only":
                summary["dm_pvalue_vs_same_lag_gm2_60m_cache"] = summary["dm_pvalue_vs_same_lag_gm2"]
            out.append(summary)
    return out


def fit_summary(rows: list[Row], target: str, model: str, features: list[Row], lag: int, family: str) -> Row:
    x, y, months = design_matrix_specs(rows, target, features)
    if len(y) < len(features) + 8:
        return {}
    split = max(len(y) - max(12, len(y) // 5), len(features) + 5)
    beta, stderr, tstats, pvalues, train_r2 = ols_hac(x[:split], y[:split])
    test_pred = add_intercept(x[split:]) @ beta if len(y[split:]) else np.array([])
    full_beta, full_stderr, full_tstats, full_pvalues, full_r2 = ols_hac(x, y)
    cooks = cooks_distance(x, y, full_beta)
    high_leverage = [month for month, cook in zip(months, cooks) if cook > 4 / max(len(y), 1)]
    names = feature_names(features)
    row: Row = {
        "target": target,
        "family": family,
        "model": model,
        "lag_months": lag,
        "formula": formula_text(target, features),
        "n_obs": len(y),
        "n_train": split,
        "n_test": len(y) - split,
        "train_r2": train_r2,
        "full_r2": full_r2,
        "test_rmse": rmse(y[split:], test_pred) if len(test_pred) else None,
        "test_mae": mae(y[split:], test_pred) if len(test_pred) else None,
        "test_r2": r2_score(y[split:], test_pred) if len(test_pred) > 1 else None,
        "high_leverage_month_count": sum(1 for c in cooks if c > 4 / max(len(y), 1)),
        "high_leverage_months": ";".join(high_leverage[:24]),
        "max_cooks_distance": float(max(cooks)) if len(cooks) else None,
    }
    for name, coef, se, tstat, pvalue in zip(["intercept", *names], full_beta, full_stderr, full_tstats, full_pvalues):
        safe = name.replace(" ", "_")
        row[f"coef_{safe}"] = float(coef)
        row[f"hac_se_{safe}"] = float(se)
        row[f"t_{safe}"] = float(tstat)
        row[f"p_{safe}"] = float(pvalue)
    return row


def rolling_predictions(rows: list[Row], target: str, features: list[Row], window: int) -> Row:
    x, y, months = design_matrix_specs(rows, target, features)
    if len(y) < window + 12 or len(features) + 2 >= window:
        return {}
    preds: list[float] = []
    actuals: list[float] = []
    pred_months: list[str] = []
    for end in range(window, len(y)):
        try:
            beta = ols_beta(x[end - window : end], y[end - window : end])
        except np.linalg.LinAlgError:
            continue
        preds.append(float((add_intercept(x[end : end + 1]) @ beta).item()))
        actuals.append(float(y[end]))
        pred_months.append(months[end])
    return {"months": pred_months, "actuals": actuals, "preds": preds}


def rolling_metrics_row(target: str, model: str, lag: int, window: int, sample: str, pred: Row, base: Row) -> Row:
    actual = np.array(pred["actuals"], dtype=float)
    forecast = np.array(pred["preds"], dtype=float)
    base_lookup = dict(zip(base.get("months", []), base.get("preds", [])))
    matched_months = [m for m in pred["months"] if m in base_lookup]
    base_pred = np.array([base_lookup[m] for m in matched_months], dtype=float)
    model_lookup = dict(zip(pred["months"], pred["preds"]))
    actual_lookup = dict(zip(pred["months"], pred["actuals"]))
    matched_actual = np.array([actual_lookup[m] for m in matched_months], dtype=float)
    base_rmse = rmse(matched_actual, base_pred) if len(base_pred) else None
    base_mae = mae(matched_actual, base_pred) if len(base_pred) else None
    model_rmse = rmse(actual, forecast)
    model_mae = mae(actual, forecast)
    return {
        "target": target,
        "model": model,
        "lag_months": lag,
        "window_months": window,
        "sample": sample,
        "n_predictions": len(actual),
        "rolling_rmse": model_rmse,
        "rolling_mae": model_mae,
        "rolling_r2": r2_score(actual, forecast),
        "directional_accuracy": directional_accuracy(actual, forecast),
        "sign_accuracy": sign_accuracy(actual, forecast),
        "baseline_gm2_rmse_same_lag": base_rmse,
        "baseline_gm2_mae_same_lag": base_mae,
        "rmse_improvement_vs_same_lag_gm2": pct_improvement(base_rmse, model_rmse),
        "mae_improvement_vs_same_lag_gm2": pct_improvement(base_mae, model_mae),
        "dm_stat_vs_same_lag_gm2": dm_test(matched_actual, np.array([model_lookup[m] for m in matched_months], dtype=float), base_pred)[0] if len(base_pred) else None,
        "dm_pvalue_vs_same_lag_gm2": dm_test(matched_actual, np.array([model_lookup[m] for m in matched_months], dtype=float), base_pred)[1] if len(base_pred) else None,
    }


def design_matrix_specs(rows: list[Row], target: str, features: list[Row]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    x_rows: list[list[float]] = []
    y_values: list[float] = []
    months: list[str] = []
    max_lag = max_lag_for_specs(features)
    for i in range(max_lag, len(rows)):
        y = rows[i].get(target)
        values = [feature_value(rows, i, spec) for spec in features]
        if is_number(y) and all(is_number(v) for v in values):
            x_rows.append([float(v) for v in values])
            y_values.append(float(y))
            months.append(str(rows[i]["month"]))
    return np.array(x_rows, dtype=float), np.array(y_values, dtype=float), months


def feature_value(rows: list[Row], i: int, spec: Row) -> float | None:
    if spec["kind"] == "column":
        j = i - int(spec.get("lag", 0))
        if j < 0:
            return None
        value = rows[j].get(str(spec["source"]))
        return float(value) if is_number(value) else None
    if spec["kind"] == "interaction":
        left = feature_value(rows, i, spec["left"])  # type: ignore[arg-type]
        right = feature_value(rows, i, spec["right"])  # type: ignore[arg-type]
        return left * right if is_number(left) and is_number(right) else None
    return None


def max_lag_for_specs(features: list[Row]) -> int:
    out = 0
    for spec in features:
        if spec["kind"] == "column":
            out = max(out, int(spec.get("lag", 0)))
        elif spec["kind"] == "interaction":
            out = max(out, max_lag_for_specs([spec["left"], spec["right"]]))  # type: ignore[list-item]
    return out


def feature_names(features: list[Row]) -> list[str]:
    return [str(spec["name"]) for spec in features]


def formula_text(target: str, features: list[Row]) -> str:
    return f"{target}_t = alpha + " + " + ".join(feature_names(features))


def row_by_month(rows: list[Row], month: str) -> Row:
    for row in rows:
        if row.get("month") == month:
            return row
    return {}


def design_matrix(rows: list[Row], target: str, features: list[tuple[str, int]]) -> tuple[np.ndarray, np.ndarray]:
    x_rows: list[list[float]] = []
    y_values: list[float] = []
    max_lag = max((lag for _, lag in features), default=0)
    for i in range(max_lag, len(rows)):
        y = rows[i].get(target)
        values: list[float] = []
        ok = is_number(y)
        for col, lag in features:
            value = rows[i - lag].get(col)
            ok = ok and is_number(value)
            values.append(float(value) if is_number(value) else math.nan)
        if ok:
            x_rows.append(values)
            y_values.append(float(y))
    return np.array(x_rows, dtype=float), np.array(y_values, dtype=float)


def ols(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    x_i = add_intercept(x)
    beta = np.linalg.lstsq(x_i, y, rcond=None)[0]
    residuals = y - x_i @ beta
    dof = max(len(y) - x_i.shape[1], 1)
    sigma2 = float((residuals @ residuals) / dof)
    cov = sigma2 * np.linalg.pinv(x_i.T @ x_i)
    stderr = np.sqrt(np.diag(cov))
    tstats = np.divide(beta, stderr, out=np.zeros_like(beta), where=stderr != 0)
    pvalues = 2 * (1 - stats.t.cdf(np.abs(tstats), dof))
    return beta, stderr, tstats, pvalues, r2_score(y, x_i @ beta)


def ols_beta(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(add_intercept(x), y, rcond=None)[0]


def ols_hac(x: np.ndarray, y: np.ndarray, max_lag: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    x_i = add_intercept(x)
    beta = np.linalg.lstsq(x_i, y, rcond=None)[0]
    residuals = y - x_i @ beta
    n, k = x_i.shape
    if max_lag is None:
        max_lag = max(1, int(4 * (n / 100) ** (2 / 9)))
    xtx_inv = np.linalg.pinv(x_i.T @ x_i)
    meat = np.zeros((k, k))
    for t in range(n):
        xt = x_i[t : t + 1].T
        meat += residuals[t] ** 2 * (xt @ xt.T)
    for lag in range(1, min(max_lag, n - 1) + 1):
        weight = 1 - lag / (max_lag + 1)
        gamma = np.zeros((k, k))
        for t in range(lag, n):
            gamma += residuals[t] * residuals[t - lag] * (x_i[t : t + 1].T @ x_i[t - lag : t - lag + 1])
        meat += weight * (gamma + gamma.T)
    cov = xtx_inv @ meat @ xtx_inv
    cov *= n / max(n - k, 1)
    stderr = np.sqrt(np.maximum(np.diag(cov), 0))
    tstats = np.divide(beta, stderr, out=np.zeros_like(beta), where=stderr != 0)
    dof = max(n - k, 1)
    pvalues = 2 * (1 - stats.t.cdf(np.abs(tstats), dof))
    return beta, stderr, tstats, pvalues, r2_score(y, x_i @ beta)


def add_intercept(x: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(x)), x])


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def r2_score(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    denom = float(np.sum((actual - np.mean(actual)) ** 2))
    if denom == 0:
        return None
    return float(1 - np.sum((actual - predicted) ** 2) / denom)


def directional_accuracy(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    if len(actual) < 2:
        return None
    actual_change = np.diff(actual)
    pred_change = np.diff(predicted)
    return float(np.mean(np.sign(actual_change) == np.sign(pred_change)))


def sign_accuracy(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    if len(actual) == 0:
        return None
    return float(np.mean(np.sign(actual) == np.sign(predicted)))


def pct_improvement(baseline: float | None, candidate: float | None) -> float | None:
    if baseline in (None, 0) or candidate is None:
        return None
    return float((baseline - candidate) / baseline)


def dm_test(actual: np.ndarray, candidate: np.ndarray, baseline: np.ndarray) -> tuple[float | None, float | None]:
    if len(actual) < 12 or len(candidate) != len(actual) or len(baseline) != len(actual):
        return None, None
    diff = (actual - candidate) ** 2 - (actual - baseline) ** 2
    mean_diff = float(np.mean(diff))
    centered = diff - mean_diff
    n = len(diff)
    max_lag = max(1, int(n ** (1 / 3)))
    var = float(np.mean(centered**2))
    for lag in range(1, min(max_lag, n - 1) + 1):
        weight = 1 - lag / (max_lag + 1)
        cov = float(np.mean(centered[lag:] * centered[:-lag]))
        var += 2 * weight * cov
    if var <= 0:
        return None, None
    stat = mean_diff / math.sqrt(var / n)
    pvalue = 2 * (1 - stats.norm.cdf(abs(stat)))
    return float(stat), float(pvalue)


def cooks_distance(x: np.ndarray, y: np.ndarray, beta: np.ndarray) -> np.ndarray:
    x_i = add_intercept(x)
    residuals = y - x_i @ beta
    n, p = x_i.shape
    mse = float(np.sum(residuals**2) / max(n - p, 1))
    if mse == 0:
        return np.zeros(n)
    hat = np.sum((x_i @ np.linalg.pinv(x_i.T @ x_i)) * x_i, axis=1)
    denom = p * mse * np.maximum((1 - hat) ** 2, 1e-12)
    return (residuals**2 * hat) / denom


def second_stage_findings(
    rows: list[Row],
    interaction_rows: list[Row],
    residual_rows: list[Row],
    regime_rows: list[Row],
    rolling_rows: list[Row],
) -> str:
    complete_gm2 = [r for r in rows if is_number(r.get("GM2_USD"))]
    latest = complete_gm2[-1] if complete_gm2 else {}
    lines = [
        "# Second-Stage Oil Liquidity Inventory Findings",
        "",
        "## Data Status",
        "",
        f"- Latest complete G4 GM2 month: {latest.get('month')}",
        f"- Latest complete G4 GM2 USD: {latest.get('GM2_USD'):.5e}" if latest else "- Latest complete G4 GM2 USD: n/a",
        "- All lagged GM2 features use only values observed at or before `t - lag`; inventory state variables are same-month physical-market conditions.",
        "",
        "## Selection Rule",
        "",
        "- Rolling validation is primary. A combined model is treated as useful only if it improves rolling RMSE or MAE versus the same-lag GM2-only model by at least 5%, or materially improves directional accuracy.",
        "- The chronological train/test split is retained as a secondary check.",
        "- HAC/Newey-West standard errors are reported in the model summary CSVs.",
        "",
        "## Best Rolling Models",
        "",
    ]
    for target in TARGETS:
        target_rows = [r for r in rolling_rows if r.get("target") == target and r.get("window_months") == 60 and r.get("sample") == "all"]
        gm2 = sorted([r for r in target_rows if r.get("model") == "gm2_only"], key=lambda r: finite_or_inf(r.get("rolling_rmse")))
        combined = sorted([r for r in target_rows if r.get("model") != "gm2_only"], key=lambda r: finite_or_inf(r.get("rolling_rmse")))
        if gm2:
            lines.append(f"- {target} best GM2-only: lag {gm2[0].get('lag_months')}, RMSE {gm2[0].get('rolling_rmse'):.3f}, MAE {gm2[0].get('rolling_mae'):.3f}, directional accuracy {gm2[0].get('directional_accuracy'):.3f}.")
        if combined:
            useful = is_useful_combined(combined[0])
            verdict = "passes" if useful else "does not pass"
            lines.append(f"- {target} best combined: `{combined[0].get('model')}` lag {combined[0].get('lag_months')}, RMSE {combined[0].get('rolling_rmse'):.3f}, MAE {combined[0].get('rolling_mae'):.3f}; it {verdict} the 5% error-improvement rule versus same-lag GM2.")
    lines.extend(["", "## Inventory Residual Test", ""])
    for target in TARGETS:
        target_res = sorted([r for r in residual_rows if r and r.get("target") == target], key=lambda r: finite_or_inf(r.get("p_CI_zscore", r.get("p_CI_monthly_change"))))
        best = min([r for r in residual_rows if r and r.get("target") == target], key=lambda r: finite_or_inf(r.get("test_rmse")), default=None)
        if best:
            lines.append(f"- {target}: the best residual specification by test RMSE uses GM2 lag {best.get('lag_months')} with residual-model R2 {best.get('full_r2'):.3f}. Coefficients and HAC p-values are in `analysis/residual_model_summary.csv`.")
        elif target_res:
            lines.append(f"- {target}: residual rows were estimated, but no stable best test split was available.")
    lines.extend(["", "## Regime And Shock Checks", ""])
    no_shock = [r for r in rows if r.get("is_shock_period") == 0.0]
    lines.append(f"- Main shock periods flagged: {', '.join(SHOCK_REGIMES)}. Shock-excluded rolling reruns are included in `analysis/rolling_validation_extended.csv` with `sample=excluding_shocks`.")
    lines.append(f"- Non-shock sample months with usable rows: {len(no_shock)}.")
    for target in TARGETS:
        ex_rows = [r for r in rolling_rows if r.get("target") == target and r.get("window_months") == 60 and r.get("sample") == "excluding_shocks"]
        ex_best = min(ex_rows, key=lambda r: finite_or_inf(r.get("rolling_rmse")), default=None)
        if ex_best:
            lines.append(f"- Excluding shock target months, {target} best 60m rolling model is `{ex_best.get('model')}` lag {ex_best.get('lag_months')}, RMSE {ex_best.get('rolling_rmse'):.3f}, MAE {ex_best.get('rolling_mae'):.3f}.")
    regime_best = sorted([r for r in regime_rows if r], key=lambda r: finite_or_inf(r.get("test_rmse")))[:6]
    for row in regime_best:
        lines.append(f"- Low split-error regime check: {row.get('target')} `{row.get('model')}` / {row.get('regime')} lag {row.get('lag_months')}, test RMSE {row.get('test_rmse'):.3f}.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- GM2 remains the cleaner leading oil-momentum signal in these interpretable linear tests.",
            "- Comparative inventory should be read as a physical-market state variable: its direct additive coefficient is not enough by itself; the useful question is whether inventory amplifies, dampens, or explains deviations from the liquidity-implied path.",
            "- Where combined models fail the 5% rolling-error rule, the result should be stated as a failure of CI as a direct predictor, not as proof that inventory is irrelevant to risk periods or residual deviations.",
        ]
    )
    return "\n".join(lines) + "\n"


def is_useful_combined(row: Row) -> bool:
    rmse_imp = row.get("rmse_improvement_vs_same_lag_gm2")
    mae_imp = row.get("mae_improvement_vs_same_lag_gm2")
    return (is_number(rmse_imp) and float(rmse_imp) >= 0.05) or (is_number(mae_imp) and float(mae_imp) >= 0.05)


def finite_or_inf(value: object) -> float:
    return float(value) if is_number(value) else float("inf")


def coef_for(features: list[tuple[str, int]], beta: np.ndarray, name: str) -> float | None:
    for i, (feature, _) in enumerate(features, start=1):
        if feature == name:
            return float(beta[i])
    return None


def pvalue_for(features: list[tuple[str, int]], pvalues: np.ndarray, name: str) -> float | None:
    for i, (feature, _) in enumerate(features, start=1):
        if feature == name:
            return float(pvalues[i])
    return None


def is_number(value: object) -> bool:
    return isinstance(value, (float, int)) and math.isfinite(float(value))
