from __future__ import annotations

from pathlib import Path


REQUIRED_ANALYSIS = [
    "analysis/executive_summary.md",
    "analysis/model_card.md",
    "analysis/final_findings_table.csv",
    "analysis/current_signal_snapshot.md",
    "analysis/final_model_interpretation.md",
    "analysis/target_comparison_summary.csv",
    "analysis/residual_diagnostic_summary.csv",
    "analysis/rolling_validation_extended.csv",
    "analysis/oil_equity_lead_lag_summary.csv",
    "analysis/oil_equity_findings.md",
    "analysis/oil_equity_robustness.md",
    "analysis/oil_equity_return_lag_summary.csv",
    "analysis/uso_findings.md",
    "analysis/uso_lead_lag_summary.csv",
    "analysis/uso_tracking_residual_summary.csv",
    "analysis/uso_model_summary.csv",
    "analysis/energy_gdp_findings.md",
    "analysis/energy_gdp_lead_lag.csv",
    "analysis/energy_gdp_model_summary.csv",
    "analysis/integrated_lead_lag_atlas.md",
    "analysis/system_signal_hierarchy.csv",
    "analysis/final_system_interpretation.md",
]

REQUIRED_CHARTS = [
    "charts/final_gm2_oil_lead_chart.png",
    "charts/final_actual_vs_predicted_wti.png",
    "charts/final_residual_ci_diagnostic.png",
    "charts/final_model_framework.png",
    "charts/residual_vs_ci_zscore.png",
    "charts/actual_vs_predicted_best_gm2.png",
    "charts/ci_vs_real_oil_price_level.png",
    "charts/target_comparison_rmse.png",
    "charts/oil_equity_rolling_correlation.png",
    "charts/oil_equity_lag_correlation.png",
    "charts/oil_equity_return_lag_correlation.png",
    "charts/sp500_vs_wti_yoy.png",
    "charts/oil_equity_regime_scatter.png",
    "charts/uso_vs_wti_yoy.png",
    "charts/uso_wti_return_spread.png",
    "charts/uso_tracking_residual_by_regime.png",
    "charts/uso_gm2_model_comparison.png",
    "charts/energy_vs_gdp_growth.png",
    "charts/energy_intensity_trend.png",
    "charts/gdp_per_energy_trend.png",
    "charts/energy_gdp_lead_lag_heatmap.png",
    "charts/oil_price_burden_vs_real_activity.png",
    "charts/final_lead_lag_network.png",
    "charts/final_signal_timeline_framework.png",
    "charts/final_energy_finance_oil_gdp_map.png",
]

REQUIRED_DATA = [
    "data/processed/monthly_dataset.csv",
    "data/oil_model.sqlite",
]


def main() -> None:
    missing: list[str] = []
    empty: list[str] = []
    for filename in REQUIRED_ANALYSIS + REQUIRED_CHARTS + REQUIRED_DATA:
        path = Path(filename)
        if not path.exists():
            missing.append(filename)
        elif path.stat().st_size == 0:
            empty.append(filename)
    if missing or empty:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if empty:
            details.append("empty: " + ", ".join(empty))
        raise SystemExit("Release verification failed: " + "; ".join(details))
    print(f"Release verification passed for {len(REQUIRED_ANALYSIS)} analysis files, {len(REQUIRED_CHARTS)} charts, and {len(REQUIRED_DATA)} data artifacts.")


if __name__ == "__main__":
    main()
