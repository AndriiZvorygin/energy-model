from __future__ import annotations

import argparse
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
    "analysis/physical_realised_price_findings.md",
    "analysis/physical_realised_price_summary.csv",
    "analysis/energy_gdp_findings.md",
    "analysis/energy_gdp_lead_lag.csv",
    "analysis/energy_gdp_model_summary.csv",
    "analysis/integrated_lead_lag_atlas.md",
    "analysis/system_signal_hierarchy.csv",
    "analysis/final_system_interpretation.md",
    "analysis/final_time_series_chart_notes.md",
    "analysis/system_response_framework.md",
    "analysis/system_response_indicator_catalogue.csv",
    "analysis/system_response_current_state.csv",
    "analysis/energy_burden_findings.md",
    "analysis/energy_burden_validation.csv",
    "analysis/physical_tightness_findings.md",
    "analysis/physical_tightness_summary.csv",
    "analysis/labour_early_warning_findings.md",
    "analysis/labour_early_warning_summary.csv",
    "analysis/historical_episode_library.md",
    "analysis/historical_episode_library.csv",
    "analysis/economic_output_quality.md",
    "analysis/economic_output_quality.csv",
    "analysis/energy_output_quality_correlations.csv",
    "analysis/website_visual_audit.md",
    "analysis/canadian_data_audit.md",
    "analysis/canadian_indicator_catalogue.csv",
    "analysis/canadian_historical_episodes.csv",
    "analysis/canadian_historical_episodes.md",
    "analysis/food_housing_affordability_findings.md",
    "analysis/food_housing_indicator_catalogue.csv",
    "analysis/food_price_transmission_summary.csv",
    "analysis/canadian_income_data_audit.md",
    "analysis/canadian_income_indicator_catalogue.csv",
    "analysis/refinery_presentation_audit.md",
    "analysis/evidence_topic_audit.md",
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
    "charts/physical_realised_prices_vs_benchmarks.png",
    "charts/rac_vs_wti_spread.png",
    "charts/physical_price_ci_relationship.png",
    "charts/energy_vs_gdp_growth.png",
    "charts/energy_intensity_trend.png",
    "charts/gdp_per_energy_trend.png",
    "charts/energy_gdp_lead_lag_heatmap.png",
    "charts/oil_price_burden_vs_real_activity.png",
    "charts/final_lead_lag_network.png",
    "charts/final_signal_timeline_framework.png",
    "charts/final_energy_finance_oil_gdp_map.png",
    "charts/final_oil_price_layers_time_series.png",
    "charts/final_gm2_leads_oil_time_series.png",
    "charts/final_oil_residual_ci_time_series.png",
    "charts/final_energy_gdp_time_series.png",
    "charts/system_response_chain.png",
    "charts/current_state_layers.png",
    "charts/physical_tightness_dashboard.png",
    "charts/energy_burden_dashboard.png",
    "charts/demand_destruction_cycle.png",
    "charts/industrial_transmission.png",
    "charts/labour_early_warning_indicators.png",
    "charts/household_stress_indicators.png",
    "charts/historical_episode_comparison.png",
    "charts/regime_timeline.png",
    "charts/indicator_lag_map.png",
]

