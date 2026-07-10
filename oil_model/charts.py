from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .analysis import feature, interaction, rolling_predictions
from .storage import Row


def make_charts(
    rows: list[Row],
    lag_rows: list[Row],
    out_dir: Path,
    residual_rows: list[Row] | None = None,
    rolling_rows: list[Row] | None = None,
    target_rows: list[Row] | None = None,
    oil_equity_rows: list[Row] | None = None,
    oil_equity_return_rows: list[Row] | None = None,
    uso_lead_lag_rows: list[Row] | None = None,
    uso_tracking_rows: list[Row] | None = None,
    uso_model_rows: list[Row] | None = None,
    energy_gdp_rows: list[Row] | None = None,
    energy_gdp_model_rows: list[Row] | None = None,
    system_signal_rows: list[Row] | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_series(rows, out_dir / "gm2_oil_yoy.png")
    plot_levels(rows, out_dir / "gm2_usd_components.png")
    plot_inventory(rows, out_dir / "comparative_inventory.png")
    plot_lag_corr(lag_rows, out_dir / "lag_correlations.png")
    plot_lag_corr(lag_rows, out_dir / "gm2_lag_correlation_wti_brent.png")
    scatter_by_regime(rows, out_dir / "gm2_oil_scatter_by_inventory_regime.png")
    residual_rows = residual_rows or []
    rolling_rows = rolling_rows or []
    target_rows = target_rows or []
    oil_equity_rows = oil_equity_rows or []
    oil_equity_return_rows = oil_equity_return_rows or []
    uso_lead_lag_rows = uso_lead_lag_rows or []
    uso_tracking_rows = uso_tracking_rows or []
    uso_model_rows = uso_model_rows or []
    energy_gdp_rows = energy_gdp_rows or []
    energy_gdp_model_rows = energy_gdp_model_rows or []
    system_signal_rows = system_signal_rows or []
    plot_gm2_vs_oil_best_lag(rows, lag_rows, out_dir / "gm2_vs_oil_yoy_best_lag.png")
    plot_actual_vs_predicted(rows, rolling_rows, "gm2_only", out_dir / "oil_yoy_actual_vs_predicted_gm2_only.png")
    plot_actual_vs_predicted(rows, rolling_rows, "best_combined", out_dir / "oil_yoy_actual_vs_predicted_best_combined.png")
    plot_residual_vs_ci(rows, residual_rows, out_dir / "gm2_residual_vs_ci.png")
    plot_regime_scatter(rows, out_dir / "regime_scatter_gm2_ci_oil.png")
    plot_best_gm2_prediction(rows, rolling_rows, out_dir / "actual_vs_predicted_best_gm2.png")
    plot_residual_vs_ci_zscore(rows, out_dir / "residual_vs_ci_zscore.png")
    plot_residual_time_series(rows, out_dir / "residual_time_series_regimes.png")
    plot_ci_vs_real_oil(rows, out_dir / "ci_vs_real_oil_price_level.png")
    plot_target_rmse(target_rows, out_dir / "target_comparison_rmse.png")
    plot_final_gm2_oil_lead(rows, out_dir / "final_gm2_oil_lead_chart.png")
    plot_final_actual_vs_predicted_wti(rows, out_dir / "final_actual_vs_predicted_wti.png")
    plot_final_residual_ci_diagnostic(rows, out_dir / "final_residual_ci_diagnostic.png")
    plot_final_model_framework(out_dir / "final_model_framework.png")
    plot_oil_equity_lag_correlation(oil_equity_rows, out_dir / "oil_equity_lag_correlation.png")
    plot_oil_equity_return_lag_correlation(oil_equity_return_rows, out_dir / "oil_equity_return_lag_correlation.png")
    plot_oil_equity_rolling_correlation(rows, out_dir / "oil_equity_rolling_correlation.png")
    plot_sp500_vs_wti_yoy(rows, out_dir / "sp500_vs_wti_yoy.png")
    plot_oil_equity_regime_scatter(rows, out_dir / "oil_equity_regime_scatter.png")
    plot_uso_vs_wti_yoy(rows, out_dir / "uso_vs_wti_yoy.png")
    plot_uso_wti_return_spread(rows, out_dir / "uso_wti_return_spread.png")
    plot_uso_tracking_residual_by_regime(uso_tracking_rows, out_dir / "uso_tracking_residual_by_regime.png")
    plot_uso_gm2_model_comparison(rows, uso_model_rows, out_dir / "uso_gm2_model_comparison.png")
    plot_energy_vs_gdp_growth(energy_gdp_rows, out_dir / "energy_vs_gdp_growth.png")
    plot_energy_intensity_trend(energy_gdp_rows, out_dir / "energy_intensity_trend.png")
    plot_gdp_per_energy_trend(energy_gdp_rows, out_dir / "gdp_per_energy_trend.png")
    plot_energy_gdp_lead_lag_heatmap(energy_gdp_rows, out_dir / "energy_gdp_lead_lag_heatmap.png")
    plot_oil_price_burden_vs_real_activity(energy_gdp_rows, out_dir / "oil_price_burden_vs_real_activity.png")
    plot_final_lead_lag_network(system_signal_rows, out_dir / "final_lead_lag_network.png")
    plot_final_signal_timeline_framework(out_dir / "final_signal_timeline_framework.png")
    plot_final_energy_finance_oil_gdp_map(out_dir / "final_energy_finance_oil_gdp_map.png")


def plot_series(rows: list[Row], path: Path) -> None:
    dates = [to_date(r["month"]) for r in rows]
    fig, ax = plt.subplots(figsize=(11, 6))
    for col, label in [("GM2_YoY", "GM2 YoY"), ("WTI_YoY", "WTI YoY"), ("Brent_YoY", "Brent YoY")]:
        ax.plot(dates, [r.get(col) for r in rows], label=label, linewidth=1.8)
    style_time_axis(ax)
    ax.set_title("Global M2 and Oil Price YoY")
    ax.set_ylabel("Percent")
    ax.legend()
    add_note(fig, "Formula: YoY = 100*(value/value[t-12]-1). Source: FRED/ECB/BOJ/ChinaData/EIA processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_levels(rows: list[Row], path: Path) -> None:
    dates = [to_date(r["month"]) for r in rows]
    fig, ax = plt.subplots(figsize=(11, 6))
    for col, label in [
        ("US_M2_USD", "U.S."),
        ("EA_M2_USD", "Euro area"),
        ("CN_M2_USD", "China"),
        ("JP_M2_USD", "Japan"),
        ("GM2_USD", "GM2"),
    ]:
        ax.plot(dates, [scale_trillion(r.get(col)) for r in rows], label=label, linewidth=1.5)
    style_time_axis(ax)
    ax.set_title("M2 Converted to USD")
    ax.set_ylabel("USD trillions")
    ax.legend(ncol=3)
    add_note(fig, "Formula: GM2_USD = US M2 + EA M2*EURUSD + CN M2/CNYUSD + JP M2/JPYUSD. Source: FRED/ECB/BOJ/ChinaData.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_inventory(rows: list[Row], path: Path) -> None:
    dates = [to_date(r["month"]) for r in rows]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(dates, [r.get("comparative_inventory_kb") for r in rows], label="Comparative inventory", color="#2b6cb0")
    ax.axhline(0, color="#555", linewidth=0.8)
    ax2 = ax.twinx()
    ax2.plot(dates, [r.get("CI_zscore") for r in rows], label="CI z-score", color="#c05621", alpha=0.8)
    style_time_axis(ax)
    ax.set_title("U.S. Commercial Crude Inventory vs Prior 5-Year Same-Month Average")
    ax.set_ylabel("Thousand barrels")
    ax2.set_ylabel("z-score")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2)
    add_note(fig, "Formula: comparative inventory = current month minus prior 5-year same-month average; z-score divides by prior same-month std. Source: EIA WCESTUS1.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_lag_corr(lag_rows: list[Row], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for target in sorted({str(r["target"]) for r in lag_rows}):
        selected = [r for r in lag_rows if r["target"] == target]
        ax.plot([r["lag_months"] for r in selected], [r["correlation"] for r in selected], marker="o", label=target)
    ax.axhline(0, color="#555", linewidth=0.8)
    ax.set_title("GM2 YoY Leading Oil YoY: Lag Correlations")
    ax.set_xlabel("GM2 lead, months")
    ax.set_ylabel("Pearson correlation")
    ax.legend()
    add_note(fig, "Formula: corr(GM2_YoY[t-L], Oil_YoY[t]), L=0..18. Source: FRED/ECB/BOJ/ChinaData/EIA processed monthly dataset.")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_gm2_vs_oil_best_lag(rows: list[Row], lag_rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        selected = [r for r in lag_rows if r["target"] == target and r.get("correlation") is not None]
        best = max(selected, key=lambda r: abs(float(r["correlation"])))
        lag = int(best["lag_months"])
        xs, ys = [], []
        for i in range(lag, len(rows)):
            gm2 = rows[i - lag].get("GM2_YoY")
            oil = rows[i].get(target)
            if is_num(gm2) and is_num(oil):
                xs.append(float(gm2))
                ys.append(float(oil))
        ax.scatter(xs, ys, s=22, alpha=0.72, color="#2b6cb0")
        ax.axhline(0, color="#777", linewidth=0.7)
        ax.axvline(0, color="#777", linewidth=0.7)
        ax.set_title(f"{target}, GM2 lag {lag}m")
        ax.set_xlabel("GM2 YoY lagged")
    axes[0].set_ylabel("Oil YoY")
    add_note(fig, "Formula: Oil_YoY[t] vs GM2_YoY[t-best lag]. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_actual_vs_predicted(rows: list[Row], rolling_rows: list[Row], model: str, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        choices = [r for r in rolling_rows if r.get("target") == target and r.get("window_months") == 60 and r.get("sample") in (None, "all")]
        if model == "gm2_only":
            choices = [r for r in choices if r.get("model") == "gm2_only"]
        else:
            choices = [r for r in choices if r.get("model") != "gm2_only"]
        if not choices:
            continue
        best = min(choices, key=lambda r: float(r["rolling_rmse"]))
        lag = int(best["lag_months"])
        features = features_for_model(str(best["model"]), lag)
        pred = rolling_predictions(rows, target, features, 60)
        dates = [to_date(m) for m in pred.get("months", [])]
        ax.plot(dates, pred.get("actuals", []), label="actual", linewidth=1.5, color="#222222")
        ax.plot(dates, pred.get("preds", []), label="predicted", linewidth=1.5, color="#c05621")
        ax.set_title(f"{target}: {best['model']} lag {lag}m")
        ax.set_ylabel("YoY percent")
        style_time_axis(ax)
        ax.legend()
    formula = "Oil_YoY[t] = alpha + beta*GM2_YoY[t-L]" if model == "gm2_only" else "Best combined formula from 60m rolling validation; see rolling_validation_extended.csv."
    add_note(fig, f"Formula: {formula} Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def features_for_model(model: str, lag: int) -> list[Row]:
    gm2 = feature("GM2_YoY", lag, "GM2_YoY_lag")
    ci_z = feature("CI_zscore", 0, "CI_zscore")
    ci_chg = feature("CI_monthly_change", 0, "CI_monthly_change")
    if model == "ci_only":
        return [ci_z, ci_chg]
    if model == "gm2_ci_additive":
        return [gm2, ci_z, ci_chg]
    if model == "interaction_zscore":
        return [gm2, ci_z, interaction(gm2, ci_z, "GM2_x_CI_zscore")]
    if model == "interaction_change":
        return [gm2, ci_chg, interaction(gm2, ci_chg, "GM2_x_CI_monthly_change")]
    if model in {"interaction_full", "interaction_selected_p10"}:
        return [gm2, ci_z, ci_chg, interaction(gm2, ci_z, "GM2_x_CI_zscore"), interaction(gm2, ci_chg, "GM2_x_CI_monthly_change")]
    return [gm2]


def plot_residual_vs_ci(rows: list[Row], residual_rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        candidates = [r for r in residual_rows if r and r.get("target") == target and r.get("full_r2") is not None]
        lag = int(max(candidates, key=lambda r: float(r["full_r2"]))["lag_months"]) if candidates else 4
        pred = rolling_predictions(rows, target, [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
        actual = dict(zip(pred.get("months", []), pred.get("actuals", [])))
        forecast = dict(zip(pred.get("months", []), pred.get("preds", [])))
        xs, ys = [], []
        for row in rows:
            month = row["month"]
            if month in actual and is_num(row.get("CI_zscore")):
                xs.append(float(row["CI_zscore"]))
                ys.append(float(actual[month] - forecast[month]))
        ax.scatter(xs, ys, s=24, alpha=0.72, color="#2b6cb0")
        ax.axhline(0, color="#777", linewidth=0.7)
        ax.axvline(0, color="#777", linewidth=0.7)
        ax.set_title(f"{target}, GM2 residual lag {lag}m")
        ax.set_xlabel("CI z-score")
    axes[0].set_ylabel("Actual oil YoY minus GM2 prediction")
    add_note(fig, "Formula: residual = Oil_YoY[t] - fitted(alpha + beta*GM2_YoY[t-L]); x = CI_zscore[t]. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_regime_scatter(rows: list[Row], path: Path) -> None:
    colors = {
        "financial_crisis_2008_2009": "#c05621",
        "shale_regime_2014_2017": "#2b6cb0",
        "covid_2020_2021": "#805ad5",
        "war_spr_2022_2023": "#d69e2e",
        "normal_period": "#555555",
    }
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        for row in rows:
            if is_num(row.get("GM2_YoY")) and is_num(row.get("CI_zscore")) and is_num(row.get(target)):
                regime = regime_for_chart(str(row["month"]))
                ax.scatter(float(row["GM2_YoY"]), float(row[target]), s=18 + 10 * min(abs(float(row["CI_zscore"])), 3), alpha=0.65, color=colors[regime], label=regime)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), fontsize=7)
        ax.axhline(0, color="#777", linewidth=0.7)
        ax.axvline(0, color="#777", linewidth=0.7)
        ax.set_title(target)
        ax.set_xlabel("GM2 YoY")
    axes[0].set_ylabel("Oil YoY")
    add_note(fig, "Formula: scatter Oil_YoY[t] vs GM2_YoY[t]; marker size scales with abs(CI_zscore[t]); color = historical regime. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_best_gm2_prediction(rows: list[Row], rolling_rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        choices = [
            r for r in rolling_rows
            if r.get("target") == target and r.get("model") == "gm2_only" and r.get("window_months") == 60 and r.get("sample") == "all"
        ]
        lag = int(min(choices, key=lambda r: float(r["rolling_rmse"]))["lag_months"]) if choices else 5
        pred = rolling_predictions(rows, target, [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
        dates = [to_date(m) for m in pred.get("months", [])]
        ax.plot(dates, pred.get("actuals", []), color="#222222", label="actual", linewidth=1.4)
        ax.plot(dates, pred.get("preds", []), color="#2b6cb0", label="GM2-only prediction", linewidth=1.4)
        ax.set_title(f"{target}: best GM2-only lag {lag}m")
        ax.set_ylabel("YoY percent")
        style_time_axis(ax)
        ax.legend()
    add_note(fig, "Formula: Oil_YoY[t] = alpha + beta*GM2_YoY[t-L], with L selected by 60m rolling RMSE. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_residual_vs_ci_zscore(rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        lag = 5
        pred = rolling_predictions(rows, target, [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
        actual = dict(zip(pred.get("months", []), pred.get("actuals", [])))
        forecast = dict(zip(pred.get("months", []), pred.get("preds", [])))
        xs, ys = [], []
        for row in rows:
            month = row["month"]
            if month in actual and is_num(row.get("CI_zscore")):
                xs.append(float(row["CI_zscore"]))
                ys.append(float(actual[month] - forecast[month]))
        ax.scatter(xs, ys, s=24, alpha=0.72, color="#2b6cb0")
        ax.axhline(0, color="#777", linewidth=0.7)
        ax.axvline(0, color="#777", linewidth=0.7)
        ax.set_title(f"{target} residual vs CI")
        ax.set_xlabel("CI z-score")
    axes[0].set_ylabel("Actual minus GM2-implied Oil YoY")
    add_note(fig, "Formula: residual = Oil_YoY[t] - rolling fitted(alpha + beta*GM2_YoY[t-5]); x = CI_zscore[t]. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_residual_time_series(rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        lag = 5
        pred = rolling_predictions(rows, target, [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
        dates = [to_date(m) for m in pred.get("months", [])]
        residuals = [a - p for a, p in zip(pred.get("actuals", []), pred.get("preds", []))]
        ax.plot(dates, residuals, color="#2b6cb0", linewidth=1.2)
        ax.axhline(0, color="#777", linewidth=0.7)
        shade_regimes(ax)
        ax.set_title(f"{target} GM2 residual, lag {lag}m")
        ax.set_ylabel("Residual YoY pct")
        style_time_axis(ax)
    add_note(fig, "Formula: residual = Oil_YoY[t] - rolling fitted(alpha + beta*GM2_YoY[t-5]); shaded bands mark major regimes. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_ci_vs_real_oil(rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, price_col, label in zip(axes, ["real_WTI", "real_Brent"], ["Real WTI", "Real Brent"]):
        xs = [float(r["CI_zscore"]) for r in rows if is_num(r.get("CI_zscore")) and is_num(r.get(price_col))]
        ys = [float(r[price_col]) for r in rows if is_num(r.get("CI_zscore")) and is_num(r.get(price_col))]
        ax.scatter(xs, ys, s=22, alpha=0.7, color="#2b6cb0")
        ax.axvline(0, color="#777", linewidth=0.7)
        ax.set_title(label)
        ax.set_xlabel("CI z-score")
        ax.set_ylabel("Real price, 1982-84 USD")
    add_note(fig, "Formula: real oil price = nominal oil price / (CPIAUCSL/100); x = CI_zscore. Source: FRED/EIA processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_target_rmse(target_rows: list[Row], path: Path) -> None:
    best: dict[str, Row] = {}
    for row in target_rows:
        target = str(row.get("target"))
        if not target or not is_num(row.get("rolling_rmse")):
            continue
        if target not in best or float(row["rolling_rmse"]) < float(best[target]["rolling_rmse"]):
            best[target] = row
    labels = list(best)
    values = [float(best[label]["rolling_rmse"]) for label in labels]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(range(len(labels)), values, color="#2b6cb0")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylabel("Best 60m rolling RMSE")
    ax.set_title("Alternative Target Comparison")
    ax.grid(axis="y", alpha=0.25)
    add_note(fig, "Formula: minimum 60m rolling RMSE across GM2-only, CI diagnostic, and GM2+CI linear models for each target. Source: target_comparison_summary.csv.")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_final_gm2_oil_lead(rows: list[Row], path: Path) -> None:
    lag = 5
    dates = [to_date(r["month"]) for r in rows]
    gm2_shifted = []
    for i, _ in enumerate(rows):
        j = i - lag
        gm2_shifted.append(rows[j].get("GM2_YoY") if j >= 0 else None)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, gm2_shifted, label="G4 GM2 YoY, lagged 5m", color="#2b6cb0", linewidth=2.0)
    ax.plot(dates, [r.get("WTI_YoY") for r in rows], label="WTI YoY", color="#222222", linewidth=1.4, alpha=0.85)
    ax.plot(dates, [r.get("Brent_YoY") for r in rows], label="Brent YoY", color="#c05621", linewidth=1.4, alpha=0.85)
    ax.axhline(0, color="#777", linewidth=0.8)
    shade_regimes(ax)
    style_time_axis(ax)
    ax.set_title("Final GM2 Oil Lead Signal")
    ax.set_ylabel("YoY percent")
    ax.legend()
    add_note(fig, "Formula: Oil_YoY[t] compared with GM2_YoY[t-5]. Locked reporting model uses GM2-only lag 5. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_final_actual_vs_predicted_wti(rows: list[Row], path: Path) -> None:
    lag = 5
    pred = rolling_predictions(rows, "WTI_YoY", [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
    dates = [to_date(m) for m in pred.get("months", [])]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, pred.get("actuals", []), color="#222222", label="Actual WTI YoY", linewidth=1.6)
    ax.plot(dates, pred.get("preds", []), color="#2b6cb0", label="GM2-only predicted WTI YoY", linewidth=1.8)
    ax.axhline(0, color="#777", linewidth=0.8)
    shade_regimes(ax)
    style_time_axis(ax)
    ax.set_title("WTI YoY: Actual vs Locked GM2-Only Model")
    ax.set_ylabel("YoY percent")
    ax.legend()
    add_note(fig, "Formula: WTI_YoY[t] = alpha + beta*GM2_YoY[t-5], estimated with rolling 60-month windows. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_final_residual_ci_diagnostic(rows: list[Row], path: Path) -> None:
    lag = 5
    pred = rolling_predictions(rows, "WTI_YoY", [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
    actual = dict(zip(pred.get("months", []), pred.get("actuals", [])))
    forecast = dict(zip(pred.get("months", []), pred.get("preds", [])))
    xs, ys, colors = [], [], []
    for row in rows:
        month = row["month"]
        if month in actual and is_num(row.get("CI_zscore")):
            xs.append(float(row["CI_zscore"]))
            ys.append(float(actual[month] - forecast[month]))
            colors.append("#c05621" if float(row["CI_zscore"]) > 0.5 else "#2b6cb0" if float(row["CI_zscore"]) < -0.5 else "#555555")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(xs, ys, s=28, alpha=0.72, color=colors)
    if xs and ys:
        latest_x, latest_y = xs[-1], ys[-1]
        ax.scatter([latest_x], [latest_y], s=90, facecolor="none", edgecolor="#111111", linewidth=1.8, label="latest")
    ax.axhline(0, color="#777", linewidth=0.8)
    ax.axvline(0, color="#777", linewidth=0.8)
    ax.set_title("Residual Diagnostic: WTI Rich/Cheap vs Comparative Inventory")
    ax.set_xlabel("CI z-score")
    ax.set_ylabel("WTI YoY residual vs GM2-only path")
    ax.legend()
    ax.grid(True, alpha=0.25)
    add_note(fig, "Formula: residual = actual WTI_YoY[t] - rolling predicted WTI_YoY[t] from GM2_YoY[t-5]; x = CI_zscore[t]. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_final_model_framework(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_axis_off()
    boxes = {
        "gm2": (0.07, 0.62, 0.26, 0.18, "G4 GM2 YoY\nlagged 5 months"),
        "forecast": (0.43, 0.62, 0.26, 0.18, "Oil YoY momentum\nforecast"),
        "ci": (0.07, 0.24, 0.26, 0.18, "Comparative\ninventory"),
        "residual": (0.43, 0.24, 0.26, 0.18, "Residual / state /\nregime diagnostic"),
        "regime": (0.76, 0.24, 0.18, 0.56, "Regime shocks\ncaveat layer"),
    }
    for key, (x, y, w, h, text) in boxes.items():
        color = "#e6f0fa" if key in {"gm2", "forecast"} else "#f7eee7" if key in {"ci", "residual"} else "#eeeeee"
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.025,rounding_size=0.02", linewidth=1.2, edgecolor="#444444", facecolor=color)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=12, weight="bold" if key in {"forecast", "residual"} else "normal")
    arrows = [
        ((0.33, 0.71), (0.43, 0.71), "primary signal"),
        ((0.33, 0.33), (0.43, 0.33), "diagnostic"),
        ((0.69, 0.71), (0.76, 0.63), ""),
        ((0.69, 0.33), (0.76, 0.41), ""),
    ]
    for (x1, y1), (x2, y2), label in arrows:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18, linewidth=1.4, color="#333333"))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.045, label, ha="center", va="center", fontsize=9, color="#555555")
    ax.text(0.5, 0.92, "Final Oil Liquidity Inventory Framework", ha="center", va="center", fontsize=16, weight="bold")
    ax.text(0.5, 0.08, "Liquidity describes the impulse; inventory describes the physical-market state; regimes frame when the relationship can break.", ha="center", va="center", fontsize=10, color="#555555")
    add_note(fig, "Formula: GM2_YoY[t-5] -> Oil_YoY[t]; CI_zscore and regimes diagnose residuals. Source: final project interpretation.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_oil_equity_lag_correlation(oil_equity_rows: list[Row], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    for oil_col, color in [("WTI_YoY", "#2b6cb0"), ("Brent_YoY", "#c05621")]:
        selected = [
            r for r in oil_equity_rows
            if r.get("section") == "lead_lag_correlation"
            and r.get("equity_metric") == "SP500_YoY"
            and r.get("oil_metric") == oil_col
            and r.get("correlation") is not None
        ]
        selected = sorted(selected, key=lambda r: int(r["lag_months"]))
        ax.plot([r["lag_months"] for r in selected], [r["correlation"] for r in selected], marker="o", linewidth=1.6, label=f"SP500 YoY vs {oil_col}", color=color)
    ax.axhline(0, color="#777", linewidth=0.8)
    ax.axvline(0, color="#777", linewidth=0.8)
    ax.set_title("Oil-Equity Lead-Lag Correlation")
    ax.set_xlabel("Lag months: positive = stocks lead oil, negative = oil leads stocks")
    ax.set_ylabel("Pearson correlation")
    ax.legend()
    ax.grid(True, alpha=0.25)
    add_note(fig, "Formula: corr(SP500_YoY[t-L], Oil_YoY[t]), L=-18..18. Positive L means stocks lead oil. Source: FRED processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_oil_equity_return_lag_correlation(return_rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    panels = [("monthly_log_return", "Monthly log returns"), ("quarterly_return", "Quarterly returns")]
    for ax, (metric, title) in zip(axes, panels):
        for oil_metric, color in [
            ("WTI_log_return_1m" if metric == "monthly_log_return" else "WTI_quarterly_return", "#2b6cb0"),
            ("Brent_log_return_1m" if metric == "monthly_log_return" else "Brent_quarterly_return", "#c05621"),
        ]:
            selected = [
                r for r in return_rows
                if r.get("metric") == metric
                and r.get("sample") == "full"
                and r.get("oil_metric") == oil_metric
                and r.get("correlation") is not None
            ]
            selected = sorted(selected, key=lambda r: int(r["lag_periods"]))
            ax.plot([r["lag_periods"] for r in selected], [r["correlation"] for r in selected], marker="o", linewidth=1.5, label=oil_metric, color=color)
        ax.axhline(0, color="#777", linewidth=0.8)
        ax.axvline(0, color="#777", linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel("Lag periods: positive = stocks lead oil")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("Pearson correlation")
    axes[1].legend(fontsize=8)
    add_note(fig, "Formula: corr(SP500_return[t-L], Oil_return[t]). Return lead-lag is more relevant for timing than overlapping YoY lead-lag. Source: FRED processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_oil_equity_rolling_correlation(rows: list[Row], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    for oil_col, color in [("WTI_YoY", "#2b6cb0"), ("Brent_YoY", "#c05621")]:
        dates, vals = rolling_corr_series(rows, "SP500_YoY", oil_col, 60)
        ax.plot(dates, vals, linewidth=1.8, label=f"SP500 YoY vs {oil_col}, 60m", color=color)
    ax.axhline(0, color="#777", linewidth=0.8)
    style_time_axis(ax)
    ax.set_title("Rolling 60-Month Oil-Equity Correlation")
    ax.set_ylabel("Correlation")
    ax.legend()
    add_note(fig, "Formula: rolling corr(SP500_YoY[t], Oil_YoY[t]) over 60-month windows. Source: FRED processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def rolling_corr_series(rows: list[Row], x_col: str, y_col: str, window: int) -> tuple[list[float], list[float]]:
    pairs: list[tuple[str, float, float]] = []
    for row in rows:
        if is_num(row.get(x_col)) and is_num(row.get(y_col)):
            pairs.append((str(row["month"]), float(row[x_col]), float(row[y_col])))
    dates: list[float] = []
    vals: list[float] = []
    for end in range(window, len(pairs) + 1):
        segment = pairs[end - window : end]
        corr = simple_corr([p[1] for p in segment], [p[2] for p in segment])
        if corr is not None:
            dates.append(to_date(segment[-1][0]))
            vals.append(corr)
    return dates, vals


def simple_corr(x: list[float], y: list[float]) -> float | None:
    if len(x) < 3:
        return None
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    num = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    x_den = sum((a - x_mean) ** 2 for a in x)
    y_den = sum((b - y_mean) ** 2 for b in y)
    den = (x_den * y_den) ** 0.5
    return num / den if den else None


def plot_sp500_vs_wti_yoy(rows: list[Row], path: Path) -> None:
    dates = [to_date(r["month"]) for r in rows]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, [r.get("SP500_YoY") for r in rows], label="SP500 YoY", color="#2b6cb0", linewidth=1.7)
    ax.plot(dates, [r.get("WTI_YoY") for r in rows], label="WTI YoY", color="#222222", linewidth=1.4)
    ax.axhline(0, color="#777", linewidth=0.8)
    shade_regimes(ax)
    style_time_axis(ax)
    ax.set_title("SP500 vs WTI YoY")
    ax.set_ylabel("YoY percent")
    ax.legend()
    add_note(fig, "Formula: YoY = 100*(monthly average/monthly average[t-12]-1). Source: FRED processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_oil_equity_regime_scatter(rows: list[Row], path: Path) -> None:
    colors = {
        "financial_crisis_2008_2009": "#c05621",
        "shale_regime_2014_2017": "#2b6cb0",
        "covid_2020_2021": "#805ad5",
        "war_spr_2022_2023": "#d69e2e",
        "normal_period": "#555555",
    }
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, oil_col in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        for row in rows:
            if is_num(row.get("SP500_YoY")) and is_num(row.get(oil_col)):
                regime = regime_for_chart(str(row["month"]))
                ax.scatter(float(row["SP500_YoY"]), float(row[oil_col]), s=24, alpha=0.7, color=colors[regime], label=regime)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), fontsize=7)
        ax.axhline(0, color="#777", linewidth=0.7)
        ax.axvline(0, color="#777", linewidth=0.7)
        ax.set_title(f"SP500 YoY vs {oil_col}")
        ax.set_xlabel("SP500 YoY")
    axes[0].set_ylabel("Oil YoY")
    add_note(fig, "Formula: scatter Oil_YoY[t] vs SP500_YoY[t], colored by historical regime. Source: FRED processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_uso_vs_wti_yoy(rows: list[Row], path: Path) -> None:
    dates = [to_date(r["month"]) for r in rows]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, [r.get("USO_YoY") for r in rows], label="USO YoY", color="#2b6cb0", linewidth=1.7)
    ax.plot(dates, [r.get("WTI_YoY") for r in rows], label="WTI YoY", color="#222222", linewidth=1.4)
    ax.plot(dates, [r.get("Brent_YoY") for r in rows], label="Brent YoY", color="#c05621", linewidth=1.4, alpha=0.85)
    ax.axhline(0, color="#777", linewidth=0.8)
    shade_regimes(ax)
    style_time_axis(ax)
    ax.set_title("USO Tradable Exposure vs Benchmark Oil YoY")
    ax.set_ylabel("YoY percent")
    ax.legend()
    add_note(fig, "Formula: YoY = 100*(monthly value/monthly value[t-12]-1). USO uses Yahoo adjusted month-end close; WTI/Brent use FRED monthly oil prices.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_uso_wti_return_spread(rows: list[Row], path: Path) -> None:
    dates = [to_date(r["month"]) for r in rows]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, [r.get("USO_vs_WTI_return_spread") for r in rows], label="USO minus WTI monthly log return", color="#2b6cb0", linewidth=1.5)
    ax.plot(dates, [r.get("USO_vs_Brent_return_spread") for r in rows], label="USO minus Brent monthly log return", color="#c05621", linewidth=1.3, alpha=0.85)
    ax.axhline(0, color="#777", linewidth=0.8)
    shade_regimes(ax)
    style_time_axis(ax)
    ax.set_title("USO Benchmark Return Spread")
    ax.set_ylabel("Monthly log-return spread, pct points")
    ax.legend()
    add_note(fig, "Formula: USO_vs_WTI_return_spread = USO_log_return_1m - WTI_log_return_1m; Brent analog shown. Source: Yahoo/FRED processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_uso_tracking_residual_by_regime(tracking_rows: list[Row], path: Path) -> None:
    selected = [
        r for r in tracking_rows
        if r.get("section") == "regime_tracking_summary"
        and r.get("regime") != "all"
        and is_num(r.get("USO_tracking_residual_mean"))
    ]
    labels = [str(r["regime"]).replace("_", "\n") for r in selected]
    values = [float(r["USO_tracking_residual_mean"]) for r in selected]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(range(len(values)), values, color=["#c05621", "#2b6cb0", "#805ad5", "#d69e2e", "#555555"][: len(values)])
    ax.axhline(0, color="#777", linewidth=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Mean USO minus WTI YoY, pct points")
    ax.set_title("USO Tracking Residual By Regime")
    ax.grid(axis="y", alpha=0.25)
    add_note(fig, "Formula: USO_tracking_residual = USO_YoY - WTI_YoY, averaged by historical regime. Source: analysis/uso_tracking_residual_summary.csv.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_uso_gm2_model_comparison(rows: list[Row], model_rows: list[Row], path: Path) -> None:
    choices = [
        r for r in model_rows
        if r.get("target") == "USO_YoY"
        and r.get("section") == "tradable_exposure_model"
        and r.get("model") == "uso_gm2_only"
        and is_num(r.get("rolling_rmse"))
    ]
    lag = int(min(choices, key=lambda r: float(r["rolling_rmse"]))["lag_months"]) if choices else 5
    pred = rolling_predictions(rows, "USO_YoY", [feature("GM2_YoY", lag, "GM2_YoY_lag")], 60)
    dates = [to_date(m) for m in pred.get("months", [])]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, pred.get("actuals", []), label="Actual USO YoY", color="#222222", linewidth=1.5)
    ax.plot(dates, pred.get("preds", []), label=f"GM2-only USO prediction, lag {lag}m", color="#2b6cb0", linewidth=1.7)
    ax.axhline(0, color="#777", linewidth=0.8)
    shade_regimes(ax)
    style_time_axis(ax)
    ax.set_title("USO YoY vs GM2-Only Tradable Exposure Model")
    ax.set_ylabel("YoY percent")
    ax.legend()
    add_note(fig, "Formula: USO_YoY[t] = alpha + beta*GM2_YoY[t-L], L selected by 60m rolling RMSE for USO only. Source: Yahoo/FRED processed monthly dataset; locked WTI model remains GM2 lag 5.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_energy_vs_gdp_growth(energy_rows: list[Row], path: Path) -> None:
    q_rows = sorted([r for r in energy_rows if r.get("section") == "time_series" and r.get("frequency") == "quarterly"], key=lambda r: str(r.get("period")))
    dates = [to_date(r.get("month")) for r in q_rows if r.get("month")]
    energy = [r.get("Energy_consumption_growth") for r in q_rows if r.get("month")]
    gdp = [r.get("Real_GDP_growth") for r in q_rows if r.get("month")]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, energy, label="Energy consumption YoY", color="#2b6cb0", linewidth=1.7)
    ax.plot(dates, gdp, label="Real GDP YoY", color="#222222", linewidth=1.5)
    ax.axhline(0, color="#777", linewidth=0.8)
    shade_regimes(ax)
    style_time_axis(ax)
    ax.set_title("Energy Consumption Growth vs Real GDP Growth")
    ax.set_ylabel("YoY percent")
    ax.legend()
    add_note(fig, "Formula: quarterly YoY growth from EIA total primary energy consumption and FRED GDPC1. Source: EIA MER/FRED.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_energy_intensity_trend(energy_rows: list[Row], path: Path) -> None:
    q_rows = sorted([r for r in energy_rows if r.get("section") == "time_series" and r.get("frequency") == "quarterly"], key=lambda r: str(r.get("period")))
    dates = [to_date(r.get("month")) for r in q_rows if r.get("month")]
    vals = [r.get("Energy_intensity") for r in q_rows if r.get("month")]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, vals, color="#2b6cb0", linewidth=1.8)
    style_time_axis(ax)
    ax.set_title("U.S. Energy Intensity Trend")
    ax.set_ylabel("Quadrillion Btu per real GDP unit")
    add_note(fig, "Formula: Energy_intensity = quarterly total primary energy consumption / real GDP. Source: EIA MER/FRED GDPC1.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_gdp_per_energy_trend(energy_rows: list[Row], path: Path) -> None:
    q_rows = sorted([r for r in energy_rows if r.get("section") == "time_series" and r.get("frequency") == "quarterly"], key=lambda r: str(r.get("period")))
    dates = [to_date(r.get("month")) for r in q_rows if r.get("month")]
    vals = [r.get("GDP_per_energy") for r in q_rows if r.get("month")]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, vals, color="#2b6cb0", linewidth=1.8)
    style_time_axis(ax)
    ax.set_title("GDP Per Unit Of Energy")
    ax.set_ylabel("Real GDP per quadrillion Btu")
    add_note(fig, "Formula: GDP_per_energy = real GDP / quarterly total primary energy consumption. Source: EIA MER/FRED GDPC1.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_energy_gdp_lead_lag_heatmap(energy_rows: list[Row], path: Path) -> None:
    selected = [
        r for r in energy_rows
        if r.get("section") == "lead_lag"
        and r.get("predictor") in {"Energy_consumption_growth", "Oil_consumption_growth", "WTI_YoY", "GM2_YoY"}
        and r.get("target") in {"Real_GDP_growth", "Industrial_production_YoY"}
        and is_num(r.get("correlation"))
    ]
    labels = []
    for row in selected:
        label = f"{row.get('predictor')} -> {row.get('target')}"
        if label not in labels:
            labels.append(label)
    lags = sorted({int(r["lag_periods"]) for r in selected})
    matrix = []
    for label in labels:
        vals = []
        for lag in lags:
            match = next((r for r in selected if f"{r.get('predictor')} -> {r.get('target')}" == label and int(r["lag_periods"]) == lag), None)
            vals.append(float(match["correlation"]) if match else 0.0)
        matrix.append(vals)
    fig, ax = plt.subplots(figsize=(13, max(5, 0.45 * len(labels))))
    image = ax.imshow(matrix, aspect="auto", cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(lags)))
    ax.set_xticklabels(lags, rotation=90)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title("Energy-GDP Lead-Lag Correlation Heatmap")
    ax.set_xlabel("Lag periods: positive = predictor leads target")
    fig.colorbar(image, ax=ax, label="Correlation")
    add_note(fig, "Formula: corr(predictor[t-L], target[t]) across monthly and quarterly tests. Source: EIA MER/FRED processed data.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_oil_price_burden_vs_real_activity(energy_rows: list[Row], path: Path) -> None:
    q_rows = [r for r in energy_rows if r.get("section") == "time_series" and r.get("frequency") == "quarterly"]
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {
        "financial_crisis_2008_2009": "#c05621",
        "shale_regime_2014_2017": "#2b6cb0",
        "covid_2020_2021": "#805ad5",
        "war_spr_2022_2023": "#d69e2e",
        "normal_period": "#555555",
    }
    for row in q_rows:
        if is_num(row.get("Oil_price_burden")) and is_num(row.get("Real_GDP_growth")):
            regime = str(row.get("regime") or "normal_period")
            ax.scatter(float(row["Oil_price_burden"]), float(row["Real_GDP_growth"]), color=colors.get(regime, "#555555"), alpha=0.7, s=28, label=regime)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize=7)
    ax.axhline(0, color="#777", linewidth=0.8)
    ax.set_title("Oil Price Burden vs Real Activity")
    ax.set_xlabel("Oil price burden = WTI / GDP per energy")
    ax.set_ylabel("Real GDP YoY growth")
    ax.grid(True, alpha=0.25)
    add_note(fig, "Formula: Oil_price_burden = WTI / (real GDP / energy consumption); y = Real_GDP_growth. Source: EIA MER/FRED.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_final_lead_lag_network(system_rows: list[Row], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_axis_off()
    nodes = {
        "GM2": (0.08, 0.70, "G4 GM2\nliquidity impulse", "#e6f0fa"),
        "Oil": (0.38, 0.70, "Oil YoY\nmomentum", "#f7eee7"),
        "CI": (0.38, 0.38, "Comparative\ninventory", "#f7eee7"),
        "SP500": (0.68, 0.70, "SP500\nrisk/growth proxy", "#eeeeee"),
        "Energy": (0.08, 0.20, "Energy + petroleum\nconsumption", "#e8f4ea"),
        "Industry": (0.38, 0.20, "Industrial\nproduction", "#e8f4ea"),
        "GDP": (0.68, 0.20, "Real GDP\nmeasured outcome", "#e8f4ea"),
        "Efficiency": (0.82, 0.42, "GDP per energy\nefficiency trend", "#eef2f7"),
    }
    for x, y, text, color in nodes.values():
        ax.add_patch(FancyBboxPatch((x, y), 0.18, 0.13, boxstyle="round,pad=0.025,rounding_size=0.02", linewidth=1.2, edgecolor="#444", facecolor=color))
        ax.text(x + 0.09, y + 0.065, text, ha="center", va="center", fontsize=10)
    arrows = [
        ("GM2", "Oil", "leads: locked lag 5"),
        ("CI", "Oil", "residual/state diagnostic"),
        ("Oil", "SP500", "shock/risk context"),
        ("SP500", "Oil", "coincident risk appetite"),
        ("Energy", "Industry", "physical throughput"),
        ("Industry", "GDP", "real activity"),
        ("Energy", "GDP", "anchors output"),
        ("GDP", "Efficiency", "GDP per energy rises"),
    ]
    for src, dst, label in arrows:
        x1, y1 = nodes[src][0] + 0.18, nodes[src][1] + 0.065
        x2, y2 = nodes[dst][0], nodes[dst][1] + 0.065
        if src == "CI":
            x1, y1 = nodes[src][0] + 0.09, nodes[src][1] + 0.13
            x2, y2 = nodes[dst][0] + 0.09, nodes[dst][1]
        if src == "SP500":
            x1, y1 = nodes[src][0], nodes[src][1] + 0.04
            x2, y2 = nodes[dst][0] + 0.18, nodes[dst][1] + 0.04
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=15, linewidth=1.25, color="#333"))
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.025, label, ha="center", va="center", fontsize=8, color="#555")
    ax.text(0.5, 0.94, "Integrated Lead-Lag Network", ha="center", fontsize=16, weight="bold")
    add_note(fig, "Framework: GM2 leads oil momentum; CI diagnoses residuals; SP500 reflects risk appetite; energy anchors real activity; GDP records outcome.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_final_signal_timeline_framework(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_axis_off()
    y = 0.55
    points = [
        (0.12, "Financial lead\nGM2 YoY\n~5 months before oil"),
        (0.36, "Market pricing\nOil + stocks\nrisk/growth repricing"),
        (0.60, "Physical state\nInventory residual\nregime diagnostics"),
        (0.82, "Measured outcome\nEnergy, industry,\nGDP"),
    ]
    ax.plot([0.08, 0.88], [y, y], color="#333", linewidth=1.5)
    for x, text in points:
        ax.scatter([x], [y], s=160, color="#2b6cb0")
        ax.text(x, y + 0.13, text, ha="center", va="bottom", fontsize=10)
    for (x1, _), (x2, _) in zip(points, points[1:]):
        ax.add_patch(FancyArrowPatch((x1 + 0.035, y), (x2 - 0.035, y), arrowstyle="-|>", mutation_scale=16, linewidth=1.4, color="#333"))
    ax.text(0.5, 0.90, "Final Signal Timeline Framework", ha="center", fontsize=16, weight="bold")
    ax.text(0.5, 0.20, "Positive lead means predictor information arrives before the target; diagnostics explain deviations rather than replacing the locked forecast.", ha="center", fontsize=10, color="#555")
    add_note(fig, "Timeline uses project interpretation: GM2 -> oil momentum; stocks/oil price risk layer; CI residual state; energy/GDP real economy outcome.")
    fig.subplots_adjust(left=0.03, right=0.97, top=0.95, bottom=0.08)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_final_energy_finance_oil_gdp_map(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_axis_off()
    bands = [
        (0.08, 0.68, 0.84, 0.18, "Financial Liquidity Layer", "G4 GM2 leads oil-price momentum", "#e6f0fa"),
        (0.08, 0.44, 0.84, 0.18, "Market Pricing Layer", "Oil and stocks reflect growth, risk appetite, and shock repricing", "#f7eee7"),
        (0.08, 0.20, 0.84, 0.18, "Physical Economy Layer", "Energy use anchors industrial activity; GDP records measured output", "#e8f4ea"),
    ]
    for x, y, w, h, title, body, color in bands:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.02", facecolor=color, edgecolor="#444", linewidth=1.1))
        ax.text(x + 0.03, y + h - 0.05, title, ha="left", va="center", fontsize=12, weight="bold")
        ax.text(x + 0.03, y + 0.055, body, ha="left", va="center", fontsize=11)
    ax.add_patch(FancyArrowPatch((0.50, 0.68), (0.50, 0.62), arrowstyle="-|>", mutation_scale=18, linewidth=1.4, color="#333"))
    ax.add_patch(FancyArrowPatch((0.50, 0.44), (0.50, 0.38), arrowstyle="-|>", mutation_scale=18, linewidth=1.4, color="#333"))
    ax.text(0.78, 0.53, "Comparative inventory\nexplains oil residual/state", ha="center", va="center", fontsize=10, color="#555")
    ax.text(0.78, 0.29, "GDP per energy rises:\nefficiency + structural change", ha="center", va="center", fontsize=10, color="#555")
    ax.text(0.5, 0.93, "Energy-Finance-Oil-GDP Map", ha="center", fontsize=16, weight="bold")
    add_note(fig, "Map: liquidity impulse -> market pricing -> physical economy, with inventory and efficiency as diagnostic layers.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def scatter_by_regime(rows: list[Row], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, target in zip(axes, ["WTI_YoY", "Brent_YoY"]):
        for label, predicate, color in [
            ("tight inventories", lambda z: z is not None and z < -0.5, "#2b6cb0"),
            ("normal", lambda z: z is not None and -0.5 <= z <= 0.5, "#555555"),
            ("loose inventories", lambda z: z is not None and z > 0.5, "#c05621"),
        ]:
            xs = [r["GM2_YoY"] for r in rows if predicate(r.get("CI_zscore")) and is_num(r.get("GM2_YoY")) and is_num(r.get(target))]
            ys = [r[target] for r in rows if predicate(r.get("CI_zscore")) and is_num(r.get("GM2_YoY")) and is_num(r.get(target))]
            ax.scatter(xs, ys, s=24, alpha=0.75, label=label, color=color)
        ax.axhline(0, color="#777", linewidth=0.7)
        ax.axvline(0, color="#777", linewidth=0.7)
        ax.set_title(target)
        ax.set_xlabel("GM2 YoY")
    axes[0].set_ylabel("Oil YoY")
    axes[1].legend(fontsize=8)
    add_note(fig, "Formula: Oil_YoY[t] vs same-month GM2_YoY[t], colored by CI_zscore inventory state. Source: processed monthly dataset.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def style_time_axis(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator(base=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, alpha=0.25)


def to_date(month: object):
    return mdates.datestr2num(f"{month}-01")


def scale_trillion(value: object) -> float | None:
    return float(value) / 1_000_000_000_000 if is_num(value) else None


def is_num(value: object) -> bool:
    return isinstance(value, (int, float))


def add_note(fig: plt.Figure, text: str) -> None:
    fig.text(0.01, 0.01, text, ha="left", va="bottom", fontsize=7, color="#555555")


def shade_regimes(ax: plt.Axes) -> None:
    for start, end, label, color in [
        ("2008-01", "2009-12", "2008-09", "#c05621"),
        ("2014-01", "2017-12", "2015-07", "#2b6cb0"),
        ("2020-01", "2021-12", "2020-09", "#805ad5"),
        ("2022-01", "2023-12", "2022-09", "#d69e2e"),
    ]:
        ax.axvspan(to_date(start), to_date(end), color=color, alpha=0.12)
        ax.text(to_date(label), 0.95, start[:4], transform=ax.get_xaxis_transform(), fontsize=7, ha="center", va="top", color="#555555")


def regime_for_chart(month: str) -> str:
    if "2008-01" <= month <= "2009-12":
        return "financial_crisis_2008_2009"
    if "2014-01" <= month <= "2017-12":
        return "shale_regime_2014_2017"
    if "2020-01" <= month <= "2021-12":
        return "covid_2020_2021"
    if "2022-01" <= month <= "2023-12":
        return "war_spr_2022_2023"
    return "normal_period"