REQUIRED_DATA = [
    "data/processed/monthly_dataset.csv",
    "data/processed/system_response_core.csv",
    "data/oil_model.sqlite",
    "website/public/generated/manifest.json",
    "website/public/generated/oil-price-layers.json",
    "website/public/generated/gm2-oil-lead.json",
    "website/public/generated/oil-residual-ci.json",
    "website/public/generated/energy-gdp.json",
    "website/public/generated/oil-equities.json",
    "website/public/generated/uso-tracking.json",
    "website/public/generated/lag-results.json",
    "website/public/generated/regimes.json",
    "website/public/generated/events.json",
    "website/public/generated/cross-layer.json",
    "website/public/generated/output-quality-headline.json",
    "website/public/generated/output-quality-net-output.json",
    "website/public/generated/output-quality-capacity.json",
    "website/public/generated/output-quality-household.json",
    "website/public/generated/output-quality-financial.json",
    "website/public/generated/output-quality-correlations.json",
    "website/public/generated/rolling-performance.json",
    "website/public/generated/recessions.json",
    "website/public/generated/current-classification.json",
    "website/public/generated/symptom-evaluations.json",
    "website/public/generated/regime-scores.json",
    "website/public/generated/regime-history.json",
    "website/public/generated/evidence-summary.json",
    "website/public/generated/presentation-manifest.json",
    "website/public/generated/charts/physical-tightness.json",
    "website/public/generated/charts/energy-burden.json",
    "website/public/generated/charts/industrial-transmission.json",
    "website/public/generated/charts/labour-warning.json",
    "website/public/generated/charts/demand-destruction.json",
    "website/public/generated/charts/output-quality-comparison.json",
    "website/public/generated/indicators/ci-zscore.json",
    "website/public/generated/indicators/gm2-yoy.json",
    "website/public/generated/indicators/unemployment-rate.json",
    "data/processed/canadian_core.csv",
    "website/public/generated/canada/manifest.json",
    "website/public/generated/canada/current-state.json",
    "website/public/generated/canada/canada-us-comparison.json",
    "website/public/generated/canada/current-classification.json",
    "website/public/generated/canada/symptom-evaluations.json",
    "website/public/generated/canada/regime-scores.json",
    "website/public/generated/global/manifest.json",
    "website/public/generated/global/indicators/fao-food-price-index.json",
    "website/public/generated/global/indicators/fao-food-price-index-real.json",
    "website/public/generated/global/indicators/bis-real-house-prices.json",
    "website/public/generated/canada/indicators/food-cpi.json",
    "website/public/generated/canada/indicators/grocery-cpi.json",
    "website/public/generated/canada/indicators/new-housing-price-index.json",
    "website/public/generated/canada/indicators/shelter-cpi.json",
    "website/public/generated/canada/indicators/rent-cpi.json",
    "website/public/generated/canada/indicators/mortgage-interest-cost.json",
    "website/public/generated/us/manifest.json",
    "website/public/generated/us/indicators/us-food-at-home-cpi.json",
    "website/public/generated/us/indicators/us-fhfa-house-price-index.json",
    "website/public/generated/us/indicators/us-rent-cpi.json",
    "website/public/generated/us/indicators/us-shelter-cpi.json",
    "website/public/generated/affordability-fao-food.json",
    "website/public/generated/affordability-food-transmission.json",
    "website/public/generated/affordability-canada-housing.json",
    "website/public/generated/affordability-us-housing.json",
    "website/public/generated/affordability-real-house-prices.json",
    "website/public/generated/food-transmission-analysis.json",
    "website/public/generated/canada/indicators/household-disposable-income-per-person.json",
    "website/public/generated/canada/indicators/real-disposable-income-per-person.json",
    "website/public/generated/canada/indicators/average-hourly-wages.json",
    "website/public/generated/canada/indicators/ontario-average-hourly-wages.json",
    "website/public/generated/canada/indicators/food-to-income.json",
    "website/public/generated/canada/indicators/rent-to-income.json",
    "website/public/generated/canada/indicators/mortgage-interest-to-income.json",
    "website/public/generated/canada/indicators/nhpi-to-income.json",
    "website/public/generated/affordability-canada-purchasing-power.json",
    "website/public/generated/affordability-canada-food-income.json",
    "website/public/generated/affordability-canada-housing-ratios.json",
    "website/public/generated/canada/indicators/canada-unemployment-rate.json",
    "website/public/generated/canada/indicators/ontario-unemployment-rate.json",
]


def verify(root: Path) -> str:
    missing: list[str] = []
    empty: list[str] = []
    for filename in REQUIRED_ANALYSIS + REQUIRED_CHARTS + REQUIRED_DATA:
        path = root / filename
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
    return f"Release verification passed for {len(REQUIRED_ANALYSIS)} analysis files, {len(REQUIRED_CHARTS)} charts, and {len(REQUIRED_DATA)} data artifacts."


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify required release outputs exist and are non-empty.")
    parser.add_argument("--root", default=".", help="project root")
    args = parser.parse_args()
    print(verify(Path(args.root).resolve()))


if __name__ == "__main__":
    main()
